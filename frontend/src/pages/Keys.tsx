import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { LoadingBars } from '../components/LoadingBars'

type Consumer = { id: number; name: string; status: string }
type Key = { id: number; key_prefix: string; status: string; expires_at: string | null; created_at: string }
type IssuedKey = Key & { raw_key: string }

export function Keys({ providerId }: { providerId: number }) {
  const { data: consumers } = useApi<Consumer[]>(`/api/providers/${providerId}/consumers/`)
  const [selected, setSelected] = useState<number | null>(null)
  const [keys, setKeys]         = useState<Key[]>([])
  const [loadingKeys, setLoadingKeys] = useState(false)
  const [issuing, setIssuing]   = useState(false)
  const [revealed, setRevealed] = useState<string | null>(null)

  async function pickConsumer(id: number) {
    setSelected(id); setRevealed(null); setLoadingKeys(true)
    const r = await fetch(`/api/providers/${providerId}/consumers/${id}/keys/`)
    setKeys(await r.json()); setLoadingKeys(false)
  }

  async function issueKey() {
    if (!selected) return
    setIssuing(true)
    const r = await fetch(`/api/providers/${providerId}/consumers/${selected}/keys/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
    })
    const k: IssuedKey = await r.json()
    setRevealed(k.raw_key); setKeys(prev => [k, ...prev]); setIssuing(false)
  }

  async function revoke(keyId: number) {
    await fetch(`/api/providers/${providerId}/consumers/${selected}/keys/${keyId}/revoke`, { method: 'POST' })
    setKeys(prev => prev.map(k => k.id === keyId ? { ...k, status: 'revoked' } : k))
  }

  return (
    <div>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 600, color: 'var(--dark)', margin: '0 0 4px' }}>Keys</h1>
      <p style={{ fontSize: 14, color: 'var(--muted)', margin: '0 0 32px' }}>Select a consumer to manage their API keys</p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 32, flexWrap: 'wrap' }}>
        {(consumers ?? []).map(c => (
          <button key={c.id} onClick={() => pickConsumer(c.id)} style={{
            padding: '8px 18px', borderRadius: 8, cursor: 'pointer',
            border: `1px solid ${selected === c.id ? 'var(--sage)' : 'var(--off-white)'}`,
            background: selected === c.id ? 'var(--light)' : '#fff',
            color: selected === c.id ? 'var(--dark)' : 'var(--muted)',
            fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, transition: 'all .15s',
          }}>{c.name}</button>
        ))}
      </div>

      {selected && (
        <>
          {revealed && (
            <div style={{ background: 'var(--light)', border: '1px solid var(--mid)', borderRadius: 10,
              padding: '14px 18px', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontFamily: 'var(--font-heading)', fontSize: 12, fontWeight: 700, color: 'var(--sage)' }}>⚠ Copy now — shown once:</span>
              <code style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--dark)' }}>{revealed}</code>
              <button onClick={() => navigator.clipboard.writeText(revealed)}
                style={{ background: 'var(--sage)', color: '#fff', border: 'none', borderRadius: 6,
                  padding: '5px 12px', cursor: 'pointer', fontFamily: 'var(--font-heading)', fontSize: 12, fontWeight: 600 }}>
                Copy
              </button>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button onClick={issueKey} disabled={issuing} style={{
              background: 'var(--sage)', color: '#fff', border: 'none', borderRadius: 8,
              padding: '9px 20px', cursor: 'pointer', fontFamily: 'var(--font-heading)',
              fontSize: 13, fontWeight: 600, opacity: issuing ? 0.6 : 1,
            }}>{issuing ? 'Issuing…' : '+ Issue New Key'}</button>
          </div>

          {loadingKeys ? <LoadingBars /> : (
            <div style={{ background: '#fff', border: '1px solid var(--off-white)', borderRadius: 12, overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-heading)', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--off-white)' }}>
                    {['Prefix','Status','Created','Expires',''].map(h => (
                      <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 11,
                        fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {keys.length === 0
                    ? <tr><td colSpan={5} style={{ padding: 32, textAlign: 'center', color: 'var(--muted)' }}>No keys yet</td></tr>
                    : keys.map((k, i) => (
                      <tr key={k.id} style={{ borderBottom: i < keys.length - 1 ? '1px solid var(--off-white)' : 'none' }}>
                        <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--dark)' }}>{k.key_prefix}…</td>
                        <td style={{ padding: '14px 16px' }}>
                          <span style={{ padding: '3px 10px', borderRadius: 99, fontSize: 11, fontWeight: 600,
                            background: k.status === 'active' ? 'var(--light)' : 'var(--off-white)',
                            color: k.status === 'active' ? 'var(--dark)' : 'var(--muted-2)' }}>{k.status}</span>
                        </td>
                        <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>
                          {new Date(k.created_at).toLocaleDateString()}
                        </td>
                        <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>
                          {k.expires_at ? new Date(k.expires_at).toLocaleDateString() : '—'}
                        </td>
                        <td style={{ padding: '14px 16px' }}>
                          {k.status === 'active' && (
                            <button onClick={() => revoke(k.id)} style={{
                              background: 'none', border: '1px solid var(--off-white)', borderRadius: 6,
                              padding: '4px 10px', cursor: 'pointer', fontSize: 12,
                              fontFamily: 'var(--font-heading)', color: 'var(--muted)', fontWeight: 600,
                            }}>Revoke</button>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
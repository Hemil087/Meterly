import { useApi } from '../hooks/useApi'
import { LoadingBars } from '../components/LoadingBars'
import { EmptyState } from '../components/EmptyState'

type Event = {
  occurred_at: string; consumer_id: number; method: string
  path: string; status_code: number; outcome: string; latency_ms: number
}

const BADGE: Record<string, { bg: string; color: string }> = {
  forwarded:      { bg: 'var(--light)',    color: 'var(--dark)'       },
  rate_limited:   { bg: 'var(--amber-bg)', color: 'var(--amber-text)' },
  quota_blocked:  { bg: 'var(--amber-bg)', color: 'var(--amber-text)' },
  auth_failed:    { bg: '#fee2e2',         color: '#b91c1c'           },
  upstream_error: { bg: '#fee2e2',         color: '#b91c1c'           },
}

function Badge({ outcome }: { outcome: string }) {
  const c = BADGE[outcome] ?? { bg: 'var(--off-white)', color: 'var(--muted)' }
  return (
    <span style={{ padding: '3px 10px', borderRadius: 99, fontSize: 11, fontWeight: 600,
      fontFamily: 'var(--font-heading)', background: c.bg, color: c.color }}>
      {outcome.replace(/_/g, ' ')}
    </span>
  )
}

export function Events({ providerId }: { providerId: number }) {
  const { data, loading } = useApi<Event[]>(`/api/providers/${providerId}/analytics/events?limit=50`)

  if (loading) return <LoadingBars />
  if (!data)   return <EmptyState />

  return (
    <div>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 600, color: 'var(--dark)', margin: '0 0 4px' }}>Events</h1>
      <p style={{ fontSize: 14, color: 'var(--muted)', margin: '0 0 32px' }}>Last 50 requests</p>

      <div style={{ background: '#fff', border: '1px solid var(--off-white)', borderRadius: 12, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-heading)', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--off-white)' }}>
              {['Time','Method','Path','Status','Outcome','Latency'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 11,
                  fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0
              ? <tr><td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--muted)' }}>No events yet</td></tr>
              : data.map((e, i) => (
                <tr key={i} style={{ borderBottom: i < data.length - 1 ? '1px solid var(--off-white)' : 'none' }}>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>
                    {new Date(e.occurred_at).toLocaleTimeString()}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: 'var(--sage)' }}>{e.method}</span>
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--dark)' }}>{e.path}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 12,
                    color: e.status_code >= 400 ? '#b91c1c' : 'var(--sage)' }}>{e.status_code}</td>
                  <td style={{ padding: '12px 16px' }}><Badge outcome={e.outcome} /></td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{e.latency_ms}ms</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { LoadingBars } from '../components/LoadingBars'
import { EmptyState } from '../components/EmptyState'

type Api      = { id: number; name: string; slug: string; upstream_url: string; status: string }
type Plan     = { id: number; name: string; monthly_quota: number; price_monthly: number; status: string }
type RLP      = { id: number; requests: number; window_seconds: number; algorithm: string }
type Provider = { id: number; name: string; slug: string; status: string }

const INPUT: React.CSSProperties = {
  width: '100%', padding: '9px 12px', borderRadius: 8, fontSize: 13,
  border: '1px solid var(--off-white)', fontFamily: 'var(--font-heading)',
  outline: 'none', color: 'var(--dark)', background: '#fff', boxSizing: 'border-box',
}
const LABEL: React.CSSProperties = {
  fontSize: 11, fontWeight: 600, color: 'var(--muted)',
  textTransform: 'uppercase', letterSpacing: '0.04em',
  display: 'block', marginBottom: 6,
}
const BTN: React.CSSProperties = {
  background: 'var(--sage)', color: '#fff', border: 'none', borderRadius: 8,
  padding: '9px 20px', cursor: 'pointer', fontFamily: 'var(--font-heading)',
  fontSize: 13, fontWeight: 600,
}

function Field({ label, ...props }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <label style={LABEL}>{label}</label>
      <input style={INPUT} {...props} />
    </div>
  )
}

function ProviderSettings({ providerId }: { providerId: number }) {
  const { data: provider } = useApi<Provider>(`/api/providers/${providerId}`)
  const [secret, setSecret] = useState('')
  const [show, setShow]     = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved]   = useState(false)

  async function save() {
    if (!secret.trim()) return
    setSaving(true)
    await fetch(`/api/providers/${providerId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shared_secret: secret }),
    })
    setSaving(false); setSaved(true); setSecret('')
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div style={{ background: '#fff', border: '1px solid var(--off-white)',
      borderRadius: 12, padding: 24, marginBottom: 32 }}>
      <div style={{ ...LABEL, marginBottom: 4 }}>Provider Settings</div>
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
        The upstream API key is injected as{' '}
        <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--off-white)',
          padding: '1px 6px', borderRadius: 4 }}>Authorization: Bearer …</code>{' '}
        on every forwarded request. Consumers never see it.
      </div>
      {provider && (
        <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
          Provider: <strong style={{ color: 'var(--dark)' }}>{provider.name}</strong>
          {' · '}slug:{' '}
          <code style={{ fontFamily: 'var(--font-mono)' }}>{provider.slug}</code>
        </div>
      )}
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
        <div style={{ flex: 1 }}>
          <label style={LABEL}>Upstream API Key</label>
          <div style={{ position: 'relative' }}>
            <input
              type={show ? 'text' : 'password'}
              placeholder="gsk_… or sk-… or any Bearer token"
              value={secret}
              onChange={e => setSecret(e.target.value)}
              style={{ ...INPUT, paddingRight: 80 }}
            />
            <button onClick={() => setShow(s => !s)} style={{
              position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 11, fontWeight: 600, color: 'var(--muted)',
              fontFamily: 'var(--font-heading)',
            }}>{show ? 'Hide' : 'Show'}</button>
          </div>
        </div>
        <button onClick={save} disabled={saving || !secret.trim()} style={{
          ...BTN, opacity: saving || !secret.trim() ? 0.5 : 1,
          background: saved ? 'var(--sage)' : 'var(--dark)',
          minWidth: 100, transition: 'background .3s',
        }}>
          {saved ? '✓ Saved' : saving ? 'Saving…' : 'Save Key'}
        </button>
      </div>
      <div style={{ marginTop: 12, fontSize: 12, color: 'var(--muted)' }}>
        ⚠ The current key is never displayed after saving — paste a new one to rotate it.
      </div>
    </div>
  )
}

function PlanManager({ providerId, api }: { providerId: number; api: Api }) {
  const { data: plans, loading } = useApi<Plan[]>(
    `/api/providers/${providerId}/apis/${api.id}/plans/`
  )
  const { data: _rlps } = useApi<RLP[]>(`/api/rate_limit_policies/`)
  const [form, setForm] = useState({
    name: '', monthly_quota: '10000', price_monthly: '0', rate_limit_policy_id: '1',
  })
  const [saving, setSaving]         = useState(false)
  const [localPlans, setLocalPlans] = useState<Plan[] | null>(null)

  const allPlans = localPlans ?? plans ?? []

  async function createPlan() {
    setSaving(true)
    const r = await fetch(`/api/providers/${providerId}/apis/${api.id}/plans/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: form.name,
        monthly_quota: parseInt(form.monthly_quota),
        price_monthly: parseFloat(form.price_monthly),
        rate_limit_policy_id: parseInt(form.rate_limit_policy_id),
        overage_allowed: false,
        overage_price: 0,
      }),
    })
    const p = await r.json()
    setLocalPlans([...allPlans, p])
    setForm({ name: '', monthly_quota: '10000', price_monthly: '0', rate_limit_policy_id: '1' })
    setSaving(false)
  }

  return (
    <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--off-white)' }}>
      <div style={{ ...LABEL, marginBottom: 12 }}>Plans for {api.name}</div>
      {loading ? <LoadingBars /> : (
        <div style={{ marginBottom: 16 }}>
          {allPlans.length === 0
            ? <p style={{ fontSize: 13, color: 'var(--muted)', margin: 0 }}>No plans yet.</p>
            : allPlans.map(p => (
              <div key={p.id} style={{ display: 'flex', gap: 16, alignItems: 'center',
                padding: '10px 0', borderBottom: '1px solid var(--off-white)', fontSize: 13 }}>
                <span style={{ fontWeight: 600, color: 'var(--dark)', width: 120 }}>{p.name}</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--muted)' }}>
                  {p.monthly_quota.toLocaleString()} calls/mo
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--sage)' }}>
                  ${p.price_monthly}/mo
                </span>
                <span style={{ padding: '2px 8px', borderRadius: 99, fontSize: 11, fontWeight: 600,
                  background: p.status === 'active' ? 'var(--light)' : 'var(--off-white)',
                  color: p.status === 'active' ? 'var(--dark)' : 'var(--muted-2)' }}>
                  {p.status}
                </span>
              </div>
            ))}
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
        <Field label="Plan name" placeholder="Free" value={form.name}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
        <Field label="Monthly quota" type="number" value={form.monthly_quota}
          onChange={e => setForm(f => ({ ...f, monthly_quota: e.target.value }))} />
        <Field label="Price / month ($)" type="number" value={form.price_monthly}
          onChange={e => setForm(f => ({ ...f, price_monthly: e.target.value }))} />
        <div>
            <label style={LABEL}>Rate Limit Policy</label>
            <select
                value={form.rate_limit_policy_id}
                onChange={e => setForm(f => ({ ...f, rate_limit_policy_id: e.target.value }))}
                style={{
                width: '100%', padding: '9px 12px', borderRadius: 8, fontSize: 13,
                border: '1px solid var(--off-white)', fontFamily: 'var(--font-heading)',
                color: 'var(--dark)', background: '#fff', outline: 'none',
                }}
            >
                {(_rlps ?? []).length === 0
                ? <option value="">No policies found</option>
                : (_rlps ?? []).map(r => (
                    <option key={r.id} value={r.id}>
                        #{r.id} — {r.requests} req/{r.window_seconds}s ({r.algorithm})
                    </option>
                    ))
                }
            </select>
        </div>
      </div>
      <button style={BTN} onClick={createPlan} disabled={saving || !form.name}>
        {saving ? 'Creating…' : '+ Add Plan'}
      </button>
    </div>
  )
}

export function Apis({ providerId }: { providerId: number }) {
  // ALL hooks declared before any early return — Rules of Hooks
  const { data, loading }       = useApi<Api[]>(`/api/providers/${providerId}/apis/`)
  const [apis, setApis]         = useState<Api[] | null>(null)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [form, setForm]         = useState({ name: '', slug: '', upstream_url: '' })
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState<string | null>(null)

  // early return AFTER all hooks
  if (loading && !apis) return <LoadingBars />

  const allApis = apis ?? data ?? []

  async function registerApi() {
    setSaving(true)
    setError(null)
    const r = await fetch(`/api/providers/${providerId}/apis/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    if (!r.ok) {
      const err = await r.json()
      setError(err.detail ?? 'Registration failed')
      setSaving(false)
      return
    }
    const a = await r.json()
    setApis([...allApis, a])
    setForm({ name: '', slug: '', upstream_url: '' })
    setSaving(false)
  }

  return (
    <div>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 600,
        color: 'var(--dark)', margin: '0 0 4px' }}>APIs</h1>
      <p style={{ fontSize: 14, color: 'var(--muted)', margin: '0 0 32px' }}>
        Register APIs and manage their plans
      </p>

      {/* Provider Settings */}
      <ProviderSettings providerId={providerId} />

      {/* Register new API */}
      <div style={{ background: '#fff', border: '1px solid var(--off-white)',
        borderRadius: 12, padding: 24, marginBottom: 32 }}>
        <div style={{ ...LABEL, marginBottom: 16 }}>Register new API</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: 12, marginBottom: 12 }}>
          <Field label="Name" placeholder="Groq Chat" value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          <Field label="Slug" placeholder="groq" value={form.slug}
            onChange={e => setForm(f => ({ ...f, slug: e.target.value }))} />
          <Field label="Upstream URL" placeholder="https://api.groq.com" value={form.upstream_url}
            onChange={e => setForm(f => ({ ...f, upstream_url: e.target.value }))} />
        </div>
        <button
          style={{ ...BTN, opacity: saving || !form.name || !form.slug || !form.upstream_url ? 0.5 : 1 }}
          onClick={registerApi}
          disabled={saving || !form.name || !form.slug || !form.upstream_url}
        >
          {saving ? 'Registering…' : '+ Register API'}
        </button>
        {error && (
          <div style={{ marginTop: 10, fontSize: 13, color: '#b91c1c' }}>⚠ {error}</div>
        )}
      </div>

      {/* Existing APIs */}
      {allApis.length === 0
        ? <EmptyState />
        : allApis.map(api => (
          <div key={api.id} style={{ background: '#fff', border: '1px solid var(--off-white)',
            borderRadius: 12, padding: 24, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 600,
                  color: 'var(--dark)', fontSize: 15 }}>{api.name}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12,
                  color: 'var(--muted)', marginTop: 4 }}>
                  /{api.slug} → {api.upstream_url}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ padding: '3px 10px', borderRadius: 99, fontSize: 11, fontWeight: 600,
                  background: 'var(--light)', color: 'var(--dark)' }}>{api.status}</span>
                <button onClick={() => setExpanded(expanded === api.id ? null : api.id)}
                  style={{ background: 'none', border: '1px solid var(--off-white)', borderRadius: 8,
                    padding: '6px 14px', cursor: 'pointer', fontSize: 12,
                    fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--muted)' }}>
                  {expanded === api.id ? 'Hide Plans' : 'Manage Plans'}
                </button>
              </div>
            </div>
            {expanded === api.id && <PlanManager providerId={providerId} api={api} />}
          </div>
        ))}
    </div>
  )
}
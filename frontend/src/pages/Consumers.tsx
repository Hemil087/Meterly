import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { LoadingBars } from '../components/LoadingBars'
import { EmptyState } from '../components/EmptyState'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

type ConsumerRow = {
  consumer_id: number; consumer_name: string; total_calls: number
  calls_forwarded: number; rate_limited: number; avg_latency_ms: string | null
}
type Hourly = { hour: string; total_calls: number; forwarded: number; blocked: number }
type Sub = { id: number; api_id: number; plan_id: number; status: string; cycle_anchor: string }
type Plan = { id: number; name: string; monthly_quota: number; price_monthly: number; status: string }

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

const SECTION_LABEL: React.CSSProperties = {
  fontFamily: 'var(--font-heading)', fontSize: 12, fontWeight: 600,
  color: 'var(--sage)', letterSpacing: '0.04em', textTransform: 'uppercase',
}

function Sparkline({ providerId, consumerId }: { providerId: number; consumerId: number }) {
  const { data, loading } = useApi<Hourly[]>(
    `/api/providers/${providerId}/analytics/consumers/${consumerId}/hourly?days=7`
  )
  if (loading) return <LoadingBars />
  if (!data || data.length === 0)
    return <p style={{ color: 'var(--muted)', fontSize: 13 }}>No hourly data yet — fire some requests first.</p>
  return (
    <ResponsiveContainer width="100%" height={130}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#96a78d" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#96a78d" stopOpacity={0}    />
          </linearGradient>
        </defs>
        <XAxis dataKey="hour" hide />
        <YAxis hide />
        <Tooltip
          contentStyle={{ fontFamily: 'var(--font-mono)', fontSize: 12,
            border: '1px solid var(--off-white)', borderRadius: 8 }}
          formatter={(v: number) => [fmt(v), 'calls']}
          labelFormatter={(l) => new Date(l).toLocaleString()}
        />
        <Area type="monotone" dataKey="total_calls" stroke="#96a78d" strokeWidth={2} fill="url(#sg)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function SubscriptionPanel({ providerId, consumerId }: { providerId: number; consumerId: number }) {
  const { data: subs, loading: subsLoading } = useApi<Sub[]>(
    `/api/providers/${providerId}/consumers/${consumerId}/subscriptions/`
  )
  const activeSub = (subs ?? []).find(s => s.status === 'active') ?? null
  const { data: plans } = useApi<Plan[]>(
    activeSub ? `/api/providers/${providerId}/apis/${activeSub.api_id}/plans/` : ''
  )
  const [changing, setChanging]     = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null)
  const [localSub, setLocalSub]     = useState<Sub | null>(null)

  const currentSub = localSub ?? activeSub

  async function changePlan() {
    if (!currentSub || !selectedPlan) return
    setChanging(true)
    const r = await fetch(
      `/api/providers/${providerId}/consumers/${consumerId}/subscriptions/${currentSub.id}/change_plan`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_plan_id: selectedPlan }),
      }
    )
    const updated = await r.json()
    setLocalSub(updated)
    setChanging(false)
    setSelectedPlan(null)
  }

  if (subsLoading) return <LoadingBars />

  return (
    <div style={{ padding: '16px 0' }}>
      {!currentSub
        ? <p style={{ fontSize: 13, color: 'var(--muted)', margin: 0 }}>No active subscription.</p>
        : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* Current plan label */}
            <div>
              <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '0.04em' }}>Current Plan</div>
              <div style={{ fontWeight: 600, color: 'var(--dark)', marginTop: 4 }}>
                {(plans ?? []).find(p => p.id === currentSub.plan_id)?.name ?? `Plan #${currentSub.plan_id}`}
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
                {(plans ?? []).find(p => p.id === currentSub.plan_id)?.monthly_quota.toLocaleString()} calls/mo
              </div>
            </div>

            <div style={{ flex: 1 }} />

            {/* Plan change controls */}
            {(plans ?? []).filter(p => p.status === 'active' && p.id !== currentSub.plan_id).length > 0 ? (
              <>
                <select
                  value={selectedPlan ?? ''}
                  onChange={e => setSelectedPlan(Number(e.target.value))}
                  style={{
                    padding: '8px 12px', borderRadius: 8,
                    border: '1px solid var(--off-white)',
                    fontFamily: 'var(--font-heading)', fontSize: 13,
                    color: 'var(--dark)', background: '#fff',
                  }}
                >
                  <option value="">Change plan…</option>
                  {(plans ?? [])
                    .filter(p => p.status === 'active' && p.id !== currentSub.plan_id)
                    .map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} — {p.monthly_quota.toLocaleString()} calls/mo · ${p.price_monthly}/mo
                      </option>
                    ))}
                </select>
                <button
                  onClick={changePlan}
                  disabled={!selectedPlan || changing}
                  style={{
                    background: 'var(--sage)', color: '#fff', border: 'none',
                    borderRadius: 8, padding: '8px 16px', cursor: 'pointer',
                    fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600,
                    opacity: !selectedPlan || changing ? 0.4 : 1,
                    transition: 'opacity .15s',
                  }}
                >
                  {changing ? 'Saving…' : 'Apply'}
                </button>
              </>
            ) : (
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>No other plans available</span>
            )}
          </div>
        )}
    </div>
  )
}

export function Consumers({ providerId }: { providerId: number }) {
  const { data, loading } = useApi<ConsumerRow[]>(
    `/api/providers/${providerId}/analytics/consumers?days=30`
  )
  const [selected, setSelected] = useState<number | null>(null)

  if (loading) return <LoadingBars />
  if (!data)   return <EmptyState />

  return (
    <div>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 600,
        color: 'var(--dark)', margin: '0 0 4px' }}>Consumers</h1>
      <p style={{ fontSize: 14, color: 'var(--muted)', margin: '0 0 32px' }}>
        Click a row to manage subscription and view traffic
      </p>

      {/* Consumer table */}
      <div style={{ background: '#fff', border: '1px solid var(--off-white)',
        borderRadius: 12, overflow: 'hidden', marginBottom: 24 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse',
          fontFamily: 'var(--font-heading)', fontSize: 14 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--off-white)' }}>
              {['Consumer', 'Total', 'Forwarded', 'Rate Limited', 'Avg Latency'].map(h => (
                <th key={h} style={{
                  padding: '12px 16px', textAlign: 'left', fontSize: 11,
                  fontWeight: 600, color: 'var(--muted)',
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0
              ? (
                <tr>
                  <td colSpan={5} style={{ padding: 32, textAlign: 'center', color: 'var(--muted)' }}>
                    No consumers yet
                  </td>
                </tr>
              )
              : data.map((r, i) => (
                <tr
                  key={r.consumer_id}
                  onClick={() => setSelected(selected === r.consumer_id ? null : r.consumer_id)}
                  style={{
                    borderBottom: i < data.length - 1 ? '1px solid var(--off-white)' : 'none',
                    cursor: 'pointer', transition: 'background .15s',
                    background: selected === r.consumer_id ? '#fafafa' : '#fff',
                  }}
                >
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--dark)' }}>
                    {r.consumer_name}
                    {selected === r.consumer_id && (
                      <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--sage)' }}>▲</span>
                    )}
                  </td>
                  <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)' }}>{fmt(r.total_calls)}</td>
                  <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--sage)' }}>{fmt(r.calls_forwarded)}</td>
                  <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)',
                    color: r.rate_limited > 0 ? 'var(--amber-text)' : 'var(--muted-2)' }}>{fmt(r.rate_limited)}</td>
                  <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--muted)' }}>
                    {r.avg_latency_ms ? `${Math.round(parseFloat(r.avg_latency_ms))}ms` : '—'}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Expanded panel — subscription + sparkline */}
      {selected && (
        <div style={{ background: '#fff', border: '1px solid var(--off-white)',
          borderRadius: 12, padding: 24 }}>

          {/* Subscription section */}
          <div style={{ ...SECTION_LABEL, marginBottom: 0 }}>Subscription</div>
          <SubscriptionPanel providerId={providerId} consumerId={selected} />

          {/* Divider */}
          <div style={{ borderTop: '1px solid var(--off-white)', margin: '8px 0 20px' }} />

          {/* Hourly traffic section */}
          <div style={{ ...SECTION_LABEL, marginBottom: 16 }}>Hourly Traffic — Last 7 Days</div>
          <Sparkline providerId={providerId} consumerId={selected} />
        </div>
      )}
    </div>
  )
}
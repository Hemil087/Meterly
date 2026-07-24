import { useApi } from '../hooks/useApi'
import { MetricCard } from '../components/MetricCard'
import { LoadingBars } from '../components/LoadingBars'
import { EmptyState } from '../components/EmptyState'

type Overview = {
  total_calls: number; forwarded: number; rate_limited: number
  quota_blocked: number; auth_failed: number; upstream_errors: number
  avg_latency_ms: string | null
}
type ConsumerRow = {
  consumer_id: number; consumer_name: string; total_calls: number
  calls_forwarded: number; rate_limited: number; quota_blocked: number
  avg_latency_ms: string | null
}

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

const TH: React.CSSProperties = {
  padding: '12px 16px', textAlign: 'left', fontSize: 11,
  fontWeight: 600, color: 'var(--muted)',
  textTransform: 'uppercase', letterSpacing: '0.04em',
}

export function Overview({ providerId }: { providerId: number }) {
  const ov = useApi<Overview>(`/api/providers/${providerId}/analytics/overview?days=30`)
  const cs = useApi<ConsumerRow[]>(`/api/providers/${providerId}/analytics/consumers?days=30`)

  if (ov.loading) return <LoadingBars />
  if (!ov.data) return <EmptyState />

  const d = ov.data
  const pct = (n: number) => d.total_calls > 0 ? Math.round(n / d.total_calls * 100) : 0
  const lat = d.avg_latency_ms ? Math.round(parseFloat(d.avg_latency_ms)) : 0

  return (
    <div>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 600, color: 'var(--dark)', margin: '0 0 4px' }}>Overview</h1>
      <p style={{ fontSize: 14, color: 'var(--muted)', margin: '0 0 32px' }}>Last 30 days</p>

      <div style={{ display: 'flex', gap: 16, marginBottom: 48 }}>
        <MetricCard label="Total Calls"  value={fmt(d.total_calls)} trend={{ direction: 'up',   value: `${pct(d.forwarded)}%`,    label: 'success rate' }} />
        <MetricCard label="Forwarded"    value={fmt(d.forwarded)}   trend={{ direction: 'up',   value: `${pct(d.forwarded)}%`,    label: 'of total' }} />
        <MetricCard label="Rate Limited" value={fmt(d.rate_limited)} accent={d.rate_limited > 0}
          trend={{ direction: 'up', value: `${pct(d.rate_limited)}%`, label: 'of total', tone: d.rate_limited > 0 ? 'warning' : undefined }} />
        <MetricCard label="Avg Latency"  value={String(lat)} unit="ms" trend={{ direction: 'down', value: '—', label: 'baseline' }} />
      </div>

      <div style={{ fontFamily: 'var(--font-heading)', fontSize: 12, fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--sage)', marginBottom: 14 }}>
        Consumer Breakdown
      </div>
      {cs.loading ? <LoadingBars /> : (
        <div style={{ background: '#fff', border: '1px solid var(--off-white)', borderRadius: 12, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-heading)', fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--off-white)' }}>
                {['Consumer','Total','Forwarded','Rate Limited','Quota Blocked','Avg Latency'].map(h => <th key={h} style={TH}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {(cs.data ?? []).length === 0
                ? <tr><td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--muted)' }}>No activity yet</td></tr>
                : (cs.data ?? []).map((r, i, arr) => (
                  <tr key={r.consumer_id} style={{ borderBottom: i < arr.length - 1 ? '1px solid var(--off-white)' : 'none' }}>
                    <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--dark)' }}>{r.consumer_name}</td>
                    <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)' }}>{fmt(r.total_calls)}</td>
                    <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--sage)' }}>{fmt(r.calls_forwarded)}</td>
                    <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: r.rate_limited > 0 ? 'var(--amber-text)' : 'var(--muted-2)' }}>{fmt(r.rate_limited)}</td>
                    <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: r.quota_blocked > 0 ? 'var(--amber-text)' : 'var(--muted-2)' }}>{fmt(r.quota_blocked)}</td>
                    <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--muted)' }}>{r.avg_latency_ms ? `${Math.round(parseFloat(r.avg_latency_ms))}ms` : '—'}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
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

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
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

export function Consumers({ providerId }: { providerId: number }) {
  const { data, loading } = useApi<ConsumerRow[]>(`/api/providers/${providerId}/analytics/consumers?days=30`)
  const [selected, setSelected] = useState<number | null>(null)

  if (loading) return <LoadingBars />
  if (!data)   return <EmptyState />

  return (
    <div>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 600, color: 'var(--dark)', margin: '0 0 4px' }}>Consumers</h1>
      <p style={{ fontSize: 14, color: 'var(--muted)', margin: '0 0 32px' }}>Click a row to see hourly traffic</p>

      <div style={{ background: '#fff', border: '1px solid var(--off-white)', borderRadius: 12, overflow: 'hidden', marginBottom: 24 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-heading)', fontSize: 14 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--off-white)' }}>
              {['Consumer','Total','Forwarded','Rate Limited','Avg Latency'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 11,
                  fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0
              ? <tr><td colSpan={5} style={{ padding: 32, textAlign: 'center', color: 'var(--muted)' }}>No consumers yet</td></tr>
              : data.map((r, i) => (
                <tr key={r.consumer_id}
                  onClick={() => setSelected(selected === r.consumer_id ? null : r.consumer_id)}
                  style={{ borderBottom: i < data.length - 1 ? '1px solid var(--off-white)' : 'none',
                    cursor: 'pointer', transition: 'background .15s',
                    background: selected === r.consumer_id ? '#fafafa' : '#fff' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--dark)' }}>{r.consumer_name}</td>
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

      {selected && (
        <div style={{ background: '#fff', border: '1px solid var(--off-white)', borderRadius: 12, padding: 24 }}>
          <div style={{ fontFamily: 'var(--font-heading)', fontSize: 12, fontWeight: 600, color: 'var(--sage)',
            letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: 16 }}>
            Hourly Traffic — Last 7 Days
          </div>
          <Sparkline providerId={providerId} consumerId={selected} />
        </div>
      )}
    </div>
  )
}
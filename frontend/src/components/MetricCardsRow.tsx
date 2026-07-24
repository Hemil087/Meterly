import { MetricCard } from './MetricCard';

/** The four dashboard metric cards, wired to the values shown in the design. */
export function MetricCardsRow() {
  return (
    <div style={{ display: 'flex', gap: 20 }}>
      <MetricCard label="Total Calls" value="1.24M" trend={{ direction: 'up', value: '8.2%' }} />
      <MetricCard label="Forwarded" value="1.19M" trend={{ direction: 'up', value: '7.9%' }} />
      <MetricCard
        label="Rate Limited"
        value="48.2K"
        trend={{ direction: 'up', value: '3.1%', tone: 'warning' }}
        accent
      />
      <MetricCard label="Avg Latency" value="86" unit="ms" trend={{ direction: 'down', value: '12ms' }} />
    </div>
  );
}

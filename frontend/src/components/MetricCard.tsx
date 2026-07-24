type Trend = {
  direction: 'up' | 'down';
  value: string;
  label?: string;
  tone?: 'positive' | 'warning';
};

type MetricCardProps = {
  label: string;
  value: string;
  unit?: string;
  trend: Trend;
  /** flags the card with a left accent border, e.g. to signal it needs attention */
  accent?: boolean;
};

const arrowPaths = {
  up: 'M6 10 V2 M6 2 L2.5 5.5 M6 2 L9.5 5.5',
  down: 'M6 2 V10 M6 10 L2.5 6.5 M6 10 L9.5 6.5',
};

function TrendArrow({ direction, color }: { direction: 'up' | 'down'; color: string }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path
        d={arrowPaths[direction]}
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function MetricCard({ label, value, unit, trend, accent }: MetricCardProps) {
  const toneColor = trend.tone === 'warning' ? 'var(--amber-text)' : 'var(--sage)';
  return (
    <div
      style={{
        flex: 1,
        background: '#ffffff',
        border: '1px solid var(--off-white)',
        borderLeft: accent ? '4px solid var(--light)' : undefined,
        borderRadius: 12,
        padding: accent ? '22px 24px 22px 21px' : '22px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-heading)',
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          color: 'var(--sage)',
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: 'var(--font-heading)',
          fontSize: 34,
          fontWeight: 600,
          lineHeight: 1,
          color: 'var(--dark)',
          letterSpacing: '-0.02em',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {value}
        {unit && <span style={{ fontSize: 18, fontWeight: 400, color: 'var(--sage)' }}>{unit}</span>}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13, fontWeight: 600, color: toneColor }}>
        <TrendArrow direction={trend.direction} color={toneColor} />
        <span>{trend.value}</span>
        <span style={{ color: 'var(--muted-2)', fontWeight: 400 }}>{trend.label ?? 'vs last week'}</span>
      </div>
    </div>
  );
}

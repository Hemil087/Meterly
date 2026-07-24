const DEFAULT_WIDTHS = [78, 56, 67];

/**
 * Three bars pulsing #F0F0F0 -> #D9E9CF on a staggered 1.5s loop, so the wave
 * reads left-to-right like data filling in ("data arriving", not a spinner).
 */
export function LoadingBars({ widths = DEFAULT_WIDTHS }: { widths?: number[] }) {
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid var(--off-white)',
        borderRadius: 12,
        padding: 40,
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      {widths.map((w, i) => (
        <div
          key={i}
          style={{
            height: 14,
            width: `${w}%`,
            borderRadius: 7,
            background: 'var(--off-white)',
            animation: 'meterly-bar-pulse 1.5s ease-in-out infinite',
            animationDelay: `${i * 0.18}s`,
          }}
        />
      ))}
    </div>
  );
}

import { useEffect, useRef, useState } from 'react';

const FALLBACK_ARC_LEN = 133;
const PERIOD_MS = 1800;
const STEP_MS = 30;

function easeInOutQuad(p: number) {
  return p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
}

/**
 * The Meterly gauge with the arc filling in and the needle sweeping as a
 * percentage counts 0->100 on a loop, then holds briefly before resetting.
 * Reads as "metering / data arriving," not a spinner.
 */
export function LoadingGauge() {
  const [t, setT] = useState(0);
  const [arcLen, setArcLen] = useState(FALLBACK_ARC_LEN);
  const fillPathRef = useRef<SVGPathElement | null>(null);

  useEffect(() => {
    const iv = setInterval(() => {
      setT((prev) => (prev + STEP_MS / PERIOD_MS) % 1);
    }, STEP_MS);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    const el = fillPathRef.current;
    if (el) {
      const len = el.getTotalLength();
      if (len && Math.abs(len - arcLen) > 0.5) setArcLen(len);
    }
    // measured once on mount; the path geometry is static
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // fill 0..1 with a gentle hold at the top
  const p = t < 0.85 ? t / 0.85 : 1;
  const eased = easeInOutQuad(p);
  const pct = Math.round(eased * 100);
  const arcOffset = (arcLen * (1 - eased)).toFixed(1);
  const needleDeg = (-90 + eased * 180).toFixed(1);

  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid var(--off-white)',
        borderRadius: 12,
        padding: 44,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 20,
      }}
    >
      <svg width="120" height="120" viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 66 A 32 32 0 1 1 76 66" stroke="var(--off-white)" strokeWidth="12" strokeLinecap="round" />
        <path
          ref={fillPathRef}
          d="M20 66 A 32 32 0 1 1 76 66"
          stroke="var(--light)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={arcLen}
          strokeDashoffset={arcOffset}
        />
        <g transform={`rotate(${needleDeg} 48 66)`}>
          <line x1="48" y1="66" x2="48" y2="30" stroke="var(--sage)" strokeWidth="6" strokeLinecap="round" />
        </g>
        <circle cx="48" cy="66" r="6" fill="var(--sage)" />
      </svg>
      <div
        style={{
          fontFamily: 'var(--font-heading)',
          fontSize: 40,
          fontWeight: 600,
          lineHeight: 1,
          color: 'var(--dark)',
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: '-0.02em',
        }}
      >
        {pct}
        <span style={{ fontSize: 22, fontWeight: 400, color: 'var(--sage)' }}>%</span>
      </div>
    </div>
  );
}

type EmptyStateProps = {
  title?: string;
  subtitle?: string;
};

/**
 * Quiet radar illustration: concentric rings, faint crosshairs, and a single
 * resting sweep line/wedge — no ping dots, so it reads as calm rather than alarming.
 */
export function EmptyState({
  title = 'No API calls yet',
  subtitle = 'Traffic will appear here once your first API call comes through.',
}: EmptyStateProps) {
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid var(--off-white)',
        borderRadius: 12,
        padding: '48px 40px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 28,
      }}
    >
      <svg width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="78" stroke="var(--light)" strokeWidth="3" />
        <circle cx="100" cy="100" r="52" stroke="var(--light)" strokeWidth="3" />
        <circle cx="100" cy="100" r="26" stroke="var(--light)" strokeWidth="3" />
        <line x1="22" y1="100" x2="178" y2="100" stroke="var(--light)" strokeWidth="2" strokeDasharray="2 7" strokeLinecap="round" />
        <line x1="100" y1="22" x2="100" y2="178" stroke="var(--light)" strokeWidth="2" strokeDasharray="2 7" strokeLinecap="round" />
        <path d="M100 100 L100 22 A78 78 0 0 1 155 45 Z" fill="var(--light)" opacity="0.55" />
        <line x1="100" y1="100" x2="100" y2="22" stroke="var(--sage)" strokeWidth="4" strokeLinecap="round" />
        <circle cx="100" cy="100" r="6" fill="var(--sage)" />
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, textAlign: 'center' }}>
        <div style={{ fontFamily: 'var(--font-heading)', fontSize: 18, fontWeight: 600, color: 'var(--dark)' }}>
          {title}
        </div>
        <div style={{ fontSize: 14, lineHeight: 1.5, color: 'var(--muted)', maxWidth: 300, textWrap: 'pretty' }}>
          {subtitle}
        </div>
      </div>
    </div>
  );
}

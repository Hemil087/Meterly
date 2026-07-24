import { Wordmark } from './Wordmark';

type NavItem = {
  label: string;
  active?: boolean;
  href?: string;
};

type DashboardHeaderProps = {
  navItems?: NavItem[];
  providerName?: string;
  providerInitials?: string;
};

const defaultNav: NavItem[] = [
  { label: 'Overview', active: true },
  { label: 'Consumers' },
  { label: 'Events' },
  { label: 'Keys' },
];

/** 64px top-level dashboard header with a 4px left accent strip. */
export function DashboardHeader({
  navItems = defaultNav,
  providerName = 'Northwind Data',
  providerInitials = 'ND',
}: DashboardHeaderProps) {
  return (
    <header
      style={{
        height: 64,
        background: '#ffffff',
        borderLeft: '4px solid var(--light)',
        borderBottom: '1px solid var(--off-white)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px 0 24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
        <Wordmark fontSize={22} />
        <nav style={{ display: 'flex', alignItems: 'center', gap: 28, fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 500 }}>
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href ?? '#'}
              style={{
                color: item.active ? 'var(--dark)' : 'var(--muted)',
                textDecoration: 'none',
                position: 'relative',
              }}
            >
              {item.label}
              {item.active && (
                <span
                  style={{
                    position: 'absolute',
                    left: 0,
                    right: 0,
                    bottom: -22,
                    height: 2,
                    background: 'var(--sage)',
                    borderRadius: 2,
                  }}
                />
              )}
            </a>
          ))}
        </nav>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
          <div style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, color: 'var(--dark)', lineHeight: 1 }}>
            {providerName}
          </div>
          <div style={{ fontSize: 11, color: 'var(--muted)', lineHeight: 1 }}>Provider</div>
        </div>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: 'var(--light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--font-heading)',
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--dark)',
          }}
        >
          {providerInitials}
        </div>
      </div>
    </header>
  );
}

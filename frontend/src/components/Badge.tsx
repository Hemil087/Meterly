import type { ReactNode } from 'react';

type BadgeProps = {
  variant?: 'success' | 'warning';
  size?: 'md' | 'sm';
  children: ReactNode;
};

const variants = {
  success: { color: 'var(--dark)', background: 'var(--light)' },
  // 429 badge uses a warm amber outside the core palette to read as "attention"
  warning: { color: 'var(--amber-text)', background: 'var(--amber-bg)' },
};

const sizes = {
  md: { fontSize: 12, padding: '5px 12px' },
  sm: { fontSize: 11, padding: '3px 10px' },
};

export function Badge({ variant = 'success', size = 'md', children }: BadgeProps) {
  return (
    <span
      style={{
        fontFamily: 'var(--font-mono)',
        fontWeight: 500,
        borderRadius: 999,
        ...sizes[size],
        ...variants[variant],
      }}
    >
      {children}
    </span>
  );
}

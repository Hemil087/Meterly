import type { ButtonHTMLAttributes } from 'react';
import { useState } from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary';
};

const base: React.CSSProperties = {
  fontFamily: 'var(--font-heading)',
  fontSize: 14,
  fontWeight: 600,
  borderRadius: 8,
  cursor: 'pointer',
  transition: 'background 0.15s ease',
};

const variants: Record<'primary' | 'secondary', { rest: React.CSSProperties; hover: React.CSSProperties }> = {
  primary: {
    rest: { color: '#ffffff', background: 'var(--sage)', border: 'none', padding: '11px 20px' },
    hover: { background: 'var(--sage-hover)' },
  },
  secondary: {
    rest: {
      color: 'var(--dark)',
      background: '#ffffff',
      border: '1px solid var(--light)',
      padding: '10px 19px',
    },
    hover: { background: 'var(--off-white)' },
  },
};

export function Button({ variant = 'primary', style, children, ...rest }: ButtonProps) {
  const [hovered, setHovered] = useState(false);
  const v = variants[variant];
  return (
    <button
      {...rest}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ ...base, ...v.rest, ...(hovered ? v.hover : null), ...style }}
    >
      {children}
    </button>
  );
}

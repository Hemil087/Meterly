type FaviconProps = {
  size?: number;
  color?: string;
  className?: string;
};

/**
 * Single-color reduction of the LogoMark for tiny sizes (16-32px, favicons,
 * app icons). Arc thickened and needle shortened so both survive at 16px.
 */
export function Favicon({ size = 32, color = 'var(--sage)', className }: FaviconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 96 96"
      fill="none"
      className={className}
      role="img"
      aria-label="Meterly"
    >
      <path
        d="M22 68 A 30 30 0 1 1 74 68"
        stroke={color}
        strokeWidth="14"
        strokeLinecap="round"
      />
      <line x1="48" y1="52" x2="62" y2="34" stroke={color} strokeWidth="14" strokeLinecap="round" />
    </svg>
  );
}

type LogoMarkProps = {
  /** pixel size of the square icon */
  size?: number;
  arcColor?: string;
  needleColor?: string;
  className?: string;
};

/**
 * The Meterly dial mark: an open gauge arc with a needle at load.
 * This is the two-tone mark used everywhere except the monochrome favicon.
 */
export function LogoMark({
  size = 40,
  arcColor = 'var(--light)',
  needleColor = 'var(--sage)',
  className,
}: LogoMarkProps) {
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
        d="M20 66 A 32 32 0 1 1 76 66"
        stroke={arcColor}
        strokeWidth="12"
        strokeLinecap="round"
      />
      <line
        x1="48"
        y1="58"
        x2="63"
        y2="37"
        stroke={needleColor}
        strokeWidth="12"
        strokeLinecap="round"
      />
    </svg>
  );
}

import { LogoMark } from './LogoMark';

type WordmarkProps = {
  /** font size of the "meterly" text; the logo mark scales to match */
  fontSize?: number;
  gap?: number;
  className?: string;
};

/**
 * Horizontal lockup: dial mark + "meter" (600) / "ly" (400) in Poppins,
 * dark sage text. Scales from hero size down to favicon scale.
 */
export function Wordmark({ fontSize = 28, gap, className }: WordmarkProps) {
  const logoSize = Math.round(fontSize * 1.43);
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: gap ?? Math.round(fontSize * 0.5),
      }}
    >
      <LogoMark size={logoSize} />
      <div
        style={{
          fontFamily: 'var(--font-heading)',
          fontSize,
          lineHeight: 1,
          letterSpacing: '-0.01em',
          color: 'var(--dark)',
        }}
      >
        <span style={{ fontWeight: 600 }}>meter</span>
        <span style={{ fontWeight: 400 }}>ly</span>
      </div>
    </div>
  );
}

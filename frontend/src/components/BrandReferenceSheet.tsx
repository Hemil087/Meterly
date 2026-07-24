import { Wordmark } from './Wordmark';
import { Button } from './Button';
import { Badge } from './Badge';

const swatches = [
  { name: 'Sage', hex: '#96A78D' },
  { name: 'Mid', hex: '#B6CEB4' },
  { name: 'Light', hex: '#D9E9CF' },
  { name: 'Off-white', hex: '#F0F0F0' },
  { name: 'Dark', hex: '#3D4A38' },
];

const sectionHeading: React.CSSProperties = {
  fontFamily: 'var(--font-heading)',
  fontSize: 13,
  fontWeight: 600,
  letterSpacing: '0.04em',
  textTransform: 'uppercase',
  color: 'var(--sage)',
};

/** Developer-facing brand reference: palette, type pairing, and core UI atoms. */
export function BrandReferenceSheet() {
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid var(--off-white)',
        borderRadius: 14,
        padding: 36,
        display: 'flex',
        flexDirection: 'column',
        gap: 32,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--off-white)',
          paddingBottom: 24,
        }}
      >
        <Wordmark fontSize={28} />
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--sage)', letterSpacing: '0.02em' }}>
          brand reference v1
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={sectionHeading}>Color palette</div>
        <div style={{ display: 'flex', gap: 14 }}>
          {swatches.map((s) => (
            <div key={s.hex} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div
                style={{
                  height: 72,
                  borderRadius: 10,
                  background: s.hex,
                  border: s.hex === '#F0F0F0' ? '1px solid #e6e6e6' : undefined,
                }}
              />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <div style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, color: 'var(--dark)' }}>
                  {s.name}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)' }}>{s.hex}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 32 }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={sectionHeading}>Headings — Poppins</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 32,
                fontWeight: 600,
                color: 'var(--dark)',
                lineHeight: 1.05,
                letterSpacing: '-0.02em',
              }}
            >
              Aa Bb Cc
            </div>
            <div style={{ fontFamily: 'var(--font-heading)', fontSize: 15, fontWeight: 400, color: 'var(--dark)' }}>
              Geometric sans · 400 / 500 / 600
            </div>
          </div>
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={sectionHeading}>Data — JetBrains Mono</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 30, fontWeight: 500, color: 'var(--dark)', lineHeight: 1.05 }}>
              1,240,318
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 400, color: 'var(--dark)' }}>
              Monospace · figures &amp; IDs
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={sectionHeading}>UI components</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <Button variant="primary">Create key</Button>
          <Button variant="secondary">Secondary</Button>
          <Badge variant="success">200 OK</Badge>
          <Badge variant="warning">429 Limited</Badge>
        </div>
        <div style={{ border: '1px solid var(--off-white)', borderRadius: 10, overflow: 'hidden' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1.4fr 1fr 0.8fr 0.8fr',
              alignItems: 'center',
              gap: 12,
              padding: '11px 18px',
              background: 'var(--off-white)',
              fontFamily: 'var(--font-heading)',
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              color: 'var(--sage)',
            }}
          >
            <div>Consumer</div>
            <div>Endpoint</div>
            <div>Calls</div>
            <div>Status</div>
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1.4fr 1fr 0.8fr 0.8fr',
              alignItems: 'center',
              gap: 12,
              padding: '14px 18px',
              borderTop: '1px solid var(--off-white)',
            }}
          >
            <div style={{ fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 500, color: 'var(--dark)' }}>
              acme-corp
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--muted)' }}>/v1/query</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--dark)' }}>18,204</div>
            <div>
              <Badge variant="success" size="sm">Healthy</Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Wordmark } from './components/Wordmark'
import { Overview } from './pages/Overview'
import { Consumers } from './pages/Consumers'
import { Events } from './pages/Events'
import { Keys } from './pages/Keys'

const PROVIDER_ID = 1

const NAV = [
  { to: '/',          label: 'Overview'  },
  { to: '/consumers', label: 'Consumers' },
  { to: '/events',    label: 'Events'    },
  { to: '/keys',      label: 'Keys'      },
]

function Header() {
  return (
    <header style={{
      height: 64, background: '#fff',
      borderLeft: '4px solid var(--light)',
      borderBottom: '1px solid var(--off-white)',
      display: 'flex', alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 28px 0 24px',
      position: 'sticky', top: 0, zIndex: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
        <Wordmark fontSize={22} />
        <nav style={{ display: 'flex', gap: 28 }}>
          {NAV.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              style={({ isActive }) => ({
                color: isActive ? 'var(--dark)' : 'var(--muted)',
                textDecoration: 'none',
                fontFamily: 'var(--font-heading)',
                fontSize: 14, fontWeight: 500,
                position: 'relative' as const,
                paddingBottom: 4,
                borderBottom: isActive ? '2px solid var(--sage)' : '2px solid transparent',
              })}
            >{label}</NavLink>
          ))}
        </nav>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, color: 'var(--dark)' }}>TestCorp</div>
          <div style={{ fontSize: 11, color: 'var(--muted)' }}>Provider</div>
        </div>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'var(--light)', display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          fontFamily: 'var(--font-heading)', fontSize: 13,
          fontWeight: 600, color: 'var(--dark)',
        }}>TC</div>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main style={{ padding: '40px 48px', maxWidth: 1200, margin: '0 auto' }}>
        <Routes>
          <Route path="/"          element={<Overview   providerId={PROVIDER_ID} />} />
          <Route path="/consumers" element={<Consumers  providerId={PROVIDER_ID} />} />
          <Route path="/events"    element={<Events     providerId={PROVIDER_ID} />} />
          <Route path="/keys"      element={<Keys       providerId={PROVIDER_ID} />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
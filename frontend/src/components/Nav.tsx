import { Link, NavLink } from 'react-router-dom'
import './Nav.css'

// Matches backend/seed.py's DEMO_PURSUIT_ID — the healthy demo pursuit the splash figure and
// this nav's "Demo" link both point at.
const DEMO_PURSUIT_ID = 'demo-avionics-idiq'

export default function Nav() {
  return (
    <nav className="wm-nav">
      <NavLink to="/about" className="wm-nav__brand">
        WinMax
      </NavLink>
      <div className="wm-nav__links">
        <NavLink
          to={`/pursuits/${DEMO_PURSUIT_ID}`}
          className={({ isActive }) => `wm-nav__link ${isActive ? 'wm-nav__link--active' : ''}`}
        >
          Demo
        </NavLink>
        <NavLink
          to="/"
          end
          className={({ isActive }) => `wm-nav__link ${isActive ? 'wm-nav__link--active' : ''}`}
        >
          Pursuits
        </NavLink>
      </div>
      <Link className="wm-btn wm-btn--primary wm-nav__new" to="/?new=1">+ New pursuit</Link>
    </nav>
  )
}

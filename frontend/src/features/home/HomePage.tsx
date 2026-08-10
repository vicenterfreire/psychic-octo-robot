import { Link } from 'react-router-dom'
import { ApiStatus } from '../health/ApiStatus'

export function HomePage() {
  return (
    <div className="page-shell">
      <header className="site-header">
        <Link className="brand" to="/" aria-label="Gather home">
          <span className="brand__mark" aria-hidden="true" />
          Gather
        </Link>
        <Link className="header-link" to="/login">
          Sign in
        </Link>
      </header>

      <main className="hero">
        <p className="eyebrow">Events worth showing up for</p>
        <h1>One place to publish, reserve, and welcome every guest.</h1>
        <p className="hero__summary">
          A secure session now connects organizer, customer, and gate experiences. The complete
          event journey arrives in focused, reviewable increments.
        </p>

        <Link className="hero-link" to="/login">
          Enter the platform <span aria-hidden="true">→</span>
        </Link>

        <div className="foundation-card">
          <div>
            <p className="foundation-card__label">Foundation status</p>
            <h2>Frontend, API, database, and sessions are connected.</h2>
          </div>
          <ApiStatus />
        </div>
      </main>

      <footer className="site-footer">
        <span>React + FastAPI</span>
        <span>Built incrementally</span>
      </footer>
    </div>
  )
}

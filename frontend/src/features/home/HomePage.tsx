import { ApiStatus } from '../health/ApiStatus'

export function HomePage() {
  return (
    <div className="page-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="Gather home">
          <span className="brand__mark" aria-hidden="true" />
          Gather
        </a>
        <span className="project-label">Elite Dev Challenge 2026</span>
      </header>

      <main className="hero">
        <p className="eyebrow">Events worth showing up for</p>
        <h1>One place to publish, reserve, and welcome every guest.</h1>
        <p className="hero__summary">
          The foundation is live. Organizer, customer, and gate workflows will arrive in focused,
          reviewable increments.
        </p>

        <div className="foundation-card">
          <div>
            <p className="foundation-card__label">Foundation status</p>
            <h2>Frontend and API are ready to evolve.</h2>
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

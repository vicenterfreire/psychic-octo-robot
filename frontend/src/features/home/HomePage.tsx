import { Link } from 'react-router-dom'
import { ApiStatus } from '../health/components/ApiStatus'
import styles from './home.module.css'

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

      <main className={styles.hero}>
        <p className="eyebrow">Events worth showing up for</p>
        <h1>One place to publish, reserve, and welcome every guest.</h1>
        <p className={styles['hero-summary']}>
          A secure session now connects organizer, customer, and gate experiences. The complete
          event journey arrives in focused, reviewable increments.
        </p>

        <Link className={styles['hero-link']} to="/events">
          Browse published events <span aria-hidden="true">→</span>
        </Link>

        <div className={styles['foundation-card']}>
          <div>
            <p className={styles['foundation-card-label']}>Foundation status</p>
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

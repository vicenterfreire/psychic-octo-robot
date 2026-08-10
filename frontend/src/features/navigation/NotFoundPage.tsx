import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="centered-page">
      <p className="eyebrow">404</p>
      <h1>This event is not on the schedule.</h1>
      <Link className="text-link" to="/">
        Return home
      </Link>
    </main>
  )
}

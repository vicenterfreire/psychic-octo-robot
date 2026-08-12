import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { formatEventDate } from '../../lib/event-display'
import { SiteHeader } from '../navigation/components/SiteHeader'
import { TicketQrCode } from './components/TicketQrCode'
import { customerTicketsQueryKey, getCustomerTickets } from './tickets-api'
import styles from './tickets.module.css'

interface CopyFeedback {
  ticketId: string
  message: string
}

export function CustomerTicketsPage() {
  const [copyFeedback, setCopyFeedback] = useState<CopyFeedback | null>(null)
  const ticketsQuery = useQuery({
    queryKey: customerTicketsQueryKey,
    queryFn: getCustomerTickets,
  })

  async function copyShareLink(ticketId: string, shareUrl: string) {
    if (!navigator.clipboard) {
      setCopyFeedback({ ticketId, message: 'Clipboard access is unavailable in this browser.' })
      return
    }
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopyFeedback({ ticketId, message: 'Sharing link copied.' })
    } catch {
      setCopyFeedback({ ticketId, message: 'Could not copy the link. Open it instead.' })
    }
  }

  if (ticketsQuery.isPending) {
    return <main className="centered-page">Loading your tickets...</main>
  }

  if (ticketsQuery.isError) {
    return (
      <main className="centered-page">
        <p className="eyebrow">Tickets unavailable</p>
        <h1>We could not load your tickets.</h1>
        <button className="primary-button" type="button" onClick={() => ticketsQuery.refetch()}>
          Try again
        </button>
      </main>
    )
  }

  return (
    <div className="page-shell">
      <SiteHeader authenticated />
      <main className={styles['tickets-workspace']}>
        <div className={styles['tickets-heading']}>
          <div>
            <p className="eyebrow">Customer wallet</p>
            <h1>My Tickets</h1>
            <p>Present the QR at the gate or share its bearer link with someone you trust.</p>
          </div>
          <Link className="secondary-button" to="/customer">
            Browse events
          </Link>
        </div>

        {ticketsQuery.data.length === 0 ? (
          <section className="empty-panel">
            <h2>No tickets yet.</h2>
            <p>Approved reservations will appear here.</p>
          </section>
        ) : (
          <div className={styles['ticket-list']}>
            {ticketsQuery.data.map((ticket) => (
              <article className={styles['ticket-card']} key={ticket.id}>
                <div className={styles['ticket-card__details']}>
                  <p className="eyebrow">Ticket #{ticket.ticket_number}</p>
                  <h2>{ticket.event.name}</h2>
                  <p>{formatEventDate(ticket.event.start_at)}</p>
                  <p>
                    {ticket.event.venue_name} · {ticket.event.city}, {ticket.event.country_code}
                  </p>
                  <span
                    className={`${styles['ticket-state']} ${
                      ticket.is_used || ticket.is_revoked ? styles['ticket-state--used'] : ''
                    }`}
                  >
                    {ticket.is_revoked
                      ? 'Ticket revoked'
                      : ticket.is_used
                        ? 'Already used'
                        : 'Ready for entry'}
                  </span>
                  <div className={styles['ticket-card__actions']}>
                    <button
                      className="primary-button"
                      type="button"
                      onClick={() => copyShareLink(ticket.id, ticket.share_url)}
                    >
                      Copy sharing link
                    </button>
                    <a className="secondary-button" href={ticket.share_url}>
                      Open shared view
                    </a>
                  </div>
                  {copyFeedback?.ticketId === ticket.id && (
                    <p className={styles['ticket-copy-feedback']} aria-live="polite">
                      {copyFeedback.message}
                    </p>
                  )}
                  <p className={styles['ticket-bearer-warning']}>
                    Anyone with the link can present this ticket. Share it only with someone you
                    trust.
                  </p>
                </div>
                <TicketQrCode token={ticket.token} label={`QR for ${ticket.event.name}`} />
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

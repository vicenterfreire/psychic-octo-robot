import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { logout, sessionQueryKey } from '../auth/auth-api'
import { useSession } from '../auth/use-session'
import { ApiError } from '../../lib/api-client'
import { type CatalogEvent, searchCatalogEvents } from './catalog-api'

function providerErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  return 'Unable to reach the catalog service.'
}

export function OrganizerCatalogPage() {
  const [query, setQuery] = useState('')
  const [selectedEvent, setSelectedEvent] = useState<CatalogEvent | null>(null)
  const session = useSession()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const searchMutation = useMutation({
    mutationFn: searchCatalogEvents,
    onSuccess: () => setSelectedEvent(null),
  })
  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(sessionQueryKey, null)
      navigate('/login', { replace: true })
    },
  })

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    searchMutation.mutate(query.trim())
  }

  const results = searchMutation.data?.items ?? []

  return (
    <div className="page-shell">
      <header className="site-header">
        <Link className="brand" to="/" aria-label="Gather home">
          <span className="brand__mark" aria-hidden="true" />
          Gather
        </Link>
        <div className="workspace-account">
          <span className="account-chip">{session.data?.email}</span>
          <button
            className="header-action"
            type="button"
            disabled={logoutMutation.isPending}
            onClick={() => logoutMutation.mutate()}
          >
            {logoutMutation.isPending ? 'Signing out...' : 'Sign out'}
          </button>
        </div>
      </header>

      <main className="catalog-workspace">
        <section className="catalog-intro">
          <div>
            <p className="eyebrow">Organizer catalog</p>
            <h1>Start with something people already love.</h1>
          </div>
          <p>
            Search Ticketmaster for source material. You will define the local date, venue,
            capacity, and price in the next step.
          </p>
        </section>

        <form className="catalog-search" role="search" onSubmit={submitSearch}>
          <label htmlFor="catalog-query">Event or artist</label>
          <div>
            <input
              id="catalog-query"
              name="q"
              type="search"
              minLength={2}
              maxLength={100}
              placeholder="Try Aurora, jazz, football..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              required
            />
            <button className="primary-button" type="submit" disabled={searchMutation.isPending}>
              {searchMutation.isPending ? 'Searching...' : 'Search catalog'}
            </button>
          </div>
        </form>

        <div className="catalog-feedback" aria-live="polite">
          {searchMutation.isError && (
            <p className="form-error">{providerErrorMessage(searchMutation.error)}</p>
          )}
          {searchMutation.isSuccess && results.length === 0 && (
            <p>No Ticketmaster events matched this search. Try another complete word.</p>
          )}
          {selectedEvent && (
            <p className="selection-notice">
              Selected <strong>{selectedEvent.name}</strong>. Local event details arrive in the next
              increment.
            </p>
          )}
        </div>

        {results.length > 0 && (
          <section className="catalog-results" aria-label="Ticketmaster search results">
            {results.map((event) => {
              const isSelected = selectedEvent?.provider_event_id === event.provider_event_id
              return (
                <article className="catalog-card" key={event.provider_event_id}>
                  <div className="catalog-card__image">
                    {event.image_url ? (
                      <img src={event.image_url} alt="" />
                    ) : (
                      <span aria-hidden="true">TM</span>
                    )}
                  </div>
                  <div className="catalog-card__content">
                    <p className="catalog-card__provider">Ticketmaster source</p>
                    <h2>{event.name}</h2>
                    <p>{event.description ?? 'No provider description is available.'}</p>
                    <div className="catalog-card__actions">
                      <button
                        className="secondary-button"
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => setSelectedEvent(event)}
                      >
                        {isSelected ? 'Selected' : 'Use this event'}
                      </button>
                      {event.source_url && (
                        <a href={event.source_url} target="_blank" rel="noreferrer">
                          View source
                        </a>
                      )}
                    </div>
                  </div>
                </article>
              )
            })}
          </section>
        )}
      </main>
    </div>
  )
}

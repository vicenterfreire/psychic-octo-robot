import { createBrowserRouter } from 'react-router-dom'
import { LoginPage } from '../features/auth/LoginPage'
import { RequireRole } from '../features/auth/RequireRole'
import { RequireSession } from '../features/auth/RequireSession'
import { SessionRedirect } from '../features/auth/SessionRedirect'
import { OrganizerCatalogPage } from '../features/catalog/OrganizerCatalogPage'
import { EventDetailPage } from '../features/discovery/EventDetailPage'
import { EventDiscoveryPage } from '../features/discovery/EventDiscoveryPage'
import { GateValidationPage } from '../features/gate/GateValidationPage'
import { HomePage } from '../features/home/HomePage'
import { NotFoundPage } from '../features/navigation/NotFoundPage'
import { ReservationHoldPage } from '../features/reservations/ReservationHoldPage'
import { CustomerTicketsPage } from '../features/tickets/CustomerTicketsPage'
import { SharedTicketPage } from '../features/tickets/SharedTicketPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/events',
    element: <EventDiscoveryPage />,
  },
  {
    path: '/events/:eventId',
    element: <EventDetailPage />,
  },
  {
    path: '/tickets/share/:token',
    element: <SharedTicketPage />,
  },
  {
    element: <RequireSession />,
    children: [
      { path: '/app', element: <SessionRedirect /> },
      {
        path: '/organizer',
        element: (
          <RequireRole role="organizer">
            <OrganizerCatalogPage />
          </RequireRole>
        ),
      },
      {
        path: '/customer',
        element: (
          <RequireRole role="customer">
            <EventDiscoveryPage authenticated />
          </RequireRole>
        ),
      },
      {
        path: '/customer/events/:eventId',
        element: (
          <RequireRole role="customer">
            <EventDetailPage authenticated />
          </RequireRole>
        ),
      },
      {
        path: '/customer/reservations/:reservationId',
        element: (
          <RequireRole role="customer">
            <ReservationHoldPage />
          </RequireRole>
        ),
      },
      {
        path: '/customer/tickets',
        element: (
          <RequireRole role="customer">
            <CustomerTicketsPage />
          </RequireRole>
        ),
      },
      {
        path: '/gate',
        element: (
          <RequireRole role="gate">
            <GateValidationPage />
          </RequireRole>
        ),
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])

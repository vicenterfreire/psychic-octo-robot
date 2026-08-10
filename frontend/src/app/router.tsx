import { createBrowserRouter } from 'react-router-dom'
import { LoginPage } from '../features/auth/LoginPage'
import { RequireRole } from '../features/auth/RequireRole'
import { RequireSession } from '../features/auth/RequireSession'
import { RoleHomePage } from '../features/auth/RoleHomePage'
import { SessionRedirect } from '../features/auth/SessionRedirect'
import { OrganizerCatalogPage } from '../features/catalog/OrganizerCatalogPage'
import { EventDetailPage } from '../features/discovery/EventDetailPage'
import { EventDiscoveryPage } from '../features/discovery/EventDiscoveryPage'
import { HomePage } from '../features/home/HomePage'
import { NotFoundPage } from '../features/navigation/NotFoundPage'

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
        path: '/gate',
        element: (
          <RequireRole role="gate">
            <RoleHomePage role="gate" />
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

import { createBrowserRouter } from 'react-router-dom'
import { LoginPage } from '../features/auth/LoginPage'
import { RequireRole } from '../features/auth/RequireRole'
import { RequireSession } from '../features/auth/RequireSession'
import { RoleHomePage } from '../features/auth/RoleHomePage'
import { SessionRedirect } from '../features/auth/SessionRedirect'
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
    element: <RequireSession />,
    children: [
      { path: '/app', element: <SessionRedirect /> },
      {
        path: '/organizer',
        element: (
          <RequireRole role="organizer">
            <RoleHomePage role="organizer" />
          </RequireRole>
        ),
      },
      {
        path: '/customer',
        element: (
          <RequireRole role="customer">
            <RoleHomePage role="customer" />
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

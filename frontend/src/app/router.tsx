import { createBrowserRouter } from 'react-router-dom'
import { HomePage } from '../features/home/HomePage'
import { NotFoundPage } from '../features/navigation/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])

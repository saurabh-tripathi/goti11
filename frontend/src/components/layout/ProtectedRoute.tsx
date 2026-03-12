import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import LoadingSpinner from '../common/LoadingSpinner'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return <LoadingSpinner size="lg" />
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isAdmin, isLoading } = useAuth()
  if (isLoading) return <LoadingSpinner size="lg" />
  if (!user) return <Navigate to="/login" replace />
  if (!isAdmin) return <Navigate to="/matches" replace />
  return <>{children}</>
}

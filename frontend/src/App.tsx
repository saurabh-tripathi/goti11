import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import AppLayout from './components/layout/AppLayout'
import { ProtectedRoute, AdminRoute } from './components/layout/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import MatchListPage from './pages/MatchListPage'
import TeamSelectionPage from './pages/TeamSelectionPage'
import LeaderboardPage from './pages/LeaderboardPage'
import AdminMatchesPage from './pages/admin/AdminMatchesPage'
import AdminMatchDetailPage from './pages/admin/AdminMatchDetailPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminSeriesPage from './pages/admin/AdminSeriesPage'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route index element={<Navigate to="/matches" replace />} />
          <Route path="/matches" element={<MatchListPage />} />
          <Route path="/matches/:matchId/team" element={<TeamSelectionPage />} />
          <Route path="/matches/:matchId/leaderboard" element={<LeaderboardPage />} />

          <Route path="/admin" element={<AdminRoute><AdminMatchesPage /></AdminRoute>} />
          <Route path="/admin/matches/:matchId" element={<AdminRoute><AdminMatchDetailPage /></AdminRoute>} />
          <Route path="/admin/users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
          <Route path="/admin/series" element={<AdminRoute><AdminSeriesPage /></AdminRoute>} />
        </Route>

        <Route path="*" element={<Navigate to="/matches" replace />} />
      </Routes>
    </AuthProvider>
  )
}

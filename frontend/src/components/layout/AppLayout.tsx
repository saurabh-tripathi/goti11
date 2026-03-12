import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function AppLayout() {
  const { user, isAdmin, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-navy-900 flex flex-col">
      <nav className="bg-navy-800 border-b border-navy-700 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          {/* Logo */}
          <Link to="/matches" className="font-bold text-xl text-teal-400 tracking-tight">
            Goti<span className="text-white">11</span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1 text-sm">
            <NavLink
              to="/matches"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg transition-colors ${
                  isActive ? 'bg-teal-500/20 text-teal-400' : 'text-gray-300 hover:text-white'
                }`
              }
            >
              Matches
            </NavLink>

            {isAdmin && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-lg transition-colors ${
                    isActive ? 'bg-teal-500/20 text-teal-400' : 'text-gray-300 hover:text-white'
                  }`
                }
              >
                Admin
              </NavLink>
            )}

            <div className="flex items-center gap-2 ml-2 pl-2 border-l border-navy-600">
              <button
                onClick={() => navigate('/matches')}
                className="text-gray-400 text-xs hover:text-white"
              >
                {user?.username}
              </button>
              <button
                onClick={logout}
                className="text-xs px-2 py-1 rounded bg-navy-700 text-gray-400 hover:text-white hover:bg-navy-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

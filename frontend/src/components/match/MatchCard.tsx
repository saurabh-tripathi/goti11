import { useNavigate } from 'react-router-dom'
import type { Match } from '../../types'
import StatusBadge from '../common/StatusBadge'

function formatDate(dt: string | null): string {
  if (!dt) return 'TBD'
  return new Date(dt).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function MatchCard({ match }: { match: Match }) {
  const navigate = useNavigate()

  const canSelectTeam = ['upcoming', 'squad_synced'].includes(match.status)

  const handleClick = () => {
    if (canSelectTeam) {
      navigate(`/matches/${match.id}/team`)
    } else {
      navigate(`/matches/${match.id}/leaderboard`)
    }
  }

  return (
    <div
      onClick={handleClick}
      className="bg-navy-800 border border-navy-700 rounded-xl p-4 cursor-pointer hover:border-teal-500 transition-colors"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-white">{match.name}</h3>
          <p className="text-sm text-gray-400 mt-1">
            {match.team_a} <span className="text-teal-400">vs</span> {match.team_b}
          </p>
        </div>
        <StatusBadge status={match.status} />
      </div>
      <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
        <span>{formatDate(match.scheduled_at)}</span>
        {parseFloat(match.prize_pool) > 0 && (
          <span className="text-gold-400 font-semibold">
            Prize: ₹{parseFloat(match.prize_pool).toLocaleString()}
          </span>
        )}
      </div>
      <div className="mt-2 text-xs text-teal-400">
        {canSelectTeam ? 'Tap to select your team →' : 'Tap to view leaderboard →'}
      </div>
    </div>
  )
}

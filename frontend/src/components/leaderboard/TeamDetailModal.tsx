import type { Team, TeamPlayerDetail } from '../../types'
import LoadingSpinner from '../common/LoadingSpinner'

const ROLE_COLORS: Record<string, string> = {
  WK: 'bg-purple-900 text-purple-300',
  BAT: 'bg-blue-900 text-blue-300',
  AR: 'bg-orange-900 text-orange-300',
  BOWL: 'bg-green-900 text-green-300',
}

function PlayerRow({ p }: { p: TeamPlayerDetail }) {
  const roleStyle = ROLE_COLORS[p.role] ?? 'bg-gray-700 text-gray-300'
  const multiplier = parseFloat(p.multiplier)
  const finalPts = parseFloat(p.final_points)
  const basePts = parseFloat(p.points_earned)

  return (
    <div className={`flex items-center gap-3 py-2.5 px-4 border-b border-navy-700/50 last:border-0 ${
      p.is_captain ? 'bg-gold-400/5' : p.is_vice_captain ? 'bg-teal-400/5' : ''
    }`}>
      {/* Captain / VC badge */}
      <div className="w-7 flex-shrink-0 text-center">
        {p.is_captain && (
          <span className="inline-block bg-gold-400 text-navy-900 text-xs font-bold px-1.5 py-0.5 rounded">C</span>
        )}
        {p.is_vice_captain && (
          <span className="inline-block bg-teal-400 text-navy-900 text-xs font-bold px-1.5 py-0.5 rounded">VC</span>
        )}
      </div>

      {/* Name + role */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white truncate">{p.name}</div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${roleStyle}`}>{p.role}</span>
          {p.ipl_team && <span className="text-xs text-gray-500">{p.ipl_team}</span>}
        </div>
      </div>

      {/* Points breakdown */}
      <div className="text-right flex-shrink-0">
        <div className="text-sm font-semibold text-teal-400 font-mono">
          {finalPts.toFixed(1)}
        </div>
        {multiplier !== 1 && (
          <div className="text-xs text-gray-500 font-mono">
            {basePts.toFixed(1)} × {multiplier}
          </div>
        )}
      </div>
    </div>
  )
}

interface Props {
  username: string
  team: Team | null
  isLoading: boolean
  onClose: () => void
}

export default function TeamDetailModal({ username, team, isLoading, onClose }: Props) {
  // Sort: captain first, then VC, then by final_points desc
  const sorted = team
    ? [...team.players].sort((a, b) => {
        if (a.is_captain) return -1
        if (b.is_captain) return 1
        if (a.is_vice_captain) return -1
        if (b.is_vice_captain) return 1
        return parseFloat(b.final_points) - parseFloat(a.final_points)
      })
    : []

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-navy-800 border border-navy-700 rounded-t-2xl sm:rounded-2xl w-full sm:max-w-md max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-navy-700">
          <div>
            <h2 className="font-semibold text-white">{username}'s Team</h2>
            {team && (
              <p className="text-xs text-gray-400 mt-0.5">
                Total: <span className="text-teal-400 font-mono font-semibold">
                  {parseFloat(team.total_points).toFixed(1)} pts
                </span>
                {team.rank && (
                  <span className="ml-2 text-gray-400">· Rank #{team.rank}</span>
                )}
                {parseFloat(team.prize_awarded) > 0 && (
                  <span className="ml-2 text-gold-400">
                    · ₹{parseFloat(team.prize_awarded).toLocaleString()}
                  </span>
                )}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl leading-none p-1"
          >
            ✕
          </button>
        </div>

        {/* Column headers */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-navy-700/50 bg-navy-900/40">
          <div className="w-7" />
          <div className="flex-1 text-xs text-gray-500 uppercase tracking-wide">Player</div>
          <div className="text-xs text-gray-500 uppercase tracking-wide text-right">Pts</div>
        </div>

        {/* Player list */}
        <div className="overflow-y-auto flex-1">
          {isLoading ? (
            <LoadingSpinner />
          ) : team ? (
            sorted.map((p) => <PlayerRow key={p.player_id} p={p} />)
          ) : (
            <p className="text-center text-gray-500 py-8 text-sm">Team not available</p>
          )}
        </div>
      </div>
    </div>
  )
}

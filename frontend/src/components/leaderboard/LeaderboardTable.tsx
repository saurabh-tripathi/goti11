import type { LeaderboardEntry } from '../../types'
import { useAuth } from '../../context/AuthContext'

interface Props {
  entries: LeaderboardEntry[]
  onRowClick?: (entry: LeaderboardEntry) => void
  clickableUserIds?: Set<string>
}

export default function LeaderboardTable({ entries, onRowClick, clickableUserIds }: Props) {
  const { user } = useAuth()

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-navy-700">
            <th className="text-left py-2 px-3">#</th>
            <th className="text-left py-2 px-3">Player</th>
            <th className="text-left py-2 px-3">Captain</th>
            <th className="text-left py-2 px-3">V.Captain</th>
            <th className="text-right py-2 px-3">Points</th>
            <th className="text-right py-2 px-3">Prize</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => {
            const isMe = entry.user_id === user?.id
            const isClickable = onRowClick && (
              clickableUserIds ? clickableUserIds.has(entry.user_id) : isMe
            )
            return (
              <tr
                key={entry.user_id}
                onClick={isClickable ? () => onRowClick(entry) : undefined}
                className={`border-b border-navy-700/50 transition-colors ${
                  isMe ? 'bg-teal-500/10 font-semibold' : ''
                } ${isClickable ? 'cursor-pointer hover:bg-navy-700/60' : ''}`}
              >
                <td className="py-2 px-3 text-gray-400">{entry.rank}</td>
                <td className="py-2 px-3">
                  <span className="text-white">{entry.username}</span>
                  {isMe && <span className="ml-1 text-teal-400 text-xs">(you)</span>}
                  {isClickable && (
                    <span className="ml-1.5 text-gray-500 text-xs">↗</span>
                  )}
                </td>
                <td className="py-2 px-3 text-gray-300">{entry.captain_name}</td>
                <td className="py-2 px-3 text-gray-300">{entry.vice_captain_name}</td>
                <td className="py-2 px-3 text-right text-teal-400 font-mono">
                  {parseFloat(entry.total_points).toFixed(1)}
                </td>
                <td className="py-2 px-3 text-right text-gold-400 font-mono">
                  {parseFloat(entry.prize_awarded) > 0
                    ? `₹${parseFloat(entry.prize_awarded).toLocaleString()}`
                    : '—'}
                </td>
              </tr>
            )
          })}
          {entries.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center text-gray-500 py-8">
                No entries yet
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

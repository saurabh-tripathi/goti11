import type { MatchPlayer } from '../../types'

const ROLE_COLORS: Record<string, string> = {
  WK: 'bg-purple-900 text-purple-300',
  BAT: 'bg-blue-900 text-blue-300',
  AR: 'bg-orange-900 text-orange-300',
  BOWL: 'bg-green-900 text-green-300',
}

type SelectionStatus = 'none' | 'selected' | 'captain' | 'vice_captain'

interface PlayerCardProps {
  matchPlayer: MatchPlayer
  status: SelectionStatus
  onToggleSelect: (playerId: string) => void
  onSetCaptain: (playerId: string) => void
  onSetVC: (playerId: string) => void
  disabled?: boolean
}

export default function PlayerCard({
  matchPlayer,
  status,
  onToggleSelect,
  onSetCaptain,
  onSetVC,
  disabled = false,
}: PlayerCardProps) {
  const { player, credit_value, team_name } = matchPlayer
  const roleStyle = ROLE_COLORS[player.role] ?? 'bg-gray-700 text-gray-300'

  const isSelected = status !== 'none'
  const isCaptain = status === 'captain'
  const isVC = status === 'vice_captain'

  return (
    <div
      className={`relative rounded-xl border p-3 transition-all ${
        isCaptain
          ? 'border-gold-400 bg-gold-400/10'
          : isVC
          ? 'border-teal-400 bg-teal-400/10'
          : isSelected
          ? 'border-teal-500 bg-navy-700'
          : 'border-navy-600 bg-navy-800 hover:border-navy-500'
      } ${disabled && !isSelected ? 'opacity-50' : ''}`}
    >
      {/* Captain / VC badge */}
      {(isCaptain || isVC) && (
        <span className={`absolute top-1 right-1 text-xs font-bold px-1.5 py-0.5 rounded ${
          isCaptain ? 'bg-gold-400 text-navy-900' : 'bg-teal-400 text-navy-900'
        }`}>
          {isCaptain ? 'C' : 'VC'}
        </span>
      )}

      {/* Main click area — select/deselect */}
      <button
        onClick={() => !disabled && onToggleSelect(player.id)}
        className="w-full text-left"
        disabled={disabled && !isSelected}
      >
        <div className="font-medium text-white text-sm truncate pr-6">{player.name}</div>
        <div className="flex items-center gap-1 mt-1">
          <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${roleStyle}`}>
            {player.role}
          </span>
          <span className="text-xs text-gray-400">{team_name}</span>
        </div>
        <div className="text-xs text-teal-400 mt-1">{parseFloat(credit_value)} cr</div>
      </button>

      {/* C / VC buttons — only show when selected */}
      {isSelected && (
        <div className="mt-2 flex gap-1.5">
          <button
            onClick={() => onSetCaptain(player.id)}
            className={`flex-1 text-xs py-1 rounded font-semibold transition-colors ${
              isCaptain
                ? 'bg-gold-400 text-navy-900'
                : 'bg-navy-700 hover:bg-gold-400/20 text-gray-300 hover:text-gold-400 border border-navy-600 hover:border-gold-400/50'
            }`}
          >
            C
          </button>
          <button
            onClick={() => onSetVC(player.id)}
            className={`flex-1 text-xs py-1 rounded font-semibold transition-colors ${
              isVC
                ? 'bg-teal-400 text-navy-900'
                : 'bg-navy-700 hover:bg-teal-400/20 text-gray-300 hover:text-teal-400 border border-navy-600 hover:border-teal-400/50'
            }`}
          >
            VC
          </button>
        </div>
      )}
    </div>
  )
}

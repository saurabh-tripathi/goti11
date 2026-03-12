import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMatch } from '../../api/matches'
import { listMatchTeams } from '../../api/teams'
import { syncSquad, syncScore, finalizeMatch, overrideScore, getMatchScores } from '../../api/admin'
import type { Match, Team, PlayerScore } from '../../types'
import StatusBadge from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'

function ActionButton({
  label,
  onClick,
  loading,
  variant = 'default',
  confirm,
}: {
  label: string
  onClick: () => void
  loading?: boolean
  variant?: 'default' | 'danger' | 'success'
  confirm?: string
}) {
  const handleClick = () => {
    if (confirm && !window.confirm(confirm)) return
    onClick()
  }
  const colors = {
    default: 'bg-navy-700 hover:bg-navy-600 text-white',
    danger: 'bg-red-700 hover:bg-red-600 text-white',
    success: 'bg-teal-600 hover:bg-teal-500 text-white',
  }
  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 ${colors[variant]}`}
    >
      {loading ? '…' : label}
    </button>
  )
}

export default function AdminMatchDetailPage() {
  const { matchId } = useParams<{ matchId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [actionMsg, setActionMsg] = useState('')
  const [overrides, setOverrides] = useState<Record<string, string>>({})

  const { data: match, isLoading: matchLoading } = useQuery<Match>({
    queryKey: ['match', matchId],
    queryFn: () => getMatch(matchId!),
  })

  const { data: scores, isLoading: scoresLoading } = useQuery<PlayerScore[]>({
    queryKey: ['scores', matchId],
    queryFn: () => getMatchScores(matchId!),
    retry: false,
  })

  const { data: teams } = useQuery<Team[]>({
    queryKey: ['teams', matchId],
    queryFn: () => listMatchTeams(matchId!),
    retry: false,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['match', matchId] })
    qc.invalidateQueries({ queryKey: ['scores', matchId] })
    qc.invalidateQueries({ queryKey: ['teams', matchId] })
  }

  const syncSquadMut = useMutation({
    mutationFn: () => syncSquad(matchId!),
    onSuccess: (d) => { setActionMsg(d.message); invalidate() },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setActionMsg(msg ?? 'Sync squad failed')
    },
  })

  const syncScoreMut = useMutation({
    mutationFn: () => syncScore(matchId!),
    onSuccess: (d) => { setActionMsg(d.message); invalidate() },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setActionMsg(msg ?? 'Sync score failed')
    },
  })

  const finalizeMut = useMutation({
    mutationFn: () => finalizeMatch(matchId!),
    onSuccess: (d) => { setActionMsg(d.message); invalidate() },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setActionMsg(msg ?? 'Finalize failed')
    },
  })

  const overrideMut = useMutation({
    mutationFn: ({ playerId, pts }: { playerId: string; pts: number }) =>
      overrideScore(matchId!, playerId, pts),
    onSuccess: (d) => { setActionMsg(d.message); invalidate() },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setActionMsg(msg ?? 'Override failed')
    },
  })

  if (matchLoading) return <LoadingSpinner size="lg" />

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/admin')} className="text-gray-400 hover:text-white">
          ← Back
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-white">{match?.name}</h1>
          <p className="text-sm text-gray-400">{match?.team_a} vs {match?.team_b}</p>
        </div>
        {match && <StatusBadge status={match.status} />}
      </div>

      {/* Action message */}
      {actionMsg && (
        <div className="bg-teal-900/30 border border-teal-700 rounded-lg px-4 py-2 text-sm text-teal-300 flex justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg('')} className="text-gray-400 hover:text-white ml-4">✕</button>
        </div>
      )}

      {/* Action buttons */}
      <div className="bg-navy-800 border border-navy-700 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-gray-400 mb-3">Actions</h2>
        <div className="flex flex-wrap gap-3">
          <ActionButton
            label="Sync Squad"
            onClick={() => syncSquadMut.mutate()}
            loading={syncSquadMut.isPending}
            variant="default"
          />
          <ActionButton
            label="Sync Score"
            onClick={() => syncScoreMut.mutate()}
            loading={syncScoreMut.isPending}
            variant="default"
          />
          <ActionButton
            label="Finalize Match"
            onClick={() => finalizeMut.mutate()}
            loading={finalizeMut.isPending}
            variant="success"
            confirm="Finalize this match? This will compute prizes and lock the leaderboard."
          />
        </div>
      </div>

      {/* Score overrides */}
      <div className="bg-navy-800 border border-navy-700 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-gray-400 mb-3">Score Overrides</h2>
        {scoresLoading ? (
          <LoadingSpinner size="sm" />
        ) : scores && scores.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-navy-700">
                  <th className="text-left py-2 px-3">Player</th>
                  <th className="text-right py-2 px-3">Raw Pts</th>
                  <th className="text-right py-2 px-3">Override</th>
                  <th className="text-right py-2 px-3">Effective</th>
                  <th className="py-2 px-3"></th>
                </tr>
              </thead>
              <tbody>
                {scores.map((s) => (
                  <tr key={s.player_id} className="border-b border-navy-700/50">
                    <td className="py-2 px-3 text-white">
                      {s.player_name}
                      <span className="ml-1 text-xs text-gray-500">{s.role}</span>
                    </td>
                    <td className="py-2 px-3 text-right text-gray-300 font-mono">
                      {parseFloat(s.raw_points).toFixed(1)}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <input
                        type="number"
                        step="0.5"
                        value={overrides[s.player_id] ?? (s.override_points ?? '')}
                        onChange={(e) => setOverrides({ ...overrides, [s.player_id]: e.target.value })}
                        className="w-20 bg-navy-700 border border-navy-600 rounded px-2 py-1 text-sm text-white text-right focus:outline-none focus:border-teal-500"
                        placeholder="—"
                      />
                    </td>
                    <td className="py-2 px-3 text-right text-teal-400 font-mono">
                      {parseFloat(s.effective_points).toFixed(1)}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={() => {
                          const val = overrides[s.player_id]
                          if (val === undefined || val === '') return
                          overrideMut.mutate({ playerId: s.player_id, pts: parseFloat(val) })
                        }}
                        disabled={overrideMut.isPending}
                        className="text-xs px-2 py-1 bg-teal-700 hover:bg-teal-600 text-white rounded"
                      >
                        Apply
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No scores yet. Sync score first.</p>
        )}
      </div>

      {/* All teams */}
      <div className="bg-navy-800 border border-navy-700 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-gray-400 mb-3">
          All Teams ({teams?.length ?? 0})
        </h2>
        {teams && teams.length > 0 ? (
          <div className="space-y-3">
            {teams.map((team) => (
              <div key={team.id} className="bg-navy-700 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-white font-medium">
                    Team #{team.id.slice(-6)}
                  </span>
                  <span className="text-xs text-teal-400">
                    {parseFloat(team.total_points).toFixed(1)} pts
                    {team.rank && ` · Rank #${team.rank}`}
                  </span>
                </div>
                <div className="text-xs text-gray-400">
                  C: {team.players.find((p) => p.is_captain)?.name ?? '?'} ·{' '}
                  VC: {team.players.find((p) => p.is_vice_captain)?.name ?? '?'}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No teams submitted yet.</p>
        )}
      </div>
    </div>
  )
}

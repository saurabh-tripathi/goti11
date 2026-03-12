import { useState, useMemo, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMatch } from '../api/matches'
import { getSquad } from '../api/matches'
import { getMyTeam, createOrUpdateTeam } from '../api/teams'
import type { Match, MatchPlayer } from '../types'
import PlayerCard from '../components/team/PlayerCard'
import RoleFilterBar, { type RoleFilter } from '../components/team/RoleFilterBar'
import TeamSummaryBar from '../components/team/TeamSummaryBar'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import StatusBadge from '../components/common/StatusBadge'

const MAX_CREDITS = 100

// Map backend role strings to filter keys
function roleToFilter(role: string): RoleFilter {
  const r = role.toUpperCase()
  if (r.includes('WK') || r.includes('KEEPER')) return 'WK'
  if (r === 'BAT' || r === 'BATTER' || r === 'BATSMAN') return 'BAT'
  if (r === 'AR' || r === 'ALL' || r.includes('ALLROUNDER') || r.includes('ALL-ROUNDER')) return 'AR'
  if (r === 'BOWL' || r === 'BOWLER') return 'BOWL'
  return 'BAT'
}

type SelectionStatus = 'none' | 'selected' | 'captain' | 'vice_captain'

export default function TeamSelectionPage() {
  const { matchId } = useParams<{ matchId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: match } = useQuery<Match>({
    queryKey: ['match', matchId],
    queryFn: () => getMatch(matchId!),
  })

  const { data: squad, isLoading: squadLoading, error: squadError } = useQuery<MatchPlayer[]>({
    queryKey: ['squad', matchId],
    queryFn: () => getSquad(matchId!),
  })

  const { data: existingTeam } = useQuery({
    queryKey: ['myTeam', matchId],
    queryFn: () => getMyTeam(matchId!),
    retry: false,
  })

  // Player selection state: map playerId → status
  const [selection, setSelection] = useState<Map<string, SelectionStatus>>(new Map())
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('ALL')
  const [submitError, setSubmitError] = useState('')

  // Pre-populate from existing team
  useEffect(() => {
    if (!existingTeam) return
    const map = new Map<string, SelectionStatus>()
    existingTeam.players.forEach((p) => {
      if (p.is_captain) map.set(p.player_id, 'captain')
      else if (p.is_vice_captain) map.set(p.player_id, 'vice_captain')
      else map.set(p.player_id, 'selected')
    })
    setSelection(map)
  }, [existingTeam])

  const mutation = useMutation({
    mutationFn: (payload: Parameters<typeof createOrUpdateTeam>[1]) =>
      createOrUpdateTeam(matchId!, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['myTeam', matchId] })
      navigate(`/matches/${matchId}/leaderboard`)
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setSubmitError(msg ?? 'Failed to save team')
    },
  })

  const isLocked = match
    ? !['upcoming', 'squad_synced'].includes(match.status) ||
      (!!match.lock_time && new Date(match.lock_time) <= new Date())
    : false

  const selectedPlayers = useMemo(
    () => Array.from(selection.entries()).filter(([, s]) => s !== 'none'),
    [selection]
  )

  const captainId = selectedPlayers.find(([, s]) => s === 'captain')?.[0]
  const vcId = selectedPlayers.find(([, s]) => s === 'vice_captain')?.[0]

  const creditsUsed = useMemo(() => {
    if (!squad) return 0
    return selectedPlayers.reduce((sum, [id]) => {
      const mp = squad.find((p) => p.player_id === id)
      return sum + (mp ? parseFloat(mp.credit_value) : 0)
    }, 0)
  }, [selectedPlayers, squad])

  const filteredSquad = useMemo(() => {
    if (!squad) return []
    if (roleFilter === 'ALL') return squad
    return squad.filter((mp) => roleToFilter(mp.player.role) === roleFilter)
  }, [squad, roleFilter])

  const handleToggleSelect = (playerId: string) => {
    if (isLocked) return
    setSelection((prev) => {
      const next = new Map(prev)
      const current = next.get(playerId) ?? 'none'
      if (current !== 'none') {
        next.delete(playerId)
      } else {
        const count = Array.from(next.values()).filter((s) => s !== 'none').length
        if (count >= 11) return prev // max 11
        next.set(playerId, 'selected')
      }
      return next
    })
  }

  const handleSetCaptain = (playerId: string) => {
    if (isLocked) return
    setSelection((prev) => {
      const next = new Map(prev)
      const current = next.get(playerId)
      if (!current || current === 'none') return prev

      if (current === 'captain') {
        // Toggle off
        next.set(playerId, 'selected')
        return next
      }

      // Demote existing captain
      for (const [id, s] of next) {
        if (s === 'captain') next.set(id, 'selected')
      }
      // If this player was VC, clear that too — can't be both
      next.set(playerId, 'captain')
      return next
    })
  }

  const handleSetVC = (playerId: string) => {
    if (isLocked) return
    setSelection((prev) => {
      const next = new Map(prev)
      const current = next.get(playerId)
      if (!current || current === 'none') return prev

      if (current === 'vice_captain') {
        // Toggle off
        next.set(playerId, 'selected')
        return next
      }

      // Demote existing VC
      for (const [id, s] of next) {
        if (s === 'vice_captain') next.set(id, 'selected')
      }
      // If this player was captain, clear that too — can't be both
      next.set(playerId, 'vice_captain')
      return next
    })
  }

  const handleSubmit = () => {
    setSubmitError('')
    if (selectedPlayers.length !== 11) return
    if (!captainId || !vcId) return

    mutation.mutate({
      player_ids: selectedPlayers.map(([id]) => id),
      captain_id: captainId,
      vice_captain_id: vcId,
    })
  }

  if (squadLoading) return <LoadingSpinner size="lg" />
  if (squadError) return <ErrorMessage message="Failed to load squad" />

  return (
    <div className="pb-24">
      {/* Match header */}
      {match && (
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-white">{match.name}</h1>
            <p className="text-sm text-gray-400">{match.team_a} vs {match.team_b}</p>
          </div>
          <StatusBadge status={match.status} />
        </div>
      )}

      {isLocked && (
        <div className="mb-4 bg-yellow-900/30 border border-yellow-700 rounded-lg px-4 py-3 text-sm text-yellow-300">
          Team selection is locked for this match
        </div>
      )}

      {submitError && (
        <div className="mb-4 bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-sm text-red-300">
          {submitError}
        </div>
      )}

      {/* Role filter */}
      <div className="mb-4">
        <RoleFilterBar active={roleFilter} onChange={setRoleFilter} />
      </div>

      {/* Player grid */}
      {filteredSquad.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>No players found. Admin needs to sync squad first.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {filteredSquad.map((mp) => {
            const status = selection.get(mp.player_id) ?? 'none'
            const atMax = selectedPlayers.length >= 11 && status === 'none'
            return (
              <PlayerCard
                key={mp.player_id}
                matchPlayer={mp}
                status={status}
                onToggleSelect={handleToggleSelect}
                onSetCaptain={handleSetCaptain}
                onSetVC={handleSetVC}
                disabled={isLocked || atMax}
              />
            )
          })}
        </div>
      )}

      <TeamSummaryBar
        selectedCount={selectedPlayers.length}
        creditsUsed={creditsUsed}
        maxCredits={MAX_CREDITS}
        hasCaptain={!!captainId}
        hasVC={!!vcId}
        onSubmit={handleSubmit}
        isLoading={mutation.isPending}
        isLocked={isLocked}
      />
    </div>
  )
}

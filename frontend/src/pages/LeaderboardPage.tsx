import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMatch } from '../api/matches'
import { matchLeaderboard, seriesLeaderboard, myHistory } from '../api/leaderboard'
import { getMyTeam, listMatchTeams } from '../api/teams'
import type { Match, LeaderboardEntry, SeriesLeaderboardEntry, UserMatchHistory, Team } from '../types'
import LeaderboardTable from '../components/leaderboard/LeaderboardTable'
import TeamDetailModal from '../components/leaderboard/TeamDetailModal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import StatusBadge from '../components/common/StatusBadge'
import { useAuth } from '../context/AuthContext'

type Tab = 'match' | 'series' | 'history'

function SeriesLeaderboardTable({ entries }: { entries: SeriesLeaderboardEntry[] }) {
  const { user } = useAuth()
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-navy-700">
            <th className="text-left py-2 px-3">#</th>
            <th className="text-left py-2 px-3">Player</th>
            <th className="text-right py-2 px-3">Matches</th>
            <th className="text-right py-2 px-3">Points</th>
            <th className="text-right py-2 px-3">Prize</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => {
            const isMe = entry.user_id === user?.id
            return (
              <tr
                key={entry.user_id}
                className={`border-b border-navy-700/50 ${
                  isMe ? 'bg-teal-500/10 font-semibold' : 'hover:bg-navy-700/30'
                }`}
              >
                <td className="py-2 px-3 text-gray-400">{entry.rank}</td>
                <td className="py-2 px-3">
                  <span className="text-white">{entry.username}</span>
                  {isMe && <span className="ml-1 text-teal-400 text-xs">(you)</span>}
                </td>
                <td className="py-2 px-3 text-right text-gray-300">{entry.matches_played}</td>
                <td className="py-2 px-3 text-right text-teal-400 font-mono">
                  {parseFloat(entry.fantasy_points).toFixed(1)}
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
              <td colSpan={5} className="text-center text-gray-500 py-8">No entries yet</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

function HistoryTable({ entries }: { entries: UserMatchHistory[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-navy-700">
            <th className="text-left py-2 px-3">Match</th>
            <th className="text-left py-2 px-3">Captain</th>
            <th className="text-left py-2 px-3">VC</th>
            <th className="text-right py-2 px-3">Rank</th>
            <th className="text-right py-2 px-3">Points</th>
            <th className="text-right py-2 px-3">Prize</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.match_id} className="border-b border-navy-700/50 hover:bg-navy-700/30">
              <td className="py-2 px-3 text-white">{entry.match_name}</td>
              <td className="py-2 px-3 text-gray-300">{entry.captain_name}</td>
              <td className="py-2 px-3 text-gray-300">{entry.vice_captain_name}</td>
              <td className="py-2 px-3 text-right text-gray-400">{entry.rank ?? '—'}</td>
              <td className="py-2 px-3 text-right text-teal-400 font-mono">
                {parseFloat(entry.total_points).toFixed(1)}
              </td>
              <td className="py-2 px-3 text-right text-gold-400 font-mono">
                {parseFloat(entry.prize_awarded) > 0
                  ? `₹${parseFloat(entry.prize_awarded).toLocaleString()}`
                  : '—'}
              </td>
            </tr>
          ))}
          {entries.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center text-gray-500 py-8">No history yet</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default function LeaderboardPage() {
  const { matchId } = useParams<{ matchId: string }>()
  const { user, isAdmin } = useAuth()
  const [tab, setTab] = useState<Tab>('match')
  const [selectedEntry, setSelectedEntry] = useState<LeaderboardEntry | null>(null)

  const { data: match } = useQuery<Match>({
    queryKey: ['match', matchId],
    queryFn: () => getMatch(matchId!),
  })

  const { data: matchLb, isLoading: matchLbLoading } = useQuery<LeaderboardEntry[]>({
    queryKey: ['leaderboard', 'match', matchId],
    queryFn: () => matchLeaderboard(matchId!),
    enabled: tab === 'match',
  })

  const { data: seriesLb, isLoading: seriesLbLoading } = useQuery<SeriesLeaderboardEntry[]>({
    queryKey: ['leaderboard', 'series', match?.series_id],
    queryFn: () => seriesLeaderboard(match!.series_id),
    enabled: tab === 'series' && !!match?.series_id,
  })

  const { data: history, isLoading: historyLoading } = useQuery<UserMatchHistory[]>({
    queryKey: ['leaderboard', 'history', match?.series_id],
    queryFn: () => myHistory(match!.series_id),
    enabled: tab === 'history' && !!match?.series_id,
  })

  // Admin: fetch all teams so any row is viewable
  const { data: allTeams } = useQuery<Team[]>({
    queryKey: ['teams', matchId],
    queryFn: () => listMatchTeams(matchId!),
    enabled: isAdmin && tab === 'match',
    retry: false,
  })

  // Current user's own team (for non-admin clicking their own row)
  const { data: myTeam, isLoading: myTeamLoading } = useQuery<Team>({
    queryKey: ['myTeam', matchId],
    queryFn: () => getMyTeam(matchId!),
    enabled: !!selectedEntry && selectedEntry.user_id === user?.id && !isAdmin,
    retry: false,
  })

  // Which team to show in the modal
  const teamForModal: Team | null | undefined = selectedEntry
    ? isAdmin
      ? (allTeams?.find((t) => t.user_id === selectedEntry.user_id) ?? null)
      : myTeam ?? null
    : null

  // Which rows are clickable
  const clickableUserIds: Set<string> | undefined = isAdmin && allTeams
    ? new Set(allTeams.map((t) => t.user_id))
    : user
      ? new Set([user.id])
      : undefined

  return (
    <div>
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

      {/* Tabs */}
      <div className="flex gap-1 border-b border-navy-700 mb-4">
        {(['match', 'series', 'history'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === t
                ? 'text-teal-400 border-b-2 border-teal-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {t === 'history' ? 'My History' : t === 'series' ? 'Series' : 'Match'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="bg-navy-800 border border-navy-700 rounded-xl overflow-hidden">
        {tab === 'match' && (
          matchLbLoading ? <LoadingSpinner /> :
          <LeaderboardTable
            entries={matchLb ?? []}
            onRowClick={setSelectedEntry}
            clickableUserIds={clickableUserIds}
          />
        )}
        {tab === 'series' && (
          seriesLbLoading ? <LoadingSpinner /> :
          <SeriesLeaderboardTable entries={seriesLb ?? []} />
        )}
        {tab === 'history' && (
          historyLoading ? <LoadingSpinner /> :
          <HistoryTable entries={history ?? []} />
        )}
      </div>

      {/* Team detail modal */}
      {selectedEntry && (
        <TeamDetailModal
          username={selectedEntry.username}
          team={teamForModal ?? null}
          isLoading={!isAdmin && myTeamLoading}
          onClose={() => setSelectedEntry(null)}
        />
      )}
    </div>
  )
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listSeries } from '../api/series'
import { listMatches } from '../api/matches'
import type { Series, Match } from '../types'
import MatchCard from '../components/match/MatchCard'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import StatusBadge from '../components/common/StatusBadge'

function SeriesAccordion({ series }: { series: Series }) {
  const [open, setOpen] = useState(true)

  const { data: matches, isLoading } = useQuery<Match[]>({
    queryKey: ['matches', series.id],
    queryFn: () => listMatches(series.id),
    enabled: open,
  })

  return (
    <div className="bg-navy-800 border border-navy-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-navy-700/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="font-semibold text-white">{series.name}</span>
          <StatusBadge status={series.status} />
        </div>
        <div className="flex items-center gap-3">
          {parseFloat(series.prize_pool) > 0 && (
            <span className="text-xs text-gold-400">
              ₹{parseFloat(series.prize_pool).toLocaleString()} pool
            </span>
          )}
          <span className="text-gray-400 text-sm">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-navy-700">
          {isLoading ? (
            <LoadingSpinner />
          ) : matches && matches.length > 0 ? (
            matches.map((match) => <MatchCard key={match.id} match={match} />)
          ) : (
            <p className="text-center text-gray-500 py-4 text-sm">No matches in this series</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function MatchListPage() {
  const { data: seriesList, isLoading, error } = useQuery<Series[]>({
    queryKey: ['series'],
    queryFn: listSeries,
  })

  if (isLoading) return <LoadingSpinner size="lg" />
  if (error) return <ErrorMessage message="Failed to load series" />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">Matches</h1>

      {seriesList && seriesList.length > 0 ? (
        seriesList.map((s) => <SeriesAccordion key={s.id} series={s} />)
      ) : (
        <div className="text-center py-16 text-gray-500">
          <p className="text-4xl mb-3">🏏</p>
          <p>No series available yet</p>
        </div>
      )}
    </div>
  )
}

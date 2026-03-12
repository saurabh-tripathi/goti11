import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listMatches, createMatch } from '../../api/matches'
import { listSeries } from '../../api/series'
import type { Match, Series, MatchCreate } from '../../types'
import StatusBadge from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'

function CreateMatchModal({
  series,
  onClose,
}: {
  series: Series[]
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState<MatchCreate>({
    series_id: series[0]?.id ?? '',
    name: '',
    team_a: '',
    team_b: '',
    cricapi_match_id: '',
    scheduled_at: '',
    lock_time: '',
    prize_pool: '0',
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: createMatch,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['matches'] })
      onClose()
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Failed to create match')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: MatchCreate = {
      ...form,
      cricapi_match_id: form.cricapi_match_id || undefined,
      scheduled_at: form.scheduled_at || undefined,
      lock_time: form.lock_time || undefined,
    }
    mutation.mutate(payload)
  }

  const field = (key: keyof MatchCreate, label: string, type = 'text', required = false) => (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      <input
        type={type}
        value={(form[key] as string) ?? ''}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        required={required}
        className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
      />
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-bold text-white mb-4">Create Match</h2>

        {error && (
          <div className="mb-3 text-sm text-red-400 bg-red-900/30 border border-red-800 rounded px-3 py-2">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Series</label>
            <select
              value={form.series_id}
              onChange={(e) => setForm({ ...form, series_id: e.target.value })}
              className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
              required
            >
              {series.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          {field('name', 'Match Name', 'text', true)}
          {field('team_a', 'Team A', 'text', true)}
          {field('team_b', 'Team B', 'text', true)}
          {field('cricapi_match_id', 'Cricapi Match ID')}
          {field('scheduled_at', 'Scheduled At', 'datetime-local')}
          {field('lock_time', 'Lock Time', 'datetime-local')}
          {field('prize_pool', 'Prize Pool (₹)', 'number')}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 rounded-lg bg-navy-700 text-gray-300 hover:bg-navy-600 text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex-1 py-2 rounded-lg bg-teal-500 text-white font-semibold text-sm hover:bg-teal-400 disabled:opacity-50"
            >
              {mutation.isPending ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function AdminMatchesPage() {
  const navigate = useNavigate()
  const [showModal, setShowModal] = useState(false)

  const { data: matches, isLoading } = useQuery<Match[]>({
    queryKey: ['matches'],
    queryFn: () => listMatches(),
  })

  const { data: series } = useQuery<Series[]>({
    queryKey: ['series'],
    queryFn: listSeries,
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin — Matches</h1>
          <div className="flex gap-3 mt-2">
            <button
              onClick={() => navigate('/admin/series')}
              className="text-sm text-teal-400 hover:text-teal-300"
            >
              Series →
            </button>
            <button
              onClick={() => navigate('/admin/users')}
              className="text-sm text-teal-400 hover:text-teal-300"
            >
              Users →
            </button>
          </div>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-teal-500 text-white rounded-lg text-sm font-semibold hover:bg-teal-400"
        >
          + Create Match
        </button>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="bg-navy-800 border border-navy-700 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-navy-700">
                <th className="text-left py-3 px-4">Match</th>
                <th className="text-left py-3 px-4">Teams</th>
                <th className="text-left py-3 px-4">Scheduled</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-right py-3 px-4">Prize</th>
              </tr>
            </thead>
            <tbody>
              {matches?.map((m) => (
                <tr
                  key={m.id}
                  onClick={() => navigate(`/admin/matches/${m.id}`)}
                  className="border-b border-navy-700/50 hover:bg-navy-700/50 cursor-pointer"
                >
                  <td className="py-3 px-4 text-white font-medium">{m.name}</td>
                  <td className="py-3 px-4 text-gray-300">{m.team_a} vs {m.team_b}</td>
                  <td className="py-3 px-4 text-gray-400 text-xs">
                    {m.scheduled_at ? new Date(m.scheduled_at).toLocaleString() : '—'}
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={m.status} />
                  </td>
                  <td className="py-3 px-4 text-right text-gold-400">
                    {parseFloat(m.prize_pool) > 0 ? `₹${parseFloat(m.prize_pool).toLocaleString()}` : '—'}
                  </td>
                </tr>
              ))}
              {!matches?.length && (
                <tr>
                  <td colSpan={5} className="text-center text-gray-500 py-8">No matches yet</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showModal && series && (
        <CreateMatchModal series={series} onClose={() => setShowModal(false)} />
      )}
    </div>
  )
}

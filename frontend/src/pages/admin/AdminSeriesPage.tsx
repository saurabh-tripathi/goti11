import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listSeries, createSeries, patchSeries } from '../../api/series'
import type { Series, SeriesCreate, SeriesPatch } from '../../types'
import StatusBadge from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'

const EMPTY_FORM: SeriesCreate = {
  name: '',
  cricapi_series_id: '',
  status: 'upcoming',
  start_date: '',
  end_date: '',
  prize_pool: '0',
}

function SeriesForm({
  initial,
  onSubmit,
  onCancel,
  loading,
  error,
}: {
  initial: SeriesCreate
  onSubmit: (data: SeriesCreate) => void
  onCancel: () => void
  loading: boolean
  error: string
}) {
  const [form, setForm] = useState<SeriesCreate>(initial)

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onSubmit(form) }}
      className="space-y-3"
    >
      {error && (
        <div className="text-sm text-red-400 bg-red-900/30 border border-red-800 rounded px-3 py-2">
          {error}
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="block text-xs text-gray-400 mb-1">Series Name *</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Status</label>
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
            className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
          >
            {['upcoming', 'active', 'finished'].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Prize Pool (₹)</label>
          <input
            type="number"
            value={form.prize_pool}
            onChange={(e) => setForm({ ...form, prize_pool: e.target.value })}
            className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Start Date</label>
          <input
            type="date"
            value={form.start_date ?? ''}
            onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">End Date</label>
          <input
            type="date"
            value={form.end_date ?? ''}
            onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-xs text-gray-400 mb-1">Cricapi Series ID</label>
          <input
            type="text"
            value={form.cricapi_series_id ?? ''}
            onChange={(e) => setForm({ ...form, cricapi_series_id: e.target.value })}
            className="w-full bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-500"
          />
        </div>
      </div>
      <div className="flex gap-3 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-2 rounded-lg bg-navy-700 text-gray-300 hover:bg-navy-600 text-sm"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="flex-1 py-2 rounded-lg bg-teal-500 text-white font-semibold text-sm hover:bg-teal-400 disabled:opacity-50"
        >
          {loading ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  )
}

export default function AdminSeriesPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [formError, setFormError] = useState('')

  const { data: seriesList, isLoading } = useQuery<Series[]>({
    queryKey: ['series'],
    queryFn: listSeries,
  })

  const createMut = useMutation({
    mutationFn: createSeries,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['series'] })
      setShowCreate(false)
      setFormError('')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setFormError(msg ?? 'Failed to create series')
    },
  })

  const patchMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: SeriesPatch }) => patchSeries(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['series'] })
      setEditId(null)
      setFormError('')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setFormError(msg ?? 'Failed to update series')
    },
  })

  if (isLoading) return <LoadingSpinner size="lg" />

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Admin — Series</h1>
        <button
          onClick={() => { setShowCreate(true); setEditId(null) }}
          className="px-4 py-2 bg-teal-500 text-white rounded-lg text-sm font-semibold hover:bg-teal-400"
        >
          + Create Series
        </button>
      </div>

      {showCreate && (
        <div className="bg-navy-800 border border-teal-700 rounded-xl p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">New Series</h2>
          <SeriesForm
            initial={EMPTY_FORM}
            onSubmit={(data) => createMut.mutate(data)}
            onCancel={() => { setShowCreate(false); setFormError('') }}
            loading={createMut.isPending}
            error={formError}
          />
        </div>
      )}

      <div className="space-y-3">
        {seriesList?.map((s) => (
          <div key={s.id} className="bg-navy-800 border border-navy-700 rounded-xl p-4">
            {editId === s.id ? (
              <>
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Edit: {s.name}</h3>
                <SeriesForm
                  initial={{
                    name: s.name,
                    cricapi_series_id: s.cricapi_series_id ?? '',
                    status: s.status,
                    start_date: s.start_date ?? '',
                    end_date: s.end_date ?? '',
                    prize_pool: s.prize_pool,
                  }}
                  onSubmit={(data) => patchMut.mutate({ id: s.id, data })}
                  onCancel={() => { setEditId(null); setFormError('') }}
                  loading={patchMut.isPending}
                  error={formError}
                />
              </>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{s.name}</span>
                    <StatusBadge status={s.status} />
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {s.start_date ?? '?'} → {s.end_date ?? '?'}
                    {parseFloat(s.prize_pool) > 0 && (
                      <span className="ml-2 text-gold-400">
                        ₹{parseFloat(s.prize_pool).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => { setEditId(s.id); setShowCreate(false) }}
                  className="text-xs px-3 py-1 bg-navy-700 hover:bg-navy-600 text-gray-300 rounded-lg"
                >
                  Edit
                </button>
              </div>
            )}
          </div>
        ))}
        {!seriesList?.length && !showCreate && (
          <p className="text-center text-gray-500 py-8">No series yet</p>
        )}
      </div>
    </div>
  )
}

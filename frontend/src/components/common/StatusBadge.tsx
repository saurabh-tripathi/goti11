const STATUS_STYLES: Record<string, string> = {
  upcoming: 'bg-blue-900 text-blue-300',
  squad_synced: 'bg-teal-900 text-teal-300',
  locked: 'bg-yellow-900 text-yellow-300',
  scoring: 'bg-orange-900 text-orange-300',
  completed: 'bg-green-900 text-green-300',
  cancelled: 'bg-gray-700 text-gray-400',
  active: 'bg-teal-900 text-teal-300',
  finished: 'bg-green-900 text-green-300',
}

export default function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status.toLowerCase()] ?? 'bg-gray-700 text-gray-300'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide ${style}`}>
      {status.replace('_', ' ')}
    </span>
  )
}

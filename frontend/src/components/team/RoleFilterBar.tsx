export type RoleFilter = 'ALL' | 'WK' | 'BAT' | 'AR' | 'BOWL'

const ROLES: RoleFilter[] = ['ALL', 'WK', 'BAT', 'AR', 'BOWL']

export default function RoleFilterBar({
  active,
  onChange,
}: {
  active: RoleFilter
  onChange: (r: RoleFilter) => void
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {ROLES.map((role) => (
        <button
          key={role}
          onClick={() => onChange(role)}
          className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
            active === role
              ? 'bg-teal-500 text-white'
              : 'bg-navy-700 text-gray-300 hover:bg-navy-600'
          }`}
        >
          {role}
        </button>
      ))}
    </div>
  )
}

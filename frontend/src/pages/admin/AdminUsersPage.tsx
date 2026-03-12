import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listUsers, patchUser } from '../../api/admin'
import type { User } from '../../types'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import { useAuth } from '../../context/AuthContext'

export default function AdminUsersPage() {
  const { user: me } = useAuth()
  const qc = useQueryClient()

  const { data: users, isLoading } = useQuery<User[]>({
    queryKey: ['admin-users'],
    queryFn: listUsers,
  })

  const mutation = useMutation({
    mutationFn: ({ userId, patch }: { userId: string; patch: { is_active?: boolean; is_admin?: boolean } }) =>
      patchUser(userId, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-users'] }),
  })

  if (isLoading) return <LoadingSpinner size="lg" />

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Admin — Users</h1>

      <div className="bg-navy-800 border border-navy-700 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-navy-700">
              <th className="text-left py-3 px-4">Username</th>
              <th className="text-left py-3 px-4">Email</th>
              <th className="text-right py-3 px-4">Prize Pts</th>
              <th className="text-center py-3 px-4">Active</th>
              <th className="text-center py-3 px-4">Admin</th>
            </tr>
          </thead>
          <tbody>
            {users?.map((u) => {
              const isMe = u.id === me?.id
              return (
                <tr key={u.id} className={`border-b border-navy-700/50 ${isMe ? 'bg-teal-500/5' : ''}`}>
                  <td className="py-3 px-4 text-white">
                    {u.username}
                    {isMe && <span className="ml-1 text-xs text-teal-400">(you)</span>}
                  </td>
                  <td className="py-3 px-4 text-gray-400">{u.email}</td>
                  <td className="py-3 px-4 text-right text-teal-400">{u.prize_points}</td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => mutation.mutate({ userId: u.id, patch: { is_active: !u.is_active } })}
                      disabled={isMe}
                      className={`px-2 py-0.5 rounded text-xs font-semibold transition-colors ${
                        u.is_active
                          ? 'bg-green-800 text-green-300 hover:bg-red-800 hover:text-red-300'
                          : 'bg-red-800 text-red-300 hover:bg-green-800 hover:text-green-300'
                      } disabled:opacity-50`}
                    >
                      {u.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => mutation.mutate({ userId: u.id, patch: { is_admin: !u.is_admin } })}
                      disabled={isMe}
                      className={`px-2 py-0.5 rounded text-xs font-semibold transition-colors ${
                        u.is_admin
                          ? 'bg-purple-800 text-purple-300 hover:bg-navy-600 hover:text-gray-400'
                          : 'bg-navy-700 text-gray-400 hover:bg-purple-800 hover:text-purple-300'
                      } disabled:opacity-50`}
                    >
                      {u.is_admin ? 'Admin' : 'User'}
                    </button>
                  </td>
                </tr>
              )
            })}
            {!users?.length && (
              <tr>
                <td colSpan={5} className="text-center text-gray-500 py-8">No users found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

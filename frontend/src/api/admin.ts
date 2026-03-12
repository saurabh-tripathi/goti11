import client from './client'
import type { User, PlayerScore } from '../types'

export const listUsers = async (): Promise<User[]> => {
  const { data } = await client.get<User[]>('/admin/users')
  return data
}

export const patchUser = async (userId: string, body: { is_active?: boolean; is_admin?: boolean }): Promise<User> => {
  const { data } = await client.patch<User>(`/admin/users/${userId}`, body)
  return data
}

export const syncSquad = async (matchId: string): Promise<{ message: string }> => {
  const { data } = await client.post(`/matches/${matchId}/sync-squad`)
  return data
}

export const syncScore = async (matchId: string): Promise<{ message: string }> => {
  const { data } = await client.post(`/matches/${matchId}/sync-score`)
  return data
}

export const finalizeMatch = async (matchId: string): Promise<{ message: string }> => {
  const { data } = await client.post(`/matches/${matchId}/finalize`)
  return data
}

export const overrideScore = async (
  matchId: string,
  playerId: string,
  overridePoints: number
): Promise<{ message: string }> => {
  const { data } = await client.patch<{ message: string }>(`/matches/${matchId}/override-score`, {
    player_id: playerId,
    override_points: overridePoints,
  })
  return data
}

export const getMatchScores = async (matchId: string): Promise<PlayerScore[]> => {
  const { data } = await client.get<PlayerScore[]>(`/matches/${matchId}/scores`)
  return data
}

export const getCricapiMatches = async (): Promise<Record<string, unknown>[]> => {
  const { data } = await client.get('/admin/cricapi/matches')
  return data
}

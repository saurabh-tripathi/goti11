import client from './client'
import type { Team, TeamCreate } from '../types'

export const getMyTeam = async (matchId: string): Promise<Team> => {
  const { data } = await client.get<Team>(`/matches/${matchId}/my-team`)
  return data
}

export const createOrUpdateTeam = async (matchId: string, body: TeamCreate): Promise<Team> => {
  const { data } = await client.post<Team>(`/matches/${matchId}/my-team`, body)
  return data
}

export const listMatchTeams = async (matchId: string): Promise<Team[]> => {
  const { data } = await client.get<Team[]>(`/matches/${matchId}/teams`)
  return data
}

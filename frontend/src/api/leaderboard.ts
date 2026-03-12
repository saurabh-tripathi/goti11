import client from './client'
import type { LeaderboardEntry, SeriesLeaderboardEntry, UserMatchHistory } from '../types'

export const matchLeaderboard = async (matchId: string): Promise<LeaderboardEntry[]> => {
  const { data } = await client.get<LeaderboardEntry[]>(`/matches/${matchId}/leaderboard`)
  return data
}

export const seriesLeaderboard = async (seriesId: string): Promise<SeriesLeaderboardEntry[]> => {
  const { data } = await client.get<SeriesLeaderboardEntry[]>(`/series/${seriesId}/leaderboard`)
  return data
}

export const myHistory = async (seriesId: string): Promise<UserMatchHistory[]> => {
  const { data } = await client.get<UserMatchHistory[]>(`/series/${seriesId}/my-history`)
  return data
}

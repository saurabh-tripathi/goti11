import client from './client'
import type { Match, MatchCreate, MatchPatch, MatchPlayer } from '../types'

export const listMatches = async (seriesId?: string): Promise<Match[]> => {
  const { data } = await client.get<Match[]>('/matches', {
    params: seriesId ? { series_id: seriesId } : undefined,
  })
  return data
}

export const getMatch = async (matchId: string): Promise<Match> => {
  const { data } = await client.get<Match>(`/matches/${matchId}`)
  return data
}

export const getSquad = async (matchId: string): Promise<MatchPlayer[]> => {
  const { data } = await client.get<MatchPlayer[]>(`/matches/${matchId}/squad`)
  return data
}

export const createMatch = async (body: MatchCreate): Promise<Match> => {
  const { data } = await client.post<Match>('/matches', body)
  return data
}

export const patchMatch = async (matchId: string, body: MatchPatch): Promise<Match> => {
  const { data } = await client.patch<Match>(`/matches/${matchId}`, body)
  return data
}

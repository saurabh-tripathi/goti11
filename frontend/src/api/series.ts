import client from './client'
import type { Series, SeriesCreate, SeriesPatch } from '../types'

export const listSeries = async (): Promise<Series[]> => {
  const { data } = await client.get<Series[]>('/series')
  return data
}

export const getSeries = async (id: string): Promise<Series> => {
  const { data } = await client.get<Series>(`/series/${id}`)
  return data
}

export const createSeries = async (body: SeriesCreate): Promise<Series> => {
  const { data } = await client.post<Series>('/series', body)
  return data
}

export const patchSeries = async (id: string, body: SeriesPatch): Promise<Series> => {
  const { data } = await client.patch<Series>(`/series/${id}`, body)
  return data
}

import client from './client'
import type { TokenResponse, User } from '../types'

export const login = async (username: string, password: string): Promise<TokenResponse> => {
  const { data } = await client.post<TokenResponse>('/auth/login', { username, password })
  return data
}

export const register = async (username: string, email: string, password: string): Promise<User> => {
  const { data } = await client.post<User>('/auth/register', { username, email, password })
  return data
}

export const refresh = async (refreshToken: string): Promise<TokenResponse> => {
  const { data } = await client.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
  return data
}

export const getMe = async (): Promise<User> => {
  const { data } = await client.get<User>('/auth/me')
  return data
}

import { apiRequest, clearStoredToken, storeToken } from './client'
import type {
  AccessTokenResponse,
  LoginRequest,
  RegisterRequest,
  UserPublic,
} from '../types/api'

export async function registerUser(payload: RegisterRequest): Promise<UserPublic> {
  return apiRequest<UserPublic>('/api/auth/register', {
    method: 'POST',
    json: payload,
    token: null,
  })
}

export async function loginUser(payload: LoginRequest): Promise<AccessTokenResponse> {
  const response = await apiRequest<AccessTokenResponse>('/api/auth/login', {
    method: 'POST',
    json: payload,
    token: null,
  })
  storeToken(response.access_token)
  return response
}

export function logoutUser(): void {
  clearStoredToken()
}

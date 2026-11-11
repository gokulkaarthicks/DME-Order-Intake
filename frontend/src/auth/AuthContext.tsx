import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { loginUser, logoutUser, registerUser } from '../api/auth'
import { clearStoredToken, getStoredToken, setUnauthorizedHandler } from '../api/client'
import type { LoginRequest, RegisterRequest } from '../types/api'

interface AuthContextValue {
  isAuthenticated: boolean
  login: (payload: LoginRequest) => Promise<void>
  register: (payload: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken())

  const logout = useCallback(() => {
    logoutUser()
    setToken(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setToken(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(token),
      async login(payload) {
        const response = await loginUser(payload)
        setToken(response.access_token)
      },
      async register(payload) {
        await registerUser(payload)
      },
      logout,
    }),
    [logout, token],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export function clearAuthSession(): void {
  clearStoredToken()
}

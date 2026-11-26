import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { TOKEN_STORAGE_KEY } from '../services/api'
import { authService } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(localStorage.getItem(TOKEN_STORAGE_KEY)))

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const activeToken = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!activeToken) {
      setUser(null)
      setLoading(false)
      return null
    }
    try {
      const me = await authService.getMe()
      setUser(me)
      return me
    } catch {
      logout()
      return null
    } finally {
      setLoading(false)
    }
  }, [logout])

  useEffect(() => {
    if (token) {
      refreshUser()
    } else {
      setLoading(false)
    }
  }, [token, refreshUser])

  const login = async (email, password) => {
    const data = await authService.login(email, password)
    localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loading,
        isAuthenticated: Boolean(token && user),
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

import { create } from 'zustand'
import api from '@/shared/lib/api'
import type { LoginResponse, User } from '@/shared/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: JSON.parse(localStorage.getItem('cotia_user') || 'null'),
  token: localStorage.getItem('cotia_token'),
  isAuthenticated: !!localStorage.getItem('cotia_token'),
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.post<LoginResponse>('/auth/login', { email, password })
      localStorage.setItem('cotia_token', data.access_token)

      const { data: userData } = await api.get<User>('/auth/me')
      localStorage.setItem('cotia_user', JSON.stringify(userData))

      set({
        user: userData,
        token: data.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: { message?: string } } } }
      const message = err.response?.data?.detail?.message || 'Error al iniciar sesión'
      set({ isLoading: false, error: message, isAuthenticated: false })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('cotia_token')
    localStorage.removeItem('cotia_user')
    set({ user: null, token: null, isAuthenticated: false, error: null })
  },

  clearError: () => set({ error: null }),
}))

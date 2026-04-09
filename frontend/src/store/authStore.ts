import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User, AuthState } from '../types'

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user: User, token: string) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'auth-store' }
  )
)
import { create } from 'zustand'

type Theme = 'light' | 'dark'

interface UIState {
  theme: Theme
  toggleTheme: () => void
}

const storedTheme = (localStorage.getItem('cotia_theme') as Theme) || 'light'
document.documentElement.classList.toggle('dark', storedTheme === 'dark')

export const useUIStore = create<UIState>((set, get) => ({
  theme: storedTheme,

  toggleTheme: () => {
    const next: Theme = get().theme === 'dark' ? 'light' : 'dark'
    localStorage.setItem('cotia_theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
    set({ theme: next })
  },
}))

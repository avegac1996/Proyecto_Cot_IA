import { Moon, Sun } from 'lucide-react'
import { useUIStore } from '@/shared/store/uiStore'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useUIStore()

  return (
    <button
      onClick={toggleTheme}
      title={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      className="flex items-center gap-2 px-3.5 py-2.5 rounded-lg text-sm font-semibold transition-all w-full"
      style={{
        color: 'var(--color-text)',
        backgroundColor: 'var(--color-bg)',
        border: '1px solid var(--color-border)',
      }}
    >
      {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      <span>{theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}</span>
    </button>
  )
}

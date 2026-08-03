import { LogOut, UserCircle } from 'lucide-react'
import { useAuthStore } from '@/shared/store/authStore'

export default function UserMenu() {
  const { user, logout } = useAuthStore()

  return (
    <div className="flex items-center justify-between gap-2 px-3.5 py-2.5 rounded-lg" style={{ backgroundColor: 'var(--color-bg)' }}>
      <div className="flex items-center gap-2 min-w-0">
        <UserCircle className="w-5 h-5 shrink-0" style={{ color: 'var(--color-text-muted)' }} />
        <div className="min-w-0 leading-tight">
          <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text)' }}>
            {user?.username}
          </p>
          <p className="text-xs capitalize" style={{ color: 'var(--color-text-muted)' }}>
            {user?.rol}
          </p>
        </div>
      </div>
      <button
        onClick={logout}
        title="Cerrar sesión"
        className="p-1.5 rounded-lg transition-colors shrink-0"
        style={{ color: 'var(--color-danger)' }}
      >
        <LogOut className="w-4 h-4" />
      </button>
    </div>
  )
}

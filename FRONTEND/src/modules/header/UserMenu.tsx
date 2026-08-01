import { LogOut, UserCircle } from 'lucide-react'
import { useAuthStore } from '@/shared/store/authStore'

export default function UserMenu() {
  const { user, logout } = useAuthStore()

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <UserCircle className="w-6 h-6" style={{ color: 'var(--color-text-muted)' }} />
        <div className="hidden sm:block leading-tight">
          <p className="text-sm font-medium" style={{ color: 'var(--color-text)' }}>
            {user?.username}
          </p>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            {user?.rol}
          </p>
        </div>
      </div>
      <button
        onClick={logout}
        title="Cerrar sesión"
        className="p-2 rounded-lg transition-colors"
        style={{ color: 'var(--color-danger)' }}
      >
        <LogOut className="w-5 h-5" />
      </button>
    </div>
  )
}

import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/shared/store/authStore'

export default function HomePage() {
  const { user, isAuthenticated, logout } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--color-bg)' }}>
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4" style={{ color: 'var(--color-text)' }}>
          Bienvenido, {user?.username}
        </h1>
        <p className="mb-2" style={{ color: 'var(--color-text-muted)' }}>
          Rol: <span className="font-medium">{user?.rol}</span>
        </p>
        <p className="mb-8" style={{ color: 'var(--color-text-muted)' }}>
          El sistema está en construcción. Próximamente: carga de archivos, preguntas, cotización e historial.
        </p>
        <button
          onClick={logout}
          className="px-6 py-2.5 rounded-lg font-medium text-white transition-colors"
          style={{ backgroundColor: 'var(--color-danger)' }}
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}

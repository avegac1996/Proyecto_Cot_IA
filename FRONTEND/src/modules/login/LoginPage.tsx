import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, Mail, Loader2, AlertCircle, ShieldCheck, User } from 'lucide-react'
import { useAuthStore } from '@/shared/store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      navigate('/')
    } catch {
      // error is set in store
    }
  }

  const handleQuickLogin = async (quickEmail: string, quickPassword: string) => {
    try {
      await login(quickEmail, quickPassword)
      navigate('/')
    } catch {
      // error is set in store
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ backgroundColor: 'var(--color-bg)' }}>
      <div
        className="w-full max-w-md"
        style={{
          backgroundColor: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: '32px',
        }}
      >
        {/* Header */}
        <div className="text-center mb-8">
          <span
            className="inline-block text-xs font-bold uppercase tracking-wider px-2 py-1 rounded mb-3"
            style={{ backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)' }}
          >
            AV Electronics
          </span>
          <img
            src="/logo.png"
            alt="AV Electronics"
            className="h-16 w-auto object-contain mx-auto mb-3"
          />
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>
            Iniciar Sesión
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
            Sistema Inteligente de Cotización
          </p>
        </div>

          {/* Error */}
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border p-3 text-sm"
              style={{
                borderColor: 'var(--color-danger)',
                backgroundColor: 'rgba(220, 38, 38, 0.1)',
                color: 'var(--color-danger)',
              }}>
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text)' }}>
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5"
                  style={{ color: 'var(--color-text-muted)' }} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); clearError() }}
                  required
                  disabled={isLoading}
                  placeholder="admin@cotia.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border outline-none transition-colors text-sm"
                  style={{
                    borderColor: 'var(--color-border)',
                    backgroundColor: 'var(--color-bg)',
                    color: 'var(--color-text)',
                  }}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text)' }}>
                Contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5"
                  style={{ color: 'var(--color-text-muted)' }} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); clearError() }}
                  required
                  disabled={isLoading}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border outline-none transition-colors text-sm"
                  style={{
                    borderColor: 'var(--color-border)',
                    backgroundColor: 'var(--color-bg)',
                    color: 'var(--color-text)',
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded-lg font-medium text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              style={{ backgroundColor: 'var(--color-primary)' }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Iniciando sesión...
                </>
              ) : (
                'Iniciar sesión'
              )}
            </button>
          </form>

          {/* Quick login (solo para pruebas) */}
          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={() => handleQuickLogin('admin@cotia.com', 'Admin123!')}
              disabled={isLoading}
              className="flex-1 py-2.5 rounded-lg font-medium text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 border"
              style={{
                borderColor: 'var(--color-primary)',
                color: 'var(--color-primary)',
                backgroundColor: 'transparent',
              }}
            >
              <ShieldCheck className="w-4 h-4" />
              Admin
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('user@cotia.com', 'User123!')}
              disabled={isLoading}
              className="flex-1 py-2.5 rounded-lg font-medium text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 border"
              style={{
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-muted)',
                backgroundColor: 'transparent',
              }}
            >
              <User className="w-4 h-4" />
              User
            </button>
          </div>

          {/* Default credentials hint */}
          <div className="mt-6 pt-6 border-t text-xs space-y-1"
            style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}>
            <p className="font-medium">Credenciales por defecto:</p>
            <p>Admin: admin@cotia.com / Admin123!</p>
            <p>User: user@cotia.com / User123!</p>
          </div>
      </div>
    </div>
  )
}

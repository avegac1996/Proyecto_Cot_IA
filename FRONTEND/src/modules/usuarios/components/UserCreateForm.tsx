import { useState } from 'react'
import { Loader2, UserPlus, AlertCircle } from 'lucide-react'
import { createUsuario, extractErrorMessage } from '../services/usuariosService'

interface Props {
  onCreated: () => void
}

export default function UserCreateForm({ onCreated }: Props) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rol, setRol] = useState<'admin' | 'user'>('user')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)
    try {
      await createUsuario({ username, email, password, rol })
      setSuccess(`Usuario "${username}" creado correctamente`)
      setUsername('')
      setEmail('')
      setPassword('')
      setRol('user')
      onCreated()
    } catch (err) {
      setError(extractErrorMessage(err, 'Error al crear el usuario'))
    } finally {
      setIsLoading(false)
    }
  }

  const inputStyle = {
    borderColor: 'var(--color-border)',
    backgroundColor: 'var(--color-bg)',
    color: 'var(--color-text)',
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border p-6 space-y-4"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <h3 className="text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--color-text)' }}>
        <UserPlus className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
        Crear usuario
      </h3>

      {error && (
        <div
          className="flex items-center gap-2 rounded-lg border p-3 text-sm"
          style={{ borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }}
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="rounded-lg border p-3 text-sm" style={{ borderColor: '#16a34a', color: '#16a34a' }}>
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text)' }}>
            Usuario
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
            disabled={isLoading}
            placeholder="vendedor1"
            className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm"
            style={inputStyle}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text)' }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
            placeholder="vendedor1@cotia.com"
            className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm"
            style={inputStyle}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text)' }}>
            Contraseña
          </label>
          <input
            type="text"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            disabled={isLoading}
            placeholder="Vendedor123!"
            className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm"
            style={inputStyle}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text)' }}>
            Rol
          </label>
          <select
            value={rol}
            onChange={(e) => setRol(e.target.value as 'admin' | 'user')}
            disabled={isLoading}
            className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm"
            style={inputStyle}
          >
            <option value="user">user</option>
            <option value="admin">admin</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="px-5 py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
        style={{ backgroundColor: 'var(--color-primary)' }}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
        Crear usuario
      </button>
    </form>
  )
}

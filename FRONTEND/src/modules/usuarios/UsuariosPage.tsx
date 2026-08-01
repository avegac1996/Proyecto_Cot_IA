import { useCallback, useEffect, useState } from 'react'
import { AlertCircle, Loader2, Users } from 'lucide-react'
import type { User } from '@/shared/types'
import {
  extractErrorMessage,
  listUsuarios,
  toggleActiveUsuario,
} from './services/usuariosService'
import UserCreateForm from './components/UserCreateForm'
import UserList from './components/UserList'

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const fetchUsuarios = useCallback(async () => {
    try {
      const data = await listUsuarios()
      setUsuarios(data.usuarios)
      setError(null)
    } catch (err) {
      setError(extractErrorMessage(err, 'Error al cargar los usuarios'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUsuarios()
  }, [fetchUsuarios])

  const handleToggleActive = async (id: number) => {
    setTogglingId(id)
    try {
      const result = await toggleActiveUsuario(id)
      setUsuarios((prev) =>
        prev.map((u) => (u.id === id ? { ...u, activo: result.activo } : u))
      )
    } catch (err) {
      setError(extractErrorMessage(err, 'Error al cambiar el estado del usuario'))
    } finally {
      setTogglingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <Users className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Gestión de Usuarios
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Crea usuarios y actívalos o desactívalos según sea necesario
          </p>
        </div>
      </div>

      {error && (
        <div
          className="flex items-center gap-2 rounded-lg border p-3 text-sm"
          style={{ borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }}
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <UserCreateForm onCreated={fetchUsuarios} />

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
        </div>
      ) : (
        <UserList usuarios={usuarios} onToggleActive={handleToggleActive} togglingId={togglingId} />
      )}
    </div>
  )
}

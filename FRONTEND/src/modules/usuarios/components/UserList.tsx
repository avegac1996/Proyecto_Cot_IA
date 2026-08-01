import { UserCheck, UserX } from 'lucide-react'
import type { User } from '@/shared/types'
import { useAuthStore } from '@/shared/store/authStore'

interface Props {
  usuarios: User[]
  onToggleActive: (id: number) => void
  togglingId: number | null
}

export default function UserList({ usuarios, onToggleActive, togglingId }: Props) {
  const currentUser = useAuthStore((s) => s.user)

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ backgroundColor: 'var(--color-primary)' }}>
              <th className="text-left px-4 py-3 font-semibold text-white">Usuario</th>
              <th className="text-left px-4 py-3 font-semibold text-white">Email</th>
              <th className="text-left px-4 py-3 font-semibold text-white">Rol</th>
              <th className="text-left px-4 py-3 font-semibold text-white">Estado</th>
              <th className="text-right px-4 py-3 font-semibold text-white">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr
                key={u.id}
                className="border-t"
                style={{ borderColor: 'var(--color-border)' }}
              >
                <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-text)' }}>
                  {u.username}
                </td>
                <td className="px-4 py-3" style={{ color: 'var(--color-text-muted)' }}>
                  {u.email}
                </td>
                <td className="px-4 py-3">
                  <span
                    className="inline-block px-2 py-0.5 rounded text-xs font-medium"
                    style={{
                      backgroundColor: u.rol === 'admin' ? 'var(--color-primary)' : 'var(--color-bg)',
                      color: u.rol === 'admin' ? '#ffffff' : 'var(--color-text-muted)',
                    }}
                  >
                    {u.rol}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className="inline-block px-2 py-0.5 rounded text-xs font-medium"
                    style={{
                      backgroundColor: u.activo ? 'rgba(22,163,74,0.12)' : 'rgba(220,38,38,0.12)',
                      color: u.activo ? '#16a34a' : 'var(--color-danger)',
                    }}
                  >
                    {u.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onToggleActive(u.id)}
                    disabled={togglingId === u.id || u.id === currentUser?.id}
                    title={u.id === currentUser?.id ? 'No puedes desactivar tu propio usuario' : u.activo ? 'Desactivar' : 'Activar'}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      backgroundColor: u.activo ? 'rgba(220,38,38,0.12)' : 'rgba(22,163,74,0.12)',
                      color: u.activo ? 'var(--color-danger)' : '#16a34a',
                    }}
                  >
                    {u.activo ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                    {u.activo ? 'Desactivar' : 'Activar'}
                  </button>
                </td>
              </tr>
            ))}
            {usuarios.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
                  No hay usuarios registrados
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

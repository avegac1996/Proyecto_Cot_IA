import { useState } from 'react'
import { User, Mail, Phone, X, Loader2 } from 'lucide-react'

interface Props {
  onSubmit: (data: { nombre: string; correo: string; celular: string }) => void
  onCancel: () => void
  isLoading: boolean
}

export default function ClienteModal({ onSubmit, onCancel, isLoading }: Props) {
  const [nombre, setNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [celular, setCelular] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nombre.trim()) {
      setError('El nombre del cliente es obligatorio')
      return
    }
    onSubmit({ nombre: nombre.trim(), correo: correo.trim(), celular: celular.trim() })
  }

  const inputStyle = {
    backgroundColor: 'var(--color-bg)',
    border: '1px solid var(--color-border)',
    color: 'var(--color-text)',
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
      onClick={onCancel}
    >
      <div
        className="rounded-xl border max-w-md w-full"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="px-5 py-4 flex items-center justify-between border-b"
          style={{ borderColor: 'var(--color-border)' }}
        >
          <div className="flex items-center gap-2">
            <User className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
            <h3 className="font-bold" style={{ color: 'var(--color-text)' }}>
              Datos del Cliente
            </h3>
          </div>
          <button
            onClick={onCancel}
            className="p-1.5 rounded-lg"
            style={{ color: 'var(--color-text-muted)' }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 py-4 space-y-4">
          <div>
            <label className="text-xs font-medium block mb-1.5" style={{ color: 'var(--color-text-muted)' }}>
              Nombre *
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
              <input
                type="text"
                value={nombre}
                onChange={(e) => { setNombre(e.target.value); setError(null) }}
                placeholder="Nombre del cliente"
                className="w-full pl-9 pr-3 py-2 rounded-lg text-sm outline-none"
                style={inputStyle}
                autoFocus
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium block mb-1.5" style={{ color: 'var(--color-text-muted)' }}>
              Correo
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
              <input
                type="email"
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
                placeholder="correo@ejemplo.com"
                className="w-full pl-9 pr-3 py-2 rounded-lg text-sm outline-none"
                style={inputStyle}
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium block mb-1.5" style={{ color: 'var(--color-text-muted)' }}>
              Celular
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
              <input
                type="tel"
                value={celular}
                onChange={(e) => setCelular(e.target.value)}
                placeholder="0999 999 999"
                className="w-full pl-9 pr-3 py-2 rounded-lg text-sm outline-none"
                style={inputStyle}
              />
            </div>
          </div>

          {error && (
            <p className="text-xs" style={{ color: 'var(--color-danger)' }}>{error}</p>
          )}

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors"
              style={{
                border: '1px solid var(--color-border)',
                color: 'var(--color-text-muted)',
                backgroundColor: 'transparent',
              }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 py-2.5 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
              style={{ backgroundColor: 'var(--color-primary)' }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generando...
                </>
              ) : (
                'Generar cotización'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

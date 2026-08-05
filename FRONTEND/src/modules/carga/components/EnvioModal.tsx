import { useState, useEffect } from 'react'
import { Truck, X, Loader2, Check } from 'lucide-react'
import { getOpcionesEnvio } from '../services/busquedaService'
import type { OpcionEnvio } from '@/shared/types'

interface Props {
  onSubmit: (envio: OpcionEnvio | null) => void
  onCancel: () => void
  isLoading: boolean
}

export default function EnvioModal({ onSubmit, onCancel, isLoading }: Props) {
  const [opciones, setOpciones] = useState<OpcionEnvio[]>([])
  const [seleccionada, setSeleccionada] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    getOpcionesEnvio()
      .then((data) => {
        setOpciones(data)
        setCargando(false)
      })
      .catch(() => setCargando(false))
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const op = opciones.find((o) => o.id === seleccionada)
    onSubmit(op ?? null)
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
            <Truck className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
            <h3 className="font-bold" style={{ color: 'var(--color-text)' }}>
              Opción de Envío
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

        <form onSubmit={handleSubmit} className="px-5 py-4 space-y-3">
          {cargando ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin" style={{ color: 'var(--color-primary)' }} />
            </div>
          ) : (
            <>
              {opciones.map((op) => (
                <label
                  key={op.id}
                  className="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors"
                  style={{
                    borderColor: seleccionada === op.id ? 'var(--color-primary)' : 'var(--color-border)',
                    backgroundColor: seleccionada === op.id ? 'var(--color-bg)' : 'transparent',
                  }}
                >
                  <input
                    type="radio"
                    name="envio"
                    value={op.id}
                    checked={seleccionada === op.id}
                    onChange={(e) => setSeleccionada(e.target.value)}
                    className="w-4 h-4"
                    style={{ accentColor: 'var(--color-primary)' }}
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium" style={{ color: 'var(--color-text)' }}>
                      {op.nombre}
                    </div>
                  </div>
                  <span className="text-sm font-bold" style={{ color: 'var(--color-primary)' }}>
                    {op.precio === 0 ? 'Gratis' : `$${op.precio.toFixed(2)}`}
                  </span>
                </label>
              ))}
            </>
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
              disabled={!seleccionada || isLoading}
              className="flex-1 py-2.5 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
              style={{ backgroundColor: 'var(--color-primary)' }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generando...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Confirmar
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { AlertCircle, Eye, History, Loader2 } from 'lucide-react'
import type { CotizacionListItem } from '@/shared/types'
import { extractHistorialError, getHistorial } from './services/historialService'

const ESTADO_STYLE: Record<string, { bg: string; color: string }> = {
  completada: { bg: 'rgba(22,163,74,0.12)', color: '#16a34a' },
  pendiente: { bg: '#FEF3C7', color: '#B45309' },
  cancelada: { bg: 'rgba(220,38,38,0.12)', color: '#dc2626' },
}

export default function HistorialPage() {
  const [cotizaciones, setCotizaciones] = useState<CotizacionListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getHistorial()
      .then((data) => setCotizaciones(data.cotizaciones))
      .catch((err) => setError(extractHistorialError(err)))
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <History className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Historial de Cotizaciones
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Cotizaciones generadas anteriormente
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

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
        </div>
      ) : cotizaciones.length === 0 ? (
        <div
          className="rounded-xl border p-12 text-center"
          style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
        >
          <History className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--color-text-muted)' }} />
          <p className="font-medium" style={{ color: 'var(--color-text)' }}>
            Aún no hay cotizaciones
          </p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Las cotizaciones que generes aparecerán aquí
          </p>
        </div>
      ) : (
        <div
          className="rounded-xl border overflow-hidden"
          style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ backgroundColor: 'var(--color-primary)' }}>
                  <th className="text-left px-4 py-3 font-semibold text-white">#</th>
                  <th className="text-left px-4 py-3 font-semibold text-white">Fecha</th>
                  <th className="text-center px-4 py-3 font-semibold text-white">Ítems</th>
                  <th className="text-right px-4 py-3 font-semibold text-white">Total</th>
                  <th className="text-center px-4 py-3 font-semibold text-white">Estado</th>
                </tr>
              </thead>
              <tbody>
                {cotizaciones.map((c) => {
                  const estilo = ESTADO_STYLE[c.estado] ?? ESTADO_STYLE.pendiente
                  return (
                    <tr key={c.cotizacion_id} className="border-t" style={{ borderColor: 'var(--color-border)' }}>
                      <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-text)' }}>
                        <span className="inline-flex items-center gap-1.5">
                          <Eye className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
                          {c.cotizacion_id}
                        </span>
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--color-text-muted)' }}>
                        {new Date(c.fecha_creacion).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-center" style={{ color: 'var(--color-text)' }}>
                        {c.total_items}
                      </td>
                      <td className="px-4 py-3 text-right font-medium" style={{ color: 'var(--color-text)' }}>
                        ${Number(c.total).toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className="inline-block px-2 py-0.5 rounded text-xs font-medium capitalize"
                          style={{ backgroundColor: estilo.bg, color: estilo.color }}
                        >
                          {c.estado}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

import { useEffect, useState, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { AlertCircle, Eye, History, Loader2, Trash2, Download, X, FileText } from 'lucide-react'
import type { CotizacionListItem, Cotizacion } from '@/shared/types'
import {
  extractHistorialError,
  getHistorial,
  getCotizacionById,
  eliminarCotizacion,
  descargarPDF,
} from './services/historialService'

const ESTADO_STYLE: Record<string, { bg: string; color: string }> = {
  completada: { bg: 'rgba(22,163,74,0.12)', color: '#16a34a' },
  finalizada: { bg: 'rgba(22,163,74,0.12)', color: '#16a34a' },
  pendiente: { bg: '#FEF3C7', color: '#B45309' },
  cancelada: { bg: 'rgba(220,38,38,0.12)', color: '#dc2626' },
}

function money(value: string | number): string {
  return `$${Number(value).toFixed(2)}`
}

export default function HistorialPage() {
  const location = useLocation()
  const [cotizaciones, setCotizaciones] = useState<CotizacionListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cotizacionDetalle, setCotizacionDetalle] = useState<Cotizacion | null>(null)
  const [isLoadingDetalle, setIsLoadingDetalle] = useState(false)
  const [eliminandoId, setEliminandoId] = useState<number | null>(null)
  const [highlightId, setHighlightId] = useState<number | null>(null)

  const cargarHistorial = useCallback(() => {
    setIsLoading(true)
    getHistorial()
      .then((data) => setCotizaciones(data.cotizaciones))
      .catch((err) => setError(extractHistorialError(err)))
      .finally(() => setIsLoading(false))
  }, [])

  useEffect(() => {
    cargarHistorial()
  }, [cargarHistorial])

  useEffect(() => {
    const state = location.state as { cotizacionCreada?: number } | null
    if (state?.cotizacionCreada) {
      setHighlightId(state.cotizacionCreada)
      setTimeout(() => setHighlightId(null), 3000)
    }
  }, [location.state])

  const handleVer = async (cotizacionId: number) => {
    setIsLoadingDetalle(true)
    try {
      const data = await getCotizacionById(cotizacionId)
      setCotizacionDetalle(data)
    } catch {
      setError('Error al cargar el detalle de la cotización')
    } finally {
      setIsLoadingDetalle(false)
    }
  }

  const handleEliminar = async (cotizacionId: number) => {
    if (!confirm(`¿Eliminar la cotización #${cotizacionId}?`)) return
    setEliminandoId(cotizacionId)
    try {
      await eliminarCotizacion(cotizacionId)
      setCotizaciones((prev) => prev.filter((c) => c.cotizacion_id !== cotizacionId))
    } catch {
      setError('Error al eliminar la cotización')
    } finally {
      setEliminandoId(null)
    }
  }

  const handlePDF = async (cotizacionId: number) => {
    try {
      await descargarPDF(cotizacionId)
    } catch {
      setError('Error al descargar el PDF')
    }
  }

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
            Todas las cotizaciones generadas
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
          <button
            onClick={() => setError(null)}
            className="ml-auto p-0.5"
            style={{ color: 'var(--color-danger)' }}
          >
            <X className="w-3.5 h-3.5" />
          </button>
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
                  <th className="text-center px-4 py-3 font-semibold text-white">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {cotizaciones.map((c) => {
                  const estilo = ESTADO_STYLE[c.estado] ?? ESTADO_STYLE.pendiente
                  const isHighlighted = highlightId === c.cotizacion_id
                  return (
                    <tr
                      key={c.cotizacion_id}
                      className="border-t transition-colors"
                      style={{
                        borderColor: 'var(--color-border)',
                        backgroundColor: isHighlighted ? 'rgba(59,130,246,0.08)' : 'transparent',
                      }}
                    >
                      <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-text)' }}>
                        #{c.cotizacion_id}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--color-text-muted)' }}>
                        {new Date(c.fecha_creacion).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-center" style={{ color: 'var(--color-text)' }}>
                        {c.total_items}
                      </td>
                      <td className="px-4 py-3 text-right font-medium" style={{ color: 'var(--color-text)' }}>
                        {money(c.total)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className="inline-block px-2 py-0.5 rounded text-xs font-medium capitalize"
                          style={{ backgroundColor: estilo.bg, color: estilo.color }}
                        >
                          {c.estado}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => handleVer(c.cotizacion_id)}
                            className="p-1.5 rounded-lg transition-colors"
                            style={{ color: 'var(--color-primary)', backgroundColor: 'var(--color-bg)' }}
                            title="Ver detalle"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handlePDF(c.cotizacion_id)}
                            className="p-1.5 rounded-lg transition-colors"
                            style={{ color: 'var(--color-primary)', backgroundColor: 'var(--color-bg)' }}
                            title="Descargar PDF"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleEliminar(c.cotizacion_id)}
                            disabled={eliminandoId === c.cotizacion_id}
                            className="p-1.5 rounded-lg transition-colors disabled:opacity-50"
                            style={{ color: 'var(--color-danger)', backgroundColor: 'var(--color-bg)' }}
                            title="Eliminar"
                          >
                            {eliminandoId === c.cotizacion_id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal de detalle */}
      {cotizacionDetalle && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          onClick={() => setCotizacionDetalle(null)}
        >
          <div
            className="rounded-xl border max-w-3xl w-full max-h-[80vh] overflow-y-auto"
            style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              className="px-5 py-4 flex items-center justify-between border-b sticky top-0"
              style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)' }}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
                <h3 className="font-bold" style={{ color: 'var(--color-text)' }}>
                  Cotización #{cotizacionDetalle.cotizacion_id}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePDF(cotizacionDetalle.cotizacion_id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white"
                  style={{ backgroundColor: 'var(--color-primary)' }}
                >
                  <Download className="w-3.5 h-3.5" />
                  PDF
                </button>
                <button
                  onClick={() => setCotizacionDetalle(null)}
                  className="p-1.5 rounded-lg"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="px-5 py-4">
              <div className="text-xs mb-4" style={{ color: 'var(--color-text-muted)' }}>
                {new Date(cotizacionDetalle.fecha_creacion).toLocaleString()} ·{' '}
                {cotizacionDetalle.items.length} ítem(s) ·{' '}
                <span className="capitalize">{cotizacionDetalle.estado}</span>
              </div>

              <table className="w-full text-sm">
                <thead>
                  <tr style={{ backgroundColor: 'var(--color-bg)' }}>
                    <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--color-text)' }}>Producto</th>
                    <th className="text-center px-3 py-2 font-medium" style={{ color: 'var(--color-text)' }}>Cant.</th>
                    <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--color-text)' }}>Proveedor</th>
                    <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--color-text)' }}>P. Unit.</th>
                    <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--color-text)' }}>Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {cotizacionDetalle.items.map((item) => (
                    <tr key={item.id} className="border-t" style={{ borderColor: 'var(--color-border)' }}>
                      <td className="px-3 py-2.5" style={{ color: 'var(--color-text)' }}>
                        {item.producto_nombre}
                        {!item.disponible && (
                          <span className="ml-1.5 text-xs" style={{ color: 'var(--color-danger)' }}>· Agotado</span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-center" style={{ color: 'var(--color-text-muted)' }}>
                        {item.cantidad}
                      </td>
                      <td className="px-3 py-2.5" style={{ color: 'var(--color-text-muted)' }}>
                        {item.proveedor}
                        {item.es_propio && (
                          <span className="ml-1 px-1 py-0.5 rounded text-xs" style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}>
                            AV
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-right" style={{ color: 'var(--color-text)' }}>
                        {money(item.precio_unitario)}
                      </td>
                      <td className="px-3 py-2.5 text-right font-medium" style={{ color: 'var(--color-text)' }}>
                        {money(item.subtotal)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2" style={{ borderColor: 'var(--color-border)' }}>
                    <td colSpan={4} className="px-3 py-3 text-right font-bold" style={{ color: 'var(--color-text)' }}>
                      Total
                    </td>
                    <td className="px-3 py-3 text-right font-bold text-base" style={{ color: 'var(--color-primary)' }}>
                      {money(cotizacionDetalle.total)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay para detalle */}
      {isLoadingDetalle && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ backgroundColor: 'rgba(0,0,0,0.3)' }}
        >
          <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
        </div>
      )}
    </div>
  )
}

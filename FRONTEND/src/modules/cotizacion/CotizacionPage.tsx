import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Download, FileText, FileSpreadsheet, Loader2 } from 'lucide-react'
import { useCotizacionStore } from '@/shared/store/cotizacionStore'
import CotizacionTable from './components/CotizacionTable'
import {
  descargarExcel,
  descargarPDF,
  extractCotizacionError,
  generarCotizacion,
  getCotizacion,
  isAmbiguitiesPending,
} from './services/cotizacionService'

export default function CotizacionPage() {
  const navigate = useNavigate()
  const { sessionId, cotizacion, setCotizacion } = useCotizacionStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId || cotizacion) return
    setIsLoading(true)
    getCotizacion(sessionId)
      .then(setCotizacion)
      .catch(() => {
        // Aún no existe cotización para esta sesión; el usuario la genera manualmente
      })
      .finally(() => setIsLoading(false))
  }, [sessionId, cotizacion, setCotizacion])

  const handleGenerar = async () => {
    if (!sessionId) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await generarCotizacion(sessionId)
      setCotizacion(data)
    } catch (err) {
      if (isAmbiguitiesPending(err)) {
        navigate('/preguntas')
        return
      }
      setError(extractCotizacionError(err))
    } finally {
      setIsLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div
        className="rounded-xl border p-12 text-center"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <FileText className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--color-text-muted)' }} />
        <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--color-text)' }}>
          No hay una sesión activa
        </h2>
        <p className="text-sm mb-6" style={{ color: 'var(--color-text-muted)' }}>
          Carga una lista de componentes para generar una cotización
        </p>
        <button
          onClick={() => navigate('/carga')}
          className="px-5 py-2.5 rounded-lg font-medium text-white text-sm"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          Ir a Carga
        </button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
      </div>
    )
  }

  if (!cotizacion) {
    return (
      <div
        className="rounded-xl border p-12 text-center"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <FileText className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--color-primary)' }} />
        <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--color-text)' }}>
          Lista lista para cotizar
        </h2>
        <p className="text-sm mb-6" style={{ color: 'var(--color-text-muted)' }}>
          Se buscarán precios y disponibilidad en las tiendas registradas
        </p>
        {error && (
          <div
            className="mb-4 flex items-center justify-center gap-2 text-sm"
            style={{ color: 'var(--color-danger)' }}
          >
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}
        <button
          onClick={handleGenerar}
          className="px-6 py-2.5 rounded-lg font-medium text-white text-sm"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          Generar cotización
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
              Cotización #{cotizacion.cotizacion_id}
            </h2>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
              {new Date(cotizacion.fecha_creacion).toLocaleString()} · {cotizacion.items.length} ítem(s)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => descargarPDF(cotizacion.cotizacion_id)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm text-white transition-opacity hover:opacity-90"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            <Download className="w-4 h-4" />
            PDF
          </button>
          <button
            onClick={() => descargarExcel(cotizacion.cotizacion_id)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors"
            style={{
              backgroundColor: 'transparent',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text)',
            }}
          >
            <FileSpreadsheet className="w-4 h-4" />
            Excel
          </button>
        </div>
      </div>

      <CotizacionTable cotizacion={cotizacion} />

      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
        Los ítems "Sin datos" no tienen precios disponibles en las tiendas consultadas.
      </p>
    </div>
  )
}

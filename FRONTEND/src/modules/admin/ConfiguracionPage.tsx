import { useState, useEffect } from 'react'
import { Settings, Save, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { getConfiguracion, actualizarMargen } from '@/modules/carga/services/busquedaService'

export default function ConfiguracionPage() {
  const [margen, setMargen] = useState<number>(5)
  const [margenOriginal, setMargenOriginal] = useState<number>(5)
  const [tiendaPropia, setTiendaPropia] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    cargarConfiguracion()
  }, [])

  const cargarConfiguracion = async () => {
    setIsLoading(true)
    try {
      const config = await getConfiguracion()
      setMargen(config.margen_competencia)
      setMargenOriginal(config.margen_competencia)
      setTiendaPropia(config.tienda_propia)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al cargar configuración')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGuardar = async () => {
    setIsSaving(true)
    setError(null)
    setSuccess(false)
    try {
      const config = await actualizarMargen(margen)
      setMargenOriginal(config.margen_competencia)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al guardar')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
      </div>
    )
  }

  const hayCambios = margen !== margenOriginal

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <Settings className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Configuración de Negocio
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Parámetros del sistema de cotización
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

      {success && (
        <div
          className="flex items-center gap-2 rounded-lg border p-3 text-sm"
          style={{ borderColor: '#D1FAE5', backgroundColor: '#F0FDF4', color: '#065F46' }}
        >
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>Configuración guardada correctamente</span>
        </div>
      )}

      <div
        className="rounded-xl border p-6 space-y-4"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
            Margen de competencia (%)
          </label>
          <p className="text-xs mb-3" style={{ color: 'var(--color-text-muted)' }}>
            Porcentaje aplicado a productos de tiendas externas. Los productos de {tiendaPropia} no incluyen margen.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={0}
              max={100}
              step={0.5}
              value={margen}
              onChange={(e) => setMargen(parseFloat(e.target.value) || 0)}
              disabled={isSaving}
              className="w-32 px-3 py-2.5 rounded-lg border outline-none text-sm"
              style={{
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
            />
            <span className="text-lg font-bold" style={{ color: 'var(--color-text-muted)' }}>%</span>
          </div>
        </div>

        <div
          className="rounded-lg p-3 text-xs"
          style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text-muted)' }}
        >
          <p className="font-medium mb-1" style={{ color: 'var(--color-text)' }}>Tienda propia:</p>
          <p>{tiendaPropia} — los productos de esta tienda se muestran sin margen.</p>
        </div>

        <button
          onClick={handleGuardar}
          disabled={!hayCambios || isSaving}
          className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Guardando...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Guardar cambios
            </>
          )}
        </button>
      </div>
    </div>
  )
}

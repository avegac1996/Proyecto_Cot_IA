import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Search, Loader2, AlertCircle, Send, Mic, Image as ImageIcon, FileText, Type, Info, ArrowLeft } from 'lucide-react'
import { buscarComponentes, crearCotizacionDesdeCarrito, getCotizacionById } from './services/busquedaService'
import TarjetaProducto from './components/TarjetaProducto'
import CarritoPreview from './components/CarritoPreview'
import VoiceInput from './components/VoiceInput'
import ImageInput from './components/ImageInput'
import FileInput from './components/FileInput'
import type { ResultadoComponente, OpcionProducto, ItemCarrito } from '@/shared/types'

export default function CargaPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [mensaje, setMensaje] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resultados, setResultados] = useState<ResultadoComponente[]>([])
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [metodoActivo, setMetodoActivo] = useState<'texto' | 'voz' | 'imagen' | 'archivo'>('texto')
  const resultadosRef = useRef<HTMLDivElement>(null)
  const editandoCotizacionId = (location.state as { cotizacionId?: number } | null)?.cotizacionId ?? null

  useEffect(() => {
    if (resultados.length > 0 && resultadosRef.current) {
      resultadosRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [resultados])

  useEffect(() => {
    if (editandoCotizacionId) {
      getCotizacionById(editandoCotizacionId).then((cot) => {
        const itemsExistentes: ItemCarrito[] = cot.items.map((item) => ({
          termino: `${item.producto_nombre} - ${item.proveedor}`,
          cantidad: item.cantidad,
          opcion_seleccionada: {
            tienda: item.proveedor,
            nombre_producto: item.producto_nombre,
            precio_base: parseFloat(item.precio_unitario),
            precio_con_margen: parseFloat(item.precio_unitario),
            margen_aplicado: parseFloat(item.margen_aplicado),
            disponible: item.disponible,
            url: null,
            es_propio: item.es_propio,
          },
        }))
        setCarrito(itemsExistentes)
      }).catch(() => {
        setError('No se pudo cargar la cotización existente')
      })
    }
  }, [editandoCotizacionId])

  const handleBuscar = async () => {
    await handleBuscarWith(mensaje)
  }

  const handleBuscarWith = async (texto: string) => {
    const trimmed = texto.trim()
    if (!trimmed) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await buscarComponentes(trimmed)
      setResultados(data.resultados)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al buscar componentes')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVoiceTranscript = (text: string) => {
    setMensaje((prev) => (prev ? prev + ' ' + text : text))
  }

  const handleToggleSeleccion = (termino: string, cantidad: number, opcion: OpcionProducto) => {
    const itemKey = `${termino} - ${opcion.tienda}`
    setCarrito((prev) => {
      const exists = prev.some(
        (item) =>
          item.termino === itemKey &&
          item.opcion_seleccionada.tienda === opcion.tienda &&
          item.opcion_seleccionada.nombre_producto === opcion.nombre_producto
      )
      if (exists) {
        return prev.filter(
          (item) =>
            !(item.termino === itemKey &&
              item.opcion_seleccionada.tienda === opcion.tienda &&
              item.opcion_seleccionada.nombre_producto === opcion.nombre_producto)
        )
      }
      return [...prev, { termino: itemKey, cantidad, opcion_seleccionada: opcion }]
    })
  }

  const handleQuitarCarrito = (index: number) => {
    setCarrito((prev) => prev.filter((_, i) => i !== index))
  }

  const handleCambiarCantidad = (index: number, cantidad: number) => {
    setCarrito((prev) => prev.map((item, i) => (i === index ? { ...item, cantidad } : item)))
  }

  const handleBuscarSugerencia = (sugerencia: string) => {
    setMensaje(sugerencia)
    handleBuscarWith(sugerencia)
  }

  const handleFinalizar = async () => {
    if (carrito.length === 0) return
    setIsLoading(true)
    setError(null)
    try {
      const cotizacion = await crearCotizacionDesdeCarrito(carrito, editandoCotizacionId ?? undefined)
      navigate('/historial', { state: { cotizacionCreada: cotizacion.cotizacion_id } })
    } catch (err) {
      const e = err as { response?: { data?: { detail?: unknown } }; message?: string }
      const detail = e.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: unknown) => typeof d === 'string' ? d : JSON.stringify(d)).join('; '))
      } else {
        setError(e.message || 'Error al crear cotización')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const metodos = [
    { id: 'texto' as const, label: 'Escribir', icon: Type },
    { id: 'voz' as const, label: 'Hablar', icon: Mic },
    { id: 'imagen' as const, label: 'Imagen', icon: ImageIcon },
    { id: 'archivo' as const, label: 'Archivo', icon: FileText },
  ]

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      {/* Header compacto */}
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <Search className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Cotizar Componentes
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Elige cómo quieres cargar tu lista
          </p>
        </div>
      </div>

      {editandoCotizacionId && (
        <div
          className="flex items-center gap-3 rounded-lg border p-3"
          style={{ borderColor: '#DBEAFE', backgroundColor: '#EFF6FF', color: '#1E40AF' }}
        >
          <ArrowLeft
            className="w-4 h-4 flex-shrink-0 cursor-pointer hover:opacity-70"
            onClick={() => navigate('/historial')}
          />
          <span className="text-sm font-medium">
            Editando cotización #{editandoCotizacionId} — los productos que agregues se sumarán a esta cotización
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna principal */}
        <div className="lg:col-span-2 space-y-4 order-1">
          {/* Selector de método de entrada */}
          <div className="flex gap-2">
            {metodos.map((metodo) => {
              const Icon = metodo.icon
              const activo = metodoActivo === metodo.id
              return (
                <button
                  key={metodo.id}
                  onClick={() => setMetodoActivo(metodo.id)}
                  className="flex-1 flex flex-col items-center gap-1 py-3 rounded-lg border transition-all"
                  style={{
                    backgroundColor: activo ? 'var(--color-primary)' : 'var(--color-surface)',
                    borderColor: activo ? 'var(--color-primary)' : 'var(--color-border)',
                    color: activo ? '#fff' : 'var(--color-text-muted)',
                  }}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-xs font-medium">{metodo.label}</span>
                </button>
              )
            })}
          </div>

          {/* Panel del método activo */}
          <div
            className="rounded-xl border p-4 space-y-3"
            style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
          >
            {/* Tab: Escribir */}
            {metodoActivo === 'texto' && (
              <>
                <textarea
                  value={mensaje}
                  onChange={(e) => setMensaje(e.target.value)}
                  disabled={isLoading}
                  rows={3}
                  placeholder="Ej: necesito cotizar un arduino y un sensor de temperatura"
                  className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm resize-y"
                  style={{
                    borderColor: 'var(--color-border)',
                    backgroundColor: 'var(--color-bg)',
                    color: 'var(--color-text)',
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleBuscar()
                    }
                  }}
                />
                <button
                  onClick={handleBuscar}
                  disabled={!mensaje.trim() || isLoading}
                  className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  style={{ backgroundColor: 'var(--color-primary)' }}
                >
                  {isLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                  ) : (
                    <><Send className="w-4 h-4" /> Buscar componentes</>
                  )}
                </button>
              </>
            )}

            {/* Tab: Voz */}
            {metodoActivo === 'voz' && (
              <>
                <p className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
                  Presiona el micrófono y habla. Tu voz se convertirá en texto.
                </p>
                <VoiceInput onTranscript={handleVoiceTranscript} onAutoSearch={(text) => { setMensaje(text); handleBuscarWith(text) }} disabled={isLoading} />
                {mensaje && (
                  <div
                    className="rounded-lg border p-3 text-sm"
                    style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                  >
                    {mensaje}
                  </div>
                )}
                <button
                  onClick={handleBuscar}
                  disabled={!mensaje.trim() || isLoading}
                  className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  style={{ backgroundColor: 'var(--color-primary)' }}
                >
                  {isLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                  ) : (
                    <><Send className="w-4 h-4" /> Buscar componentes</>
                  )}
                </button>
              </>
            )}

            {/* Tab: Imagen */}
            {metodoActivo === 'imagen' && (
              <>
                <p className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
                  Sube una foto de tu lista de componentes. Extraeremos el texto automáticamente.
                </p>
                <ImageInput onTextExtracted={handleVoiceTranscript} disabled={isLoading} />
                {mensaje && (
                  <button
                    onClick={handleBuscar}
                    disabled={isLoading}
                    className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{ backgroundColor: 'var(--color-primary)' }}
                  >
                    {isLoading ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                    ) : (
                      <><Send className="w-4 h-4" /> Buscar componentes</>
                    )}
                  </button>
                )}
              </>
            )}

            {/* Tab: Archivo */}
            {metodoActivo === 'archivo' && (
              <>
                <p className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
                  Sube un PDF, Word, Excel o TXT con tu lista de componentes.
                </p>
                <FileInput onTextExtracted={handleVoiceTranscript} disabled={isLoading} />
                {mensaje && (
                  <button
                    onClick={handleBuscar}
                    disabled={isLoading}
                    className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{ backgroundColor: 'var(--color-primary)' }}
                  >
                    {isLoading ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                    ) : (
                      <><Send className="w-4 h-4" /> Buscar componentes</>
                    )}
                  </button>
                )}
              </>
            )}
          </div>

          {/* Resultados de búsqueda */}
          {resultados.length > 0 && (
            <div ref={resultadosRef} className="space-y-3">
              <h3 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
                Resultados ({resultados.length} {resultados.length === 1 ? 'componente' : 'componentes'})
              </h3>
              <div className="max-h-[60vh] overflow-y-auto space-y-3 pr-1">
              {resultados.map((resultado, idx) => (
                <div key={`${resultado.termino}-${idx}`} className="space-y-2">
                  <TarjetaProducto
                    resultado={resultado}
                    onToggleSeleccion={handleToggleSeleccion}
                    seleccionadas={carrito
                      .filter((item) => item.termino.startsWith(`${resultado.termino} - `))
                      .map((item) => item.opcion_seleccionada)}
                    onBuscarSugerencia={handleBuscarSugerencia}
                  />
                </div>
              ))}
              </div>
            </div>
          )}

          {error && (
            <div
              className="flex items-center gap-2 rounded-lg border p-3 text-sm"
              style={{ borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Info compacta */}
          <div
            className="flex items-start gap-2 rounded-lg border p-3 text-xs"
            style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
          >
            <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>
              AV Electronics aparece primero sin margen. Otras tiendas incluyen margen configurable.
              Si un componente no se encuentra, te sugeriremos alternativas.
            </span>
          </div>
        </div>

        {/* Columna lateral: carrito */}
        <div className="lg:col-span-1 order-2">
          <div className="lg:sticky lg:top-4">
          <CarritoPreview
            items={carrito}
            onQuitar={handleQuitarCarrito}
            onCambiarCantidad={handleCambiarCantidad}
            onFinalizar={handleFinalizar}
            disabled={carrito.length === 0 || isLoading}
          />
          </div>
        </div>
      </div>
    </div>
  )
}

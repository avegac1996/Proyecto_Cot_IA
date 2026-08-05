import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Search, Loader2, AlertCircle, Send, Mic, Image as ImageIcon, FileText, Type, Info, ArrowLeft, Sparkles, RotateCw } from 'lucide-react'
import { buscarComponentes, crearCotizacionDesdeCarrito, getCotizacionById } from './services/busquedaService'
import TarjetaProducto from './components/TarjetaProducto'
import CarritoPreview from './components/CarritoPreview'
import VoiceInput from './components/VoiceInput'
import ImageInput from './components/ImageInput'
import FileInput from './components/FileInput'
import ClienteModal from './components/ClienteModal'
import EnvioModal from './components/EnvioModal'
import AgenteChat from './components/AgenteChat'
import type { ResultadoComponente, OpcionProducto, ItemCarrito, OpcionEnvio } from '@/shared/types'

export default function CargaPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [mensaje, setMensaje] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resultados, setResultados] = useState<ResultadoComponente[]>([])
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [metodoActivo, setMetodoActivo] = useState<'texto' | 'voz' | 'imagen' | 'archivo'>('texto')
  const [mostrarModalCliente, setMostrarModalCliente] = useState(false)
  const [mostrarModalEnvio, setMostrarModalEnvio] = useState(false)
  const [datosCliente, setDatosCliente] = useState<{ nombre: string; correo: string; celular: string } | null>(null)
  const [mostrarAgente, setMostrarAgente] = useState(false)
  const [busquedaRealizada, setBusquedaRealizada] = useState(false)
  const [terminoBusqueda, setTerminoBusqueda] = useState('')
  const [resetKey, setResetKey] = useState(0)
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
        // Guardar datos del cliente existentes para no volver a pedirlos
        if (cot.cliente_nombre || cot.cliente_correo || cot.cliente_celular) {
          setDatosCliente({
            nombre: cot.cliente_nombre || '',
            correo: cot.cliente_correo || '',
            celular: cot.cliente_celular || '',
          })
        }
      }).catch(() => {
        setError('No se pudo cargar la cotización existente')
      })
    }
  }, [editandoCotizacionId])

  const handleBuscar = async () => {
    await handleBuscarWith(mensaje)
  }

  const guardarHistorialBusqueda = (termino: string, numResultados: number) => {
    try {
      const key = 'historial_busquedas'
      const stored = localStorage.getItem(key)
      const historial: { termino: string; fecha: string; resultados: number }[] = stored ? JSON.parse(stored) : []
      historial.unshift({ termino, fecha: new Date().toISOString(), resultados: numResultados })
      const limitado = historial.slice(0, 20)
      localStorage.setItem(key, JSON.stringify(limitado))
    } catch {
      // localStorage no disponible, ignorar
    }
  }

  const handleRecargar = () => {
    setResultados([])
    setCarrito([])
    setBusquedaRealizada(false)
    setTerminoBusqueda('')
    setMensaje('')
    setError(null)
    setResetKey(k => k + 1)
  }

  const handleBuscarWith = async (texto: string) => {
    const trimmed = texto.trim()
    if (!trimmed) return
    setIsLoading(true)
    setError(null)
    setBusquedaRealizada(true)
    setTerminoBusqueda(trimmed)
    try {
      const data = await buscarComponentes(trimmed)
      setResultados(data.resultados)
      guardarHistorialBusqueda(trimmed, data.resultados.length)
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

  const handleFinalizar = async (cliente?: { nombre: string; correo: string; celular: string }, envio?: OpcionEnvio | null) => {
    if (carrito.length === 0) return
    setIsLoading(true)
    setError(null)
    try {
      const cotizacion = await crearCotizacionDesdeCarrito(carrito, editandoCotizacionId ?? undefined, cliente, envio)
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
      setMostrarModalCliente(false)
      setMostrarModalEnvio(false)
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
      <div className="flex items-center justify-between">
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
        {(busquedaRealizada || carrito.length > 0 || resultados.length > 0) && (
          <button
            onClick={handleRecargar}
            title="Limpiar todo"
            className="px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            style={{
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-muted)',
              backgroundColor: 'var(--color-surface)',
            }}
          >
            <RotateCw className="w-4 h-4" />
            Recargar
          </button>
        )}
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
                <div className="flex gap-2">
                  <button
                    onClick={handleBuscar}
                    disabled={!mensaje.trim() || isLoading}
                    className="flex-1 py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{ backgroundColor: 'var(--color-primary)' }}
                  >
                    {isLoading ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                    ) : (
                      <><Send className="w-4 h-4" /> Buscar componentes</>
                    )}
                  </button>
                  <button
                    onClick={() => setMostrarAgente((v) => !v)}
                    title="Preguntar al asistente IA"
                    className="px-3 py-2.5 rounded-lg transition-colors flex items-center justify-center"
                    style={{
                      border: '1px solid var(--color-border)',
                      backgroundColor: mostrarAgente ? 'var(--color-primary)' : 'var(--color-bg)',
                      color: mostrarAgente ? '#fff' : 'var(--color-text-muted)',
                    }}
                  >
                    <Sparkles className="w-4 h-4" />
                  </button>
                </div>
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
                <div className="flex gap-2">
                  <button
                    onClick={handleBuscar}
                    disabled={!mensaje.trim() || isLoading}
                    className="flex-1 py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{ backgroundColor: 'var(--color-primary)' }}
                  >
                    {isLoading ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                    ) : (
                      <><Send className="w-4 h-4" /> Buscar componentes</>
                    )}
                  </button>
                  <button
                    onClick={() => setMostrarAgente((v) => !v)}
                    title="Preguntar al asistente IA"
                    className="px-3 py-2.5 rounded-lg transition-colors flex items-center justify-center"
                    style={{
                      border: '1px solid var(--color-border)',
                      backgroundColor: mostrarAgente ? 'var(--color-primary)' : 'var(--color-bg)',
                      color: mostrarAgente ? '#fff' : 'var(--color-text-muted)',
                    }}
                  >
                    <Sparkles className="w-4 h-4" />
                  </button>
                </div>
              </>
            )}

            {/* Tab: Imagen */}
            {metodoActivo === 'imagen' && (
              <>
                <p className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
                  Sube una foto de tu lista de componentes. Extraeremos el texto automáticamente.
                </p>
                <ImageInput key={`img-${resetKey}`} onTextExtracted={handleVoiceTranscript} disabled={isLoading} />
                {mensaje && (
                  <div className="flex gap-2">
                    <button
                      onClick={handleBuscar}
                      disabled={isLoading}
                      className="flex-1 py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      style={{ backgroundColor: 'var(--color-primary)' }}
                    >
                      {isLoading ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                      ) : (
                        <><Send className="w-4 h-4" /> Buscar componentes</>
                      )}
                    </button>
                    <button
                      onClick={() => setMostrarAgente((v) => !v)}
                      title="Preguntar al asistente IA"
                      className="px-3 py-2.5 rounded-lg transition-colors flex items-center justify-center"
                      style={{
                        border: '1px solid var(--color-border)',
                        backgroundColor: mostrarAgente ? 'var(--color-primary)' : 'var(--color-bg)',
                        color: mostrarAgente ? '#fff' : 'var(--color-text-muted)',
                      }}
                    >
                      <Sparkles className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Tab: Archivo */}
            {metodoActivo === 'archivo' && (
              <>
                <p className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
                  Sube un PDF, Word, Excel o TXT con tu lista de componentes.
                </p>
                <FileInput key={`file-${resetKey}`} onTextExtracted={handleVoiceTranscript} disabled={isLoading} />
                {mensaje && (
                  <div className="flex gap-2">
                    <button
                      onClick={handleBuscar}
                      disabled={isLoading}
                      className="flex-1 py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      style={{ backgroundColor: 'var(--color-primary)' }}
                    >
                      {isLoading ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Buscando...</>
                      ) : (
                        <><Send className="w-4 h-4" /> Buscar componentes</>
                      )}
                    </button>
                    <button
                      onClick={() => setMostrarAgente((v) => !v)}
                      title="Preguntar al asistente IA"
                      className="px-3 py-2.5 rounded-lg transition-colors flex items-center justify-center"
                      style={{
                        border: '1px solid var(--color-border)',
                        backgroundColor: mostrarAgente ? 'var(--color-primary)' : 'var(--color-bg)',
                        color: mostrarAgente ? '#fff' : 'var(--color-text-muted)',
                      }}
                    >
                      <Sparkles className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Asistente IA desplegable */}
          {mostrarAgente && busquedaRealizada && (
            <AgenteChat resultados={resultados} terminoBusqueda={terminoBusqueda} />
          )}

          {/* Sin resultados */}
          {busquedaRealizada && resultados.length === 0 && !error && !isLoading && (
            <div
              className="rounded-lg border p-4 text-sm text-center"
              style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
            >
              No se encontraron resultados para "{terminoBusqueda}". Usa el asistente IA para reformular tu búsqueda.
            </div>
          )}

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
            onFinalizar={() => {
              if (editandoCotizacionId && datosCliente) {
                // Editando cotización existente: saltar modal de cliente, ir directo a envío
                setMostrarModalEnvio(true)
              } else {
                setMostrarModalCliente(true)
              }
            }}
            disabled={carrito.length === 0 || isLoading}
          />
          </div>
        </div>
      </div>

      {mostrarModalCliente && (
        <ClienteModal
          onSubmit={(data) => {
            setDatosCliente(data)
            setMostrarModalCliente(false)
            setMostrarModalEnvio(true)
          }}
          onCancel={() => setMostrarModalCliente(false)}
          isLoading={isLoading}
        />
      )}

      {mostrarModalEnvio && (
        <EnvioModal
          onSubmit={(envio) => handleFinalizar(datosCliente ?? undefined, envio)}
          onCancel={() => setMostrarModalEnvio(false)}
          isLoading={isLoading}
        />
      )}
    </div>
  )
}

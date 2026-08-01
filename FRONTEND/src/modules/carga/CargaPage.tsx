import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Loader2, AlertCircle, Sparkles, Info, Send } from 'lucide-react'
import { buscarComponentes } from './services/busquedaService'
import { extractUploadError, uploadFile } from './services/uploadService'
import { useCotizacionStore } from '@/shared/store/cotizacionStore'
import TarjetaProducto from './components/TarjetaProducto'
import CarritoPreview from './components/CarritoPreview'
import DropZone from './components/DropZone'
import FilePreview from './components/FilePreview'
import type { ResultadoComponente, OpcionProducto, ItemCarrito } from '@/shared/types'

export default function CargaPage() {
  const navigate = useNavigate()
  const setSesion = useCotizacionStore((s) => s.setSesion)
  const [mensaje, setMensaje] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resultados, setResultados] = useState<ResultadoComponente[]>([])
  const [selecciones, setSelecciones] = useState<Record<string, OpcionProducto | null>>({})
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [file, setFile] = useState<File | null>(null)
  const resultadosRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (resultados.length > 0 && resultadosRef.current) {
      resultadosRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [resultados])

  const handleBuscar = async () => {
    const texto = mensaje.trim()
    if (!texto) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await buscarComponentes(texto)
      setResultados(data.resultados)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al buscar componentes')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSeleccionar = (termino: string, _cantidad: number, opcion: OpcionProducto) => {
    setSelecciones((prev) => ({ ...prev, [termino]: opcion }))
  }

  const handleAgregarAlCarrito = (termino: string, cantidad: number, opcion: OpcionProducto) => {
    setCarrito((prev) => {
      const filtered = prev.filter((item) => item.termino !== termino)
      return [...filtered, { termino, cantidad, opcion_seleccionada: opcion }]
    })
    setSelecciones((prev) => ({ ...prev, [termino]: null }))
  }

  const handleQuitarCarrito = (index: number) => {
    setCarrito((prev) => prev.filter((_, i) => i !== index))
  }

  const handleFinalizar = async () => {
    if (carrito.length === 0) return
    setIsLoading(true)
    setError(null)
    try {
      const lineas = carrito.map(
        (item) => `${item.cantidad} ${item.opcion_seleccionada.nombre_producto}`
      )
      const contenido = lineas.join('\n')
      const data = await uploadFile(
        new File([contenido], 'carrito.txt', { type: 'text/plain' })
      )
      setSesion(data.session_id, data.componentes)
      navigate('/cotizacion')
    } catch (err) {
      setError(extractUploadError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await uploadFile(file)
      setSesion(data.session_id, data.componentes)
      navigate(data.ambiguedades_detectadas ? '/preguntas' : '/cotizacion')
    } catch (err) {
      setError(extractUploadError(err))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
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
            Escribe lo que necesitas o sube tu lista
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna principal: búsqueda + resultados */}
        <div className="lg:col-span-2 space-y-4">
          {/* Input de búsqueda conversacional */}
          <div
            className="rounded-xl border p-4 space-y-3"
            style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
          >
            <textarea
              value={mensaje}
              onChange={(e) => setMensaje(e.target.value)}
              disabled={isLoading}
              rows={3}
              placeholder="Ej: buenas, necesito cotizar un arduino y un sensor de temperatura"
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
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Buscando...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Buscar componentes
                </>
              )}
            </button>
          </div>

          {/* Resultados de búsqueda */}
          {resultados.length > 0 && (
            <div ref={resultadosRef} className="space-y-3">
              <h3 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
                Resultados ({resultados.length} {resultados.length === 1 ? 'componente' : 'componentes'})
              </h3>
              {resultados.map((resultado, idx) => (
                <div key={`${resultado.termino}-${idx}`} className="space-y-2">
                  <TarjetaProducto
                    resultado={resultado}
                    onSeleccionar={handleSeleccionar}
                    seleccionada={selecciones[resultado.termino] ?? null}
                  />
                  {selecciones[resultado.termino] && (
                    <button
                      onClick={() =>
                        handleAgregarAlCarrito(
                          resultado.termino,
                          resultado.cantidad,
                          selecciones[resultado.termino]!
                        )
                      }
                      className="w-full py-2 rounded-lg font-medium text-white text-xs transition-colors flex items-center justify-center gap-1"
                      style={{ backgroundColor: 'var(--color-primary)' }}
                    >
                      Agregar al carrito
                    </button>
                  )}
                </div>
              ))}
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

          {/* Separador + upload alternativo */}
          <div className="flex items-center gap-3 pt-2">
            <div className="flex-1 border-t" style={{ borderColor: 'var(--color-border)' }} />
            <span className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
              O sube un archivo
            </span>
            <div className="flex-1 border-t" style={{ borderColor: 'var(--color-border)' }} />
          </div>

          <DropZone onFileSelected={setFile} disabled={isLoading} />
          {file && <FilePreview file={file} onRemove={() => setFile(null)} />}
          {file && (
            <button
              onClick={handleUpload}
              disabled={isLoading}
              className="w-full py-2.5 rounded-lg font-medium text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 border"
              style={{
                borderColor: 'var(--color-primary)',
                color: 'var(--color-primary)',
                backgroundColor: 'transparent',
              }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Procesando...
                </>
              ) : (
                'Procesar archivo'
              )}
            </button>
          )}

          {/* Info de auto-completado */}
          <div
            className="rounded-xl border p-4 space-y-3"
            style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
          >
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
              <p className="text-xs font-bold" style={{ color: 'var(--color-text)' }}>
                Auto-completado inteligente
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
                Resistencias → 220Ω 1/4W
              </div>
              <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
                LEDs → 5mm rojo
              </div>
              <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
                Arduino → UNO R3
              </div>
              <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
                Fuente → 9V DC jack+
              </div>
            </div>
            <div
              className="flex items-start gap-2 pt-2 border-t text-xs"
              style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
            >
              <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span>
                AV Electronics (tienda propia) aparece primero sin margen. Otras tiendas incluyen margen configurable.
                Solo se preguntará sobre sensores, motores o componentes no reconocidos (máx. 2 preguntas).
              </span>
            </div>
          </div>
        </div>

        {/* Columna lateral: carrito */}
        <div className="lg:col-span-1">
          <CarritoPreview
            items={carrito}
            onQuitar={handleQuitarCarrito}
            onFinalizar={handleFinalizar}
            disabled={carrito.length === 0 || isLoading}
          />
        </div>
      </div>
    </div>
  )
}

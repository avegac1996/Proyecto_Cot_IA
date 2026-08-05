import { useEffect, useState, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { AlertCircle, Eye, History, Loader2, Trash2, Download, X, FileText, Lock, Plus, Search, ChevronLeft, ChevronRight, Calendar, Truck, UserCog } from 'lucide-react'
import type { CotizacionListItem, Cotizacion, OpcionEnvio } from '@/shared/types'
import {
  extractHistorialError,
  getHistorial,
  getCotizacionById,
  eliminarCotizacion,
  descargarPDF,
  finalizarCotizacion,
  actualizarEnvio,
  actualizarCliente,
} from './services/historialService'
import EnvioModal from '@/modules/carga/components/EnvioModal'

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
  const navigate = useNavigate()
  const location = useLocation()
  const [cotizaciones, setCotizaciones] = useState<CotizacionListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cotizacionDetalle, setCotizacionDetalle] = useState<Cotizacion | null>(null)
  const [isLoadingDetalle, setIsLoadingDetalle] = useState(false)
  const [eliminandoId, setEliminandoId] = useState<number | null>(null)
  const [highlightId, setHighlightId] = useState<number | null>(null)
  const [finalizando, setFinalizando] = useState(false)
  const [mostrarModalEnvio, setMostrarModalEnvio] = useState(false)
  const [guardandoEnvio, setGuardandoEnvio] = useState(false)
  const [editandoCliente, setEditandoCliente] = useState(false)
  const [guardandoCliente, setGuardandoCliente] = useState(false)
  const [clienteForm, setClienteForm] = useState({ nombre: '', correo: '', celular: '' })

  // Paginación y filtros
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const LIMIT = 10

  const cargarHistorial = useCallback(() => {
    setIsLoading(true)
    getHistorial(page, LIMIT, searchQuery || undefined, desde || undefined, hasta || undefined)
      .then((data) => {
        setCotizaciones(data.cotizaciones)
        setTotal(data.total)
        setTotalPages(Math.ceil(data.total / LIMIT))
      })
      .catch((err) => setError(extractHistorialError(err)))
      .finally(() => setIsLoading(false))
  }, [page, searchQuery, desde, hasta])

  useEffect(() => {
    cargarHistorial()
  }, [cargarHistorial])

  const handleBuscar = () => {
    setPage(1)
    setSearchQuery(searchInput.trim())
  }

  const handleLimpiarFiltros = () => {
    setPage(1)
    setSearchQuery('')
    setSearchInput('')
    setDesde('')
    setHasta('')
  }

  useEffect(() => {
    const state = location.state as { cotizacionCreada?: number } | null
    if (state?.cotizacionCreada) {
      setHighlightId(state.cotizacionCreada)
      setTimeout(() => setHighlightId(null), 3000)
    }
  }, [location.state])

  const handleVer = async (cotizacionId: number) => {
    setIsLoadingDetalle(true)
    setError(null)
    try {
      const data = await getCotizacionById(cotizacionId)
      setCotizacionDetalle(data)
    } catch {
      setError('Error al cargar el detalle de la cotización')
    } finally {
      setIsLoadingDetalle(false)
    }
  }

  const handleFinalizar = async () => {
    if (!cotizacionDetalle) return
    if (!confirm('¿Finalizar cotización? No podrá agregar más productos ni cambiar proveedores.')) return
    setFinalizando(true)
    try {
      const data = await finalizarCotizacion(cotizacionDetalle.cotizacion_id)
      setCotizacionDetalle(data)
      setCotizaciones((prev) =>
        prev.map((c) =>
          c.cotizacion_id === data.cotizacion_id ? { ...c, estado: data.estado } : c
        )
      )
    } catch {
      setError('Error al finalizar la cotización')
    } finally {
      setFinalizando(false)
    }
  }

  const handleAgregarMas = () => {
    if (!cotizacionDetalle) return
    const cid = cotizacionDetalle.cotizacion_id
    setCotizacionDetalle(null)
    navigate('/carga', { state: { cotizacionId: cid } })
  }

  const handleCambiarEnvio = async (envio: OpcionEnvio | null) => {
    if (!cotizacionDetalle) return
    setGuardandoEnvio(true)
    try {
      const data = await actualizarEnvio(cotizacionDetalle.cotizacion_id, envio)
      setCotizacionDetalle(data)
      setMostrarModalEnvio(false)
    } catch {
      setError('Error al actualizar el envío')
    } finally {
      setGuardandoEnvio(false)
    }
  }

  const handleEditarCliente = () => {
    if (!cotizacionDetalle) return
    setClienteForm({
      nombre: cotizacionDetalle.cliente_nombre || '',
      correo: cotizacionDetalle.cliente_correo || '',
      celular: cotizacionDetalle.cliente_celular || '',
    })
    setEditandoCliente(true)
  }

  const handleGuardarCliente = async () => {
    if (!cotizacionDetalle) return
    setGuardandoCliente(true)
    try {
      const data = await actualizarCliente(cotizacionDetalle.cotizacion_id, clienteForm)
      setCotizacionDetalle(data)
      setEditandoCliente(false)
    } catch {
      setError('Error al actualizar los datos del cliente')
    } finally {
      setGuardandoCliente(false)
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

      {/* Barra de búsqueda y filtros */}
      <div
        className="rounded-xl border p-4 space-y-3"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <div className="flex gap-2 flex-wrap">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleBuscar()}
              placeholder="Buscar por cliente o usuario..."
              className="w-full pl-9 pr-3 py-2 rounded-lg text-sm outline-none"
              style={{
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
            />
          </div>
          <button
            onClick={handleBuscar}
            className="px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors flex items-center gap-2"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            <Search className="w-4 h-4" />
            Buscar
          </button>
          {(searchQuery || desde || hasta) && (
            <button
              onClick={handleLimpiarFiltros}
              className="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
              style={{
                border: '1px solid var(--color-border)',
                color: 'var(--color-text-muted)',
              }}
            >
              Limpiar
            </button>
          )}
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          <div className="flex items-center gap-1.5">
            <Calendar className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
            <span className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Desde:</span>
            <input
              type="date"
              value={desde}
              onChange={(e) => { setDesde(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg text-sm outline-none"
              style={{
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
            />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Hasta:</span>
            <input
              type="date"
              value={hasta}
              onChange={(e) => { setHasta(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg text-sm outline-none"
              style={{
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
            />
          </div>
          <span className="text-xs ml-auto" style={{ color: 'var(--color-text-muted)' }}>
            {total} cotización{total !== 1 ? 'es' : ''} en total
          </span>
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
                  <th className="text-left px-4 py-3 font-semibold text-white">Cliente</th>
                  <th className="text-left px-4 py-3 font-semibold text-white">Usuario</th>
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
                      <td className="px-4 py-3" style={{ color: 'var(--color-text)' }}>
                        {c.cliente_nombre || '—'}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--color-text-muted)' }}>
                        {c.usuario_nombre || '—'}
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

      {/* Paginación */}
      {!isLoading && cotizaciones.length > 0 && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Página {page} de {totalPages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              style={{
                border: '1px solid var(--color-border)',
                color: 'var(--color-text)',
                backgroundColor: 'var(--color-surface)',
              }}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
              .map((p, idx, arr) => (
                <span key={idx} className="flex items-center">
                  {idx > 0 && arr[idx - 1] !== p - 1 && (
                    <span className="px-1 text-xs" style={{ color: 'var(--color-text-muted)' }}>...</span>
                  )}
                  <button
                    onClick={() => setPage(p)}
                    className="min-w-[36px] px-2 py-1.5 rounded-lg text-sm font-medium transition-colors"
                    style={{
                      border: '1px solid var(--color-border)',
                      backgroundColor: p === page ? 'var(--color-primary)' : 'var(--color-surface)',
                      color: p === page ? '#fff' : 'var(--color-text)',
                    }}
                  >
                    {p}
                  </button>
                </span>
              ))}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              style={{
                border: '1px solid var(--color-border)',
                color: 'var(--color-text)',
                backgroundColor: 'var(--color-surface)',
              }}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
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
                {cotizacionDetalle.estado !== 'finalizada' && (
                  <button
                    onClick={handleFinalizar}
                    disabled={finalizando}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white disabled:opacity-60"
                    style={{ backgroundColor: '#16a34a' }}
                  >
                    {finalizando ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />}
                    Finalizar
                  </button>
                )}
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
              <div className="text-xs mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                {new Date(cotizacionDetalle.fecha_creacion).toLocaleString()} ·{' '}
                {cotizacionDetalle.items.length} ítem(s) ·{' '}
                <span
                  className="inline-block px-2 py-0.5 rounded text-xs font-medium capitalize"
                  style={ESTADO_STYLE[cotizacionDetalle.estado] ?? ESTADO_STYLE.pendiente}
                >
                  {cotizacionDetalle.estado}
                </span>
              </div>

              <div
                className="rounded-lg border p-3 mb-4 text-sm space-y-1"
                style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)' }}
              >
                {!editandoCliente ? (
                  <>
                    {(cotizacionDetalle.cliente_nombre || cotizacionDetalle.cliente_correo || cotizacionDetalle.cliente_celular) ? (
                      <>
                        {cotizacionDetalle.cliente_nombre && (
                          <div style={{ color: 'var(--color-text)' }}>
                            <span className="font-medium" style={{ color: 'var(--color-text-muted)' }}>Cliente: </span>
                            {cotizacionDetalle.cliente_nombre}
                          </div>
                        )}
                        {cotizacionDetalle.cliente_correo && (
                          <div style={{ color: 'var(--color-text)' }}>
                            <span className="font-medium" style={{ color: 'var(--color-text-muted)' }}>Correo: </span>
                            {cotizacionDetalle.cliente_correo}
                          </div>
                        )}
                        {cotizacionDetalle.cliente_celular && (
                          <div style={{ color: 'var(--color-text)' }}>
                            <span className="font-medium" style={{ color: 'var(--color-text-muted)' }}>Celular: </span>
                            {cotizacionDetalle.cliente_celular}
                          </div>
                        )}
                      </>
                    ) : (
                      <div style={{ color: 'var(--color-text-muted)' }}>Sin datos de cliente</div>
                    )}
                    {cotizacionDetalle.estado !== 'finalizada' && (
                      <button
                        onClick={handleEditarCliente}
                        className="mt-2 flex items-center gap-1.5 text-xs font-medium transition-colors"
                        style={{ color: 'var(--color-primary)' }}
                      >
                        <UserCog className="w-3.5 h-3.5" />
                        Modificar cliente
                      </button>
                    )}
                  </>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium" style={{ color: 'var(--color-text)' }}>Editar cliente</span>
                      <button
                        onClick={() => setEditandoCliente(false)}
                        className="p-1 rounded"
                        style={{ color: 'var(--color-text-muted)' }}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <input
                      type="text"
                      placeholder="Nombre"
                      value={clienteForm.nombre}
                      onChange={(e) => setClienteForm({ ...clienteForm, nombre: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
                      style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
                    />
                    <input
                      type="email"
                      placeholder="Correo"
                      value={clienteForm.correo}
                      onChange={(e) => setClienteForm({ ...clienteForm, correo: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
                      style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
                    />
                    <input
                      type="text"
                      placeholder="Celular"
                      value={clienteForm.celular}
                      onChange={(e) => setClienteForm({ ...clienteForm, celular: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
                      style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
                    />
                    <button
                      onClick={handleGuardarCliente}
                      disabled={guardandoCliente}
                      className="w-full py-2 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                      style={{ backgroundColor: 'var(--color-primary)' }}
                    >
                      {guardandoCliente ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Guardando...</>
                      ) : (
                        'Guardar cambios'
                      )}
                    </button>
                  </div>
                )}
              </div>

              {cotizacionDetalle.estado === 'finalizada' && (
                <div
                  className="flex items-center gap-2 rounded-lg border p-3 mb-4 text-sm"
                  style={{ borderColor: '#D1FAE5', backgroundColor: '#F0FDF4', color: '#065F46' }}
                >
                  <Lock className="w-4 h-4 flex-shrink-0" />
                  <span>Cotización finalizada. No se pueden agregar más productos ni cambiar proveedores.</span>
                </div>
              )}

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
                  <tr className="border-t" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)' }}>
                    <td colSpan={4} className="px-3 py-2 text-right font-medium text-sm" style={{ color: 'var(--color-text)' }}>
                      Subtotal
                    </td>
                    <td className="px-3 py-2 text-right font-medium text-sm" style={{ color: 'var(--color-text)' }}>
                      {money(cotizacionDetalle.total)}
                    </td>
                  </tr>
                  <tr style={{ backgroundColor: 'var(--color-bg)' }}>
                    <td colSpan={4} className="px-3 py-2 text-right text-xs" style={{ color: 'var(--color-text-muted)' }}>
                      {cotizacionDetalle.envio_nombre
                        ? `Envío (${cotizacionDetalle.envio_nombre})`
                        : 'Envío (no seleccionado)'}
                    </td>
                    <td className="px-3 py-2 text-right text-xs font-medium" style={{ color: 'var(--color-text)' }}>
                      {cotizacionDetalle.envio_precio != null ? money(cotizacionDetalle.envio_precio) : '—'}
                    </td>
                  </tr>
                  <tr className="border-t-2" style={{ borderColor: 'var(--color-border)' }}>
                    <td colSpan={4} className="px-3 py-3 text-right font-bold" style={{ color: 'var(--color-text)' }}>
                      Total
                    </td>
                    <td className="px-3 py-3 text-right font-bold text-base" style={{ color: 'var(--color-primary)' }}>
                      {money(Number(cotizacionDetalle.total) + Number(cotizacionDetalle.envio_precio ?? 0))}
                    </td>
                  </tr>
                </tfoot>
              </table>

              {cotizacionDetalle.estado !== 'finalizada' && (
                <div className="mt-4 pt-4 border-t space-y-2" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={() => setMostrarModalEnvio(true)}
                    className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium text-sm transition-colors"
                    style={{
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text)',
                      backgroundColor: 'transparent',
                    }}
                  >
                    <Truck className="w-4 h-4" />
                    {cotizacionDetalle.envio_nombre ? 'Cambiar envío' : 'Seleccionar envío'}
                  </button>
                  <button
                    onClick={handleAgregarMas}
                    className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium text-white text-sm transition-colors"
                    style={{ backgroundColor: 'var(--color-primary)' }}
                  >
                    <Plus className="w-4 h-4" />
                    Agregar más productos
                  </button>
                  <p className="text-xs text-center mt-2" style={{ color: 'var(--color-text-muted)' }}>
                    Irás a la página de carga para buscar y agregar nuevos productos
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal para cambiar envío */}
      {mostrarModalEnvio && cotizacionDetalle && (
        <EnvioModal
          onSubmit={(envio) => handleCambiarEnvio(envio)}
          onCancel={() => setMostrarModalEnvio(false)}
          isLoading={guardandoEnvio}
        />
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

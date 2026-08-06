import { useState, useEffect } from 'react'
import { Store, Check, X, BadgeCheck, AlertTriangle, ChevronDown, ChevronUp, ChevronRight, Loader2, Palette, Sparkles } from 'lucide-react'
import type { ResultadoComponente, OpcionProducto } from '@/shared/types'
import { buscarAlternativas } from '../services/busquedaService'

interface Props {
  resultado: ResultadoComponente
  onToggleSeleccion: (termino: string, cantidad: number, opcion: OpcionProducto) => void
  seleccionadas: OpcionProducto[]
  onPreguntarAgente?: (termino: string) => void
}

function money(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `$${Number(value).toFixed(2)}`
}

export default function TarjetaProducto({ resultado, onToggleSeleccion, seleccionadas, onPreguntarAgente }: Props) {
  const { termino, cantidad, opciones, encontrado_propia } = resultado
  const [agotadoExpandido, setAgotadoExpandido] = useState<string | null>(null)
  const [alternativasRemotas, setAlternativasRemotas] = useState<Record<string, OpcionProducto[]>>({})
  const [cargandoAlternativas, setCargandoAlternativas] = useState<string | null>(null)
  const [varianteSeleccionada, setVarianteSeleccionada] = useState<string | null>(null)
  const [colapsado, setColapsado] = useState(false)

  // Auto-colapsar cuando hay productos seleccionados
  useEffect(() => {
    if (seleccionadas.length > 0) {
      setColapsado(true)
    }
  }, [seleccionadas.length])

  const isSelected = (op: OpcionProducto) =>
    seleccionadas.some((s) => s.tienda === op.tienda && s.nombre_producto === op.nombre_producto)

  const opcionesDisponibles = opciones.filter((o) => o.disponible)
  const esAgotado = opciones.length === 1 && opciones[0].agotado === true

  const handleClickVariante = (e: React.MouseEvent, op: OpcionProducto, variante: string) => {
    e.stopPropagation()
    if (!op.disponible) return
    setVarianteSeleccionada(variante)
    const opConVariante = { ...op, nombre_producto: `${op.nombre_producto} - ${variante}` }
    onToggleSeleccion(termino, cantidad, opConVariante)
  }

  const handleClickOpcion = (op: OpcionProducto) => {
    if (!op.disponible) {
      const key = `${op.tienda}-${op.nombre_producto}`
      setAgotadoExpandido((prev) => {
        if (prev === key) return null
        // Cargar alternativas remotas si no tenemos cache local
        if (!alternativasRemotas[key] && !cargandoAlternativas) {
          setCargandoAlternativas(key)
          buscarAlternativas(op.nombre_producto, op.tienda ?? '')
            .then((alts) => {
              setAlternativasRemotas((prev) => ({ ...prev, [key]: alts }))
            })
            .catch(() => {
              setAlternativasRemotas((prev) => ({ ...prev, [key]: [] }))
            })
            .finally(() => setCargandoAlternativas(null))
        }
        return key
      })
      return
    }
    onToggleSeleccion(termino, cantidad, op)
  }

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <div
        className="px-4 py-3 flex items-center justify-between cursor-pointer select-none transition-colors hover:opacity-80"
        style={{ backgroundColor: 'var(--color-bg)' }}
        onClick={() => setColapsado((v) => !v)}
      >
        <div className="flex items-center gap-2">
          {opciones.length > 0 && !esAgotado && (
            colapsado
              ? <ChevronRight className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }} />
              : <ChevronDown className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }} />
          )}
          <span className="font-bold text-sm" style={{ color: 'var(--color-text)' }}>
            {termino}
          </span>
          {cantidad > 1 && (
            <span
              className="px-2 py-0.5 rounded text-xs font-medium"
              style={{ backgroundColor: 'var(--color-primary)', color: '#fff' }}
            >
              x{cantidad}
            </span>
          )}
          {encontrado_propia && (
            <span
              className="flex items-center gap-1 px-1.5 py-0.5 rounded text-xs"
              style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}
            >
              <BadgeCheck className="w-3 h-3" />
              AV
            </span>
          )}
          {colapsado && seleccionadas.length > 0 && (
            <span
              className="flex items-center gap-1 px-1.5 py-0.5 rounded text-xs"
              style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}
            >
              <Check className="w-3 h-3" />
              {seleccionadas.length} {seleccionadas.length === 1 ? 'seleccionado' : 'seleccionados'}
            </span>
          )}
        </div>
        <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          {esAgotado ? 'No encontrado' : `${opciones.length} ${opciones.length === 1 ? 'opción' : 'opciones'}`}
        </span>
      </div>

      {opciones.length === 0 || esAgotado ? (
        <div className="px-4 py-4 space-y-2">
          <div className="flex items-center justify-center gap-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
            <X className="w-4 h-4" />
            No encontrado en ninguna tienda
          </div>
          {onPreguntarAgente && (
            <div className="flex justify-center">
              <button
                onClick={() => onPreguntarAgente(termino)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors text-white"
                style={{ backgroundColor: 'var(--color-primary)' }}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Preguntar al asistente IA
              </button>
            </div>
          )}
        </div>
      ) : colapsado ? null : (
        <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
          {opciones.map((op) => {
            const selected = isSelected(op)
            const key = `${op.tienda}-${op.nombre_producto}`
            const isExpanded = agotadoExpandido === key
            const alternativasLocales = opcionesDisponibles.filter((o) => o.tienda !== op.tienda)
            const altsRemotas = alternativasRemotas[key] || []
            const alternativas = [...alternativasLocales]
            for (const alt of altsRemotas) {
              if (!alternativas.some((a) => a.tienda === alt.tienda && a.nombre_producto === alt.nombre_producto)) {
                alternativas.push(alt)
              }
            }
            const estaCargando = cargandoAlternativas === key

            return (
              <div key={key}>
                <button
                  onClick={() => handleClickOpcion(op)}
                  className="w-full flex items-center justify-between px-4 py-3 text-left transition-colors"
                  style={{
                    backgroundColor: selected ? 'var(--color-primary)' : 'transparent',
                    opacity: !op.disponible && !selected ? 0.7 : 1,
                  }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {selected ? (
                      <Check className="w-4 h-4 flex-shrink-0" style={{ color: '#fff' }} />
                    ) : (
                      <Store className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }} />
                    )}
                    <div className="min-w-0">
                      <div
                        className="text-sm font-medium truncate"
                        style={{ color: selected ? '#fff' : 'var(--color-text)' }}
                      >
                        {op.nombre_producto}
                      </div>
                      <div
                        className="text-xs flex items-center gap-2 flex-wrap"
                        style={{ color: selected ? 'rgba(255,255,255,0.8)' : 'var(--color-text-muted)' }}
                      >
                        {op.tienda}
                        {op.es_propio && (
                          <span
                            className="px-1.5 py-0.5 rounded text-xs"
                            style={{
                              backgroundColor: selected ? 'rgba(255,255,255,0.2)' : '#D1FAE5',
                              color: selected ? '#fff' : '#065F46',
                            }}
                          >
                            Tienda propia
                          </span>
                        )}
                        {op.margen_aplicado > 0 && (
                          <span
                            className="px-1.5 py-0.5 rounded text-xs"
                            style={{
                              backgroundColor: selected ? 'rgba(255,255,255,0.2)' : '#FEF3C7',
                              color: selected ? '#fff' : '#B45309',
                            }}
                          >
                            +{op.margen_aplicado}%
                          </span>
                        )}
                        {!op.disponible && (
                          <span
                            className="flex items-center gap-1 text-xs cursor-pointer"
                            style={{ color: selected ? 'rgba(255,255,255,0.8)' : 'var(--color-danger)' }}
                          >
                            <AlertTriangle className="w-3 h-3" />
                            Agotado
                            <span style={{ color: '#065F46' }} className="flex items-center gap-0.5">
                              · ver alternativas
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </span>
                          </span>
                        )}
                      </div>
                      {op.variantes && op.variantes.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap mt-1" onClick={(e) => e.stopPropagation()}>
                          <Palette className="w-3 h-3 flex-shrink-0" style={{ color: selected ? 'rgba(255,255,255,0.6)' : 'var(--color-text-muted)' }} />
                          {op.variantes.map((v, vi) => {
                            const vSelected = varianteSeleccionada === v
                            return (
                              <button
                                key={vi}
                                onClick={(e) => handleClickVariante(e, op, v)}
                                disabled={!op.disponible}
                                className="px-1.5 py-0.5 rounded text-xs transition-colors disabled:opacity-50"
                                style={{
                                  backgroundColor: vSelected
                                    ? 'var(--color-primary)'
                                    : selected
                                      ? 'rgba(255,255,255,0.15)'
                                      : 'var(--color-bg)',
                                  color: vSelected
                                    ? '#fff'
                                    : selected
                                      ? 'rgba(255,255,255,0.9)'
                                      : 'var(--color-text-muted)',
                                  border: `1px solid ${vSelected ? 'var(--color-primary)' : selected ? 'rgba(255,255,255,0.2)' : 'var(--color-border)'}`,
                                }}
                              >
                                {v}
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0 ml-2">
                    <div
                      className="font-bold text-sm"
                      style={{ color: selected ? '#fff' : 'var(--color-text)' }}
                    >
                      {money(op.precio_con_margen)}
                    </div>
                    {op.margen_aplicado > 0 && op.precio_base !== op.precio_con_margen && (
                      <div
                        className="text-xs"
                        style={{ color: selected ? 'rgba(255,255,255,0.6)' : 'var(--color-text-muted)' }}
                      >
                        base: {money(op.precio_base)}
                      </div>
                    )}
                  </div>
                </button>

                {/* Panel de alternativas para agotados */}
                {isExpanded && (
                  <div
                    className="px-4 py-3 space-y-2"
                    style={{ backgroundColor: 'var(--color-bg)' }}
                  >
                    {estaCargando ? (
                      <div className="flex items-center gap-2 py-3 justify-center" style={{ color: 'var(--color-text-muted)' }}>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-xs">Buscando alternativas...</span>
                      </div>
                    ) : alternativas.length > 0 ? (
                      <>
                        <p className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
                          Productos similares en otras tiendas:
                        </p>
                        {alternativas.map((alt, altIdx) => {
                          const altSelected = isSelected(alt)
                          return (
                            <button
                              key={`${alt.tienda}-${altIdx}`}
                              onClick={() => onToggleSeleccion(termino, cantidad, alt)}
                              className="w-full flex items-center justify-between rounded-lg border px-3 py-2 text-left transition-colors"
                              style={{
                                backgroundColor: altSelected ? 'var(--color-primary)' : 'var(--color-surface)',
                                borderColor: altSelected ? 'var(--color-primary)' : 'var(--color-border)',
                              }}
                            >
                              <div className="flex items-center gap-2 min-w-0">
                                {altSelected ? (
                                  <Check className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#fff' }} />
                                ) : (
                                  <Store className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }} />
                                )}
                                <div className="min-w-0">
                                  <div
                                    className="text-xs font-medium truncate"
                                    style={{ color: altSelected ? '#fff' : 'var(--color-text)' }}
                                  >
                                    {alt.nombre_producto}
                                  </div>
                                  <div
                                    className="text-xs flex items-center gap-1.5"
                                    style={{ color: altSelected ? 'rgba(255,255,255,0.8)' : 'var(--color-text-muted)' }}
                                  >
                                    {alt.tienda}
                                    {alt.margen_aplicado > 0 && (
                                      <span
                                        className="px-1 py-0.5 rounded text-xs"
                                        style={{
                                          backgroundColor: altSelected ? 'rgba(255,255,255,0.2)' : '#FEF3C7',
                                          color: altSelected ? '#fff' : '#B45309',
                                        }}
                                      >
                                        +{alt.margen_aplicado}%
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                              <span
                                className="text-sm font-bold flex-shrink-0"
                                style={{ color: altSelected ? '#fff' : 'var(--color-primary)' }}
                              >
                                {money(alt.precio_con_margen)}
                              </span>
                            </button>
                          )
                        })}
                      </>
                    ) : (
                      <p className="text-xs text-center py-2" style={{ color: 'var(--color-text-muted)' }}>
                        No se encontraron productos similares en otras tiendas
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { Store, Check, X, BadgeCheck, Lightbulb, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import type { ResultadoComponente, OpcionProducto } from '@/shared/types'

interface Props {
  resultado: ResultadoComponente
  onToggleSeleccion: (termino: string, cantidad: number, opcion: OpcionProducto) => void
  seleccionadas: OpcionProducto[]
  onBuscarSugerencia?: (sugerencia: string) => void
}

function money(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `$${Number(value).toFixed(2)}`
}

export default function TarjetaProducto({ resultado, onToggleSeleccion, seleccionadas, onBuscarSugerencia }: Props) {
  const { termino, cantidad, opciones, encontrado_propia, sugerencia } = resultado
  const [agotadoExpandido, setAgotadoExpandido] = useState<string | null>(null)

  const isSelected = (op: OpcionProducto) =>
    seleccionadas.some((s) => s.tienda === op.tienda && s.nombre_producto === op.nombre_producto)

  const opcionesDisponibles = opciones.filter((o) => o.disponible)

  const handleClickOpcion = (op: OpcionProducto) => {
    if (!op.disponible) {
      // Toggle expandir/colapsar alternativas
      const key = `${op.tienda}-${op.nombre_producto}`
      setAgotadoExpandido((prev) => (prev === key ? null : key))
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
        className="px-4 py-3 flex items-center justify-between"
        style={{ backgroundColor: 'var(--color-bg)' }}
      >
        <div className="flex items-center gap-2">
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
        </div>
        <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          {opciones.length} {opciones.length === 1 ? 'opción' : 'opciones'}
        </span>
      </div>

      {opciones.length === 0 ? (
        <div className="px-4 py-4 space-y-2">
          <div className="flex items-center justify-center gap-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
            <X className="w-4 h-4" />
            No encontrado en ninguna tienda
          </div>
          {sugerencia && (
            <div
              className="flex items-start gap-2 rounded-lg border p-3 text-xs"
              style={{ borderColor: '#FEF3C7', backgroundColor: '#FFFBEB', color: '#92400E' }}
            >
              <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium mb-1">¿Buscabas "{sugerencia.sugerencia}"?</p>
                <p className="opacity-80 mb-2">{sugerencia.razon}</p>
                {onBuscarSugerencia && (
                  <button
                    onClick={() => onBuscarSugerencia(sugerencia.sugerencia)}
                    className="px-2 py-1 rounded text-xs font-medium transition-colors"
                    style={{ backgroundColor: '#92400E', color: '#fff' }}
                  >
                    Buscar "{sugerencia.sugerencia}"
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
          {opciones.map((op) => {
            const selected = isSelected(op)
            const key = `${op.tienda}-${op.nombre_producto}`
            const isExpanded = agotadoExpandido === key
            const alternativas = opcionesDisponibles.filter((o) => o.tienda !== op.tienda)

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
                            <span style={{ color: alternativas.length > 0 ? '#065F46' : 'var(--color-text-muted)' }} className="flex items-center gap-0.5">
                              {alternativas.length > 0 ? '· ver alternativas' : '· sin alternativas'}
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </span>
                          </span>
                        )}
                      </div>
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
                    {alternativas.length > 0 ? (
                      <>
                        <p className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
                          Disponible en otras tiendas:
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
                        No hay alternativas disponibles en otras tiendas
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

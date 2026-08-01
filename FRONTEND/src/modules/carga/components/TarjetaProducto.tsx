import { Store, Check, X, BadgeCheck } from 'lucide-react'
import type { ResultadoComponente, OpcionProducto } from '@/shared/types'

interface Props {
  resultado: ResultadoComponente
  onSeleccionar: (termino: string, cantidad: number, opcion: OpcionProducto) => void
  seleccionada?: OpcionProducto | null
}

function money(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `$${Number(value).toFixed(2)}`
}

export default function TarjetaProducto({ resultado, onSeleccionar, seleccionada }: Props) {
  const { termino, cantidad, opciones, encontrado_propia } = resultado

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
        <div className="px-4 py-6 flex items-center justify-center gap-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
          <X className="w-4 h-4" />
          No encontrado en ninguna tienda
        </div>
      ) : (
        <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
          {opciones.map((op, idx) => {
            const isSelected = seleccionada?.tienda === op.tienda && seleccionada?.nombre_producto === op.nombre_producto
            return (
              <button
                key={`${op.tienda}-${idx}`}
                onClick={() => onSeleccionar(termino, cantidad, op)}
                disabled={!op.disponible}
                className="w-full flex items-center justify-between px-4 py-3 text-left transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: isSelected ? 'var(--color-primary)' : 'transparent',
                }}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {isSelected ? (
                    <Check className="w-4 h-4 flex-shrink-0" style={{ color: '#fff' }} />
                  ) : (
                    <Store className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }} />
                  )}
                  <div className="min-w-0">
                    <div
                      className="text-sm font-medium truncate"
                      style={{ color: isSelected ? '#fff' : 'var(--color-text)' }}
                    >
                      {op.nombre_producto}
                    </div>
                    <div
                      className="text-xs flex items-center gap-2"
                      style={{ color: isSelected ? 'rgba(255,255,255,0.8)' : 'var(--color-text-muted)' }}
                    >
                      {op.tienda}
                      {op.es_propio && (
                        <span
                          className="px-1.5 py-0.5 rounded text-xs"
                          style={{
                            backgroundColor: isSelected ? 'rgba(255,255,255,0.2)' : '#D1FAE5',
                            color: isSelected ? '#fff' : '#065F46',
                          }}
                        >
                          Tienda propia
                        </span>
                      )}
                      {op.margen_aplicado > 0 && (
                        <span
                          className="px-1.5 py-0.5 rounded text-xs"
                          style={{
                            backgroundColor: isSelected ? 'rgba(255,255,255,0.2)' : '#FEF3C7',
                            color: isSelected ? '#fff' : '#B45309',
                          }}
                        >
                          +{op.margen_aplicado}%
                        </span>
                      )}
                      {!op.disponible && (
                        <span className="text-xs" style={{ color: isSelected ? 'rgba(255,255,255,0.8)' : 'var(--color-danger)' }}>
                          Agotado
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 ml-2">
                  <div
                    className="font-bold text-sm"
                    style={{ color: isSelected ? '#fff' : 'var(--color-text)' }}
                  >
                    {money(op.precio_con_margen)}
                  </div>
                  {op.margen_aplicado > 0 && op.precio_base !== op.precio_con_margen && (
                    <div
                      className="text-xs"
                      style={{ color: isSelected ? 'rgba(255,255,255,0.6)' : 'var(--color-text-muted)' }}
                    >
                      base: {money(op.precio_base)}
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

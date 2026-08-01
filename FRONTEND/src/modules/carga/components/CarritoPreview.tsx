import { ShoppingCart, Trash2, Lock } from 'lucide-react'
import type { ItemCarrito } from '@/shared/types'

interface Props {
  items: ItemCarrito[]
  onQuitar: (index: number) => void
  onFinalizar: () => void
  disabled?: boolean
}

function money(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `$${Number(value).toFixed(2)}`
}

export default function CarritoPreview({ items, onQuitar, onFinalizar, disabled }: Props) {
  const total = items.reduce((sum, item) => {
    const precio = item.opcion_seleccionada.precio_con_margen ?? 0
    return sum + precio * item.cantidad
  }, 0)

  return (
    <div
      className="rounded-xl border sticky top-4"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: 'var(--color-border)' }}>
        <ShoppingCart className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
        <h3 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
          Carrito ({items.length})
        </h3>
      </div>

      {items.length === 0 ? (
        <div className="px-4 py-8 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
          No hay items en el carrito.
          <br />
          Busca componentes y selecciona una opción.
        </div>
      ) : (
        <>
          <div className="max-h-96 overflow-y-auto divide-y" style={{ borderColor: 'var(--color-border)' }}>
            {items.map((item, idx) => (
              <div key={idx} className="px-4 py-3 flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate" style={{ color: 'var(--color-text)' }}>
                    {item.opcion_seleccionada.nombre_producto}
                  </div>
                  <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                    {item.opcion_seleccionada.tienda} · x{item.cantidad}
                  </div>
                  <div className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
                    {money(item.opcion_seleccionada.precio_con_margen)} c/u
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className="text-sm font-bold" style={{ color: 'var(--color-primary)' }}>
                    {money((item.opcion_seleccionada.precio_con_margen ?? 0) * item.cantidad)}
                  </span>
                  <button
                    onClick={() => onQuitar(idx)}
                    className="p-1 rounded transition-colors"
                    style={{ color: 'var(--color-danger)' }}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="px-4 py-3 border-t" style={{ borderColor: 'var(--color-border)' }}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
                Total
              </span>
              <span className="text-lg font-bold" style={{ color: 'var(--color-primary)' }}>
                {money(total)}
              </span>
            </div>
            <button
              onClick={onFinalizar}
              disabled={disabled}
              className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              style={{ backgroundColor: 'var(--color-primary)' }}
            >
              <Lock className="w-4 h-4" />
              Generar cotización
            </button>
          </div>
        </>
      )}
    </div>
  )
}

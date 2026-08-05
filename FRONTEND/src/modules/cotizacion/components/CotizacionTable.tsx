import { useState } from 'react'
import { CheckCircle, XCircle, Store, ShoppingCart, Lock, Plus, AlertCircle } from 'lucide-react'
import type { Cotizacion, CotizacionItem, OpcionProveedor } from '@/shared/types'

interface Props {
  cotizacion: Cotizacion
  onSelectProveedor?: (itemId: number, tienda: string) => void
  onAgregarItem?: (texto: string) => void
  onFinalizar?: () => void
  selectingId?: number | null
  ivaPct?: number
}

function money(value: string | number): string {
  return `$${Number(value).toFixed(2)}`
}

function OpcionesProveedor({
  item,
  onSelect,
  selecting,
}: {
  item: CotizacionItem
  onSelect: (tienda: string) => void
  selecting: boolean
}) {
  const opciones = item.opciones_proveedores || []
  if (opciones.length === 0) return null

  return (
    <div className="mt-2 space-y-1">
      <p className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
        Selecciona un proveedor:
      </p>
      {opciones.map((op: OpcionProveedor) => {
        const isSelected = item.proveedor === op.tienda && item.seleccionado
        return (
          <button
            key={op.tienda}
            onClick={() => onSelect(op.tienda)}
            disabled={selecting}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg border text-xs transition-colors disabled:opacity-60"
            style={{
              borderColor: isSelected ? 'var(--color-primary)' : 'var(--color-border)',
              backgroundColor: isSelected ? 'var(--color-primary)' : 'transparent',
              color: isSelected ? '#fff' : 'var(--color-text)',
            }}
          >
            <span className="flex items-center gap-2">
              <Store className="w-3.5 h-3.5" />
              {op.tienda}
              <span className="opacity-70">(base: {money(op.precio_base)})</span>
              {op.margen_aplicado > 0 && (
                <span
                  className="px-1 py-0.5 rounded"
                  style={{
                    backgroundColor: isSelected ? 'rgba(255,255,255,0.2)' : '#FEF3C7',
                    color: isSelected ? '#fff' : '#B45309',
                  }}
                >
                  +{op.margen_aplicado}%
                </span>
              )}
            </span>
            <span className="font-bold">{money(op.precio_con_margen)}</span>
          </button>
        )
      })}
    </div>
  )
}

export default function CotizacionTable({ cotizacion, onSelectProveedor, onAgregarItem, onFinalizar, selectingId, ivaPct = 0 }: Props) {
  const [nuevoItem, setNuevoItem] = useState('')
  const [adding, setAdding] = useState(false)
  const [finishing, setFinishing] = useState(false)

  const handleAgregar = async () => {
    if (!nuevoItem.trim() || !onAgregarItem) return
    setAdding(true)
    try {
      await onAgregarItem(nuevoItem.trim())
      setNuevoItem('')
    } finally {
      setAdding(false)
    }
  }

  const handleFinalizar = async () => {
    if (!onFinalizar) return
    setFinishing(true)
    try {
      await onFinalizar()
    } finally {
      setFinishing(false)
    }
  }

  const hayPendientes = cotizacion.items.some((i) => !i.seleccionado && i.disponible)
  const finalizada = cotizacion.estado === 'finalizada'

  return (
    <div className="space-y-4">
      <div
        className="rounded-xl border overflow-hidden"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ backgroundColor: 'var(--color-primary)' }}>
                <th className="text-left px-4 py-3 font-semibold text-white">Producto</th>
                <th className="text-center px-4 py-3 font-semibold text-white">Cant.</th>
                <th className="text-left px-4 py-3 font-semibold text-white">Proveedor</th>
                <th className="text-right px-4 py-3 font-semibold text-white">P. Unitario</th>
                <th className="text-right px-4 py-3 font-semibold text-white">Subtotal</th>
                <th className="text-center px-4 py-3 font-semibold text-white">Estado</th>
              </tr>
            </thead>
            <tbody>
              {cotizacion.items.map((item) => (
                <tr key={item.id} className="border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <td className="px-4 py-3 align-top">
                    <div className="font-medium" style={{ color: 'var(--color-text)' }}>
                      {item.producto_nombre}
                    </div>
                    {!item.seleccionado && item.disponible && (
                      <span
                        className="inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium"
                        style={{ backgroundColor: '#FEF3C7', color: '#B45309' }}
                      >
                        Pendiente selección
                      </span>
                    )}
                    {item.opciones_proveedores && item.opciones_proveedores.length > 0 && onSelectProveedor && !finalizada && (
                      <OpcionesProveedor
                        item={item}
                        onSelect={(tienda) => onSelectProveedor(item.id, tienda)}
                        selecting={selectingId === item.id}
                      />
                    )}
                  </td>
                  <td className="px-4 py-3 text-center align-top" style={{ color: 'var(--color-text)' }}>
                    {item.cantidad}
                  </td>
                  <td className="px-4 py-3 align-top" style={{ color: 'var(--color-text-muted)' }}>
                    {item.proveedor || '—'}
                    {Number(item.margen_aplicado) > 0 && (
                      <span
                        className="ml-2 inline-block px-1.5 py-0.5 rounded text-xs"
                        style={{ backgroundColor: '#FEF3C7', color: '#B45309' }}
                      >
                        +{item.margen_aplicado}%
                      </span>
                    )}
                    {item.es_propio && (
                      <span
                        className="ml-2 inline-block px-1.5 py-0.5 rounded text-xs"
                        style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}
                      >
                        Tienda propia
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right align-top" style={{ color: 'var(--color-text)' }}>
                    {item.disponible ? money(item.precio_unitario) : '—'}
                  </td>
                  <td className="px-4 py-3 text-right align-top font-medium" style={{ color: 'var(--color-text)' }}>
                    {item.disponible ? money(item.subtotal) : '—'}
                  </td>
                  <td className="px-4 py-3 text-center align-top">
                    {item.disponible ? (
                      <span className="inline-flex items-center gap-1 text-xs font-medium" style={{ color: '#16a34a' }}>
                        <CheckCircle className="w-4 h-4" /> Disponible
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-medium" style={{ color: 'var(--color-danger)' }}>
                        <XCircle className="w-4 h-4" /> Sin datos
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)' }}>
                <td colSpan={4} className="px-4 py-3 text-right font-medium" style={{ color: 'var(--color-text)' }}>
                  Subtotal
                </td>
                <td className="px-4 py-3 text-right font-medium" style={{ color: 'var(--color-text)' }}>
                  {money(cotizacion.total)}
                </td>
                <td />
              </tr>
              <tr style={{ backgroundColor: 'var(--color-bg)' }}>
                <td colSpan={4} className="px-4 py-2 text-right text-sm" style={{ color: 'var(--color-text-muted)' }}>
                  {cotizacion.envio_nombre
                    ? `Envío (${cotizacion.envio_nombre})`
                    : 'Envío (no seleccionado)'}
                </td>
                <td className="px-4 py-2 text-right text-sm font-medium" style={{ color: 'var(--color-text)' }}>
                  {cotizacion.envio_precio != null ? money(cotizacion.envio_precio) : '—'}
                </td>
                <td />
              </tr>
              {ivaPct > 0 && (
                <tr style={{ backgroundColor: 'var(--color-bg)' }}>
                  <td colSpan={4} className="px-4 py-2 text-right text-sm" style={{ color: 'var(--color-text-muted)' }}>
                    IVA ({ivaPct}%)
                  </td>
                  <td className="px-4 py-2 text-right text-sm font-medium" style={{ color: 'var(--color-text)' }}>
                    {money(
                      (Number(cotizacion.total) + Number(cotizacion.envio_precio ?? 0)) * ivaPct / 100
                    )}
                  </td>
                  <td />
                </tr>
              )}
              <tr className="border-t-2" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)' }}>
                <td colSpan={4} className="px-4 py-3 text-right font-bold" style={{ color: 'var(--color-text)' }}>
                  TOTAL
                </td>
                <td className="px-4 py-3 text-right font-bold text-lg" style={{ color: 'var(--color-primary)' }}>
                  {(() => {
                    const subtotal = Number(cotizacion.total)
                    const envio = Number(cotizacion.envio_precio ?? 0)
                    const base = subtotal + envio
                    const iva = ivaPct > 0 ? base * ivaPct / 100 : 0
                    return money(base + iva)
                  })()}
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {!finalizada && onAgregarItem && (
        <div
          className="rounded-xl border p-4"
          style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <ShoppingCart className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
            <h3 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
              Agregar al carrito
            </h3>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={nuevoItem}
              onChange={(e) => setNuevoItem(e.target.value)}
              disabled={adding}
              placeholder="ej: 5 resistencias de 220 ohm"
              className="flex-1 px-3 py-2 rounded-lg border outline-none text-sm"
              style={{
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
              onKeyDown={(e) => e.key === 'Enter' && handleAgregar()}
            />
            <button
              onClick={handleAgregar}
              disabled={!nuevoItem.trim() || adding}
              className="inline-flex items-center gap-1 px-4 py-2 rounded-lg font-medium text-white text-sm disabled:opacity-60"
              style={{ backgroundColor: 'var(--color-primary)' }}
            >
              <Plus className="w-4 h-4" />
              {adding ? 'Agregando...' : 'Agregar'}
            </button>
          </div>
        </div>
      )}

      {!finalizada && onFinalizar && (
        <div className="flex items-center justify-between">
          {hayPendientes && (
            <div className="flex items-center gap-2 text-sm" style={{ color: '#B45309' }}>
              <AlertCircle className="w-4 h-4" />
              Hay ítems pendientes de selección
            </div>
          )}
          <button
            onClick={handleFinalizar}
            disabled={finishing || hayPendientes}
            className="ml-auto inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium text-white text-sm disabled:opacity-60 disabled:cursor-not-allowed"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            <Lock className="w-4 h-4" />
            {finishing ? 'Finalizando...' : 'Finalizar cotización'}
          </button>
        </div>
      )}

      {finalizada && (
        <div
          className="flex items-center gap-2 rounded-lg border p-3 text-sm"
          style={{ borderColor: '#D1FAE5', backgroundColor: '#F0FDF4', color: '#065F46' }}
        >
          <Lock className="w-4 h-4" />
          Cotización finalizada. Los precios y proveedores están bloqueados.
        </div>
      )}

      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
        Los ítems "Sin datos" no tienen precios disponibles en las tiendas consultadas.
        Los ítems de AV Electronics (tienda propia) no incluyen margen. Los de otras tiendas incluyen 5% de margen.
      </p>
    </div>
  )
}

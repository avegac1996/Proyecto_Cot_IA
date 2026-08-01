import { CheckCircle, XCircle } from 'lucide-react'
import type { Cotizacion } from '@/shared/types'

interface Props {
  cotizacion: Cotizacion
}

function money(value: string | number): string {
  return `$${Number(value).toFixed(2)}`
}

export default function CotizacionTable({ cotizacion }: Props) {
  return (
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
                <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-text)' }}>
                  {item.producto_nombre}
                </td>
                <td className="px-4 py-3 text-center" style={{ color: 'var(--color-text)' }}>
                  {item.cantidad}
                </td>
                <td className="px-4 py-3" style={{ color: 'var(--color-text-muted)' }}>
                  {item.proveedor || '—'}
                  {Number(item.margen_aplicado) > 0 && (
                    <span
                      className="ml-2 inline-block px-1.5 py-0.5 rounded text-xs"
                      style={{ backgroundColor: '#FEF3C7', color: '#B45309' }}
                    >
                      +{item.margen_aplicado}%
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right" style={{ color: 'var(--color-text)' }}>
                  {item.disponible ? money(item.precio_unitario) : '—'}
                </td>
                <td className="px-4 py-3 text-right font-medium" style={{ color: 'var(--color-text)' }}>
                  {item.disponible ? money(item.subtotal) : '—'}
                </td>
                <td className="px-4 py-3 text-center">
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
            <tr className="border-t-2" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)' }}>
              <td colSpan={4} className="px-4 py-3 text-right font-bold" style={{ color: 'var(--color-text)' }}>
                TOTAL
              </td>
              <td className="px-4 py-3 text-right font-bold text-lg" style={{ color: 'var(--color-primary)' }}>
                {money(cotizacion.total)}
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}

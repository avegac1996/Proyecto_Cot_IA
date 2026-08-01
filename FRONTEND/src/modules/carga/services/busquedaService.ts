import api from '@/shared/lib/api'
import type { BusquedaResponse, ConfiguracionNegocio, ItemCarrito, Cotizacion } from '@/shared/types'

export async function buscarComponentes(texto: string): Promise<BusquedaResponse> {
  const { data } = await api.post<BusquedaResponse>('/buscar', { texto })
  return data
}

export async function getConfiguracion(): Promise<ConfiguracionNegocio> {
  const { data } = await api.get<ConfiguracionNegocio>('/configuracion')
  return data
}

export async function actualizarMargen(margen: number): Promise<ConfiguracionNegocio> {
  const { data } = await api.put<ConfiguracionNegocio>('/configuracion/margen', { margen })
  return data
}

export async function crearCotizacionDesdeCarrito(
  items: ItemCarrito[]
): Promise<Cotizacion> {
  const payload = {
    items: items.map((item) => ({
      nombre_producto: item.opcion_seleccionada.nombre_producto,
      cantidad: item.cantidad,
      tienda: item.opcion_seleccionada.tienda,
      precio_unitario: item.opcion_seleccionada.precio_con_margen ?? 0,
      margen_aplicado: item.opcion_seleccionada.margen_aplicado,
      disponible: item.opcion_seleccionada.disponible,
      es_propio: item.opcion_seleccionada.es_propio,
      url: item.opcion_seleccionada.url,
    })),
  }
  const { data } = await api.post<Cotizacion>('/cotizacion/desde-carrito', payload)
  return data
}

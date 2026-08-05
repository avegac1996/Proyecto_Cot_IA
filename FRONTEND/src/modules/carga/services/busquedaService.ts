import api from '@/shared/lib/api'
import type { BusquedaResponse, ConfiguracionNegocio, ItemCarrito, Cotizacion, OpcionProducto, OpcionEnvio, ResultadoComponente } from '@/shared/types'

export async function buscarComponentes(texto: string): Promise<BusquedaResponse> {
  const { data } = await api.post<BusquedaResponse>('/buscar', { texto })
  return data
}

export interface MensajeChat {
  role: 'user' | 'assistant'
  content: string
}

export async function preguntarAgente(
  pregunta: string,
  resultados: ResultadoComponente[],
  historial: MensajeChat[] = []
): Promise<string> {
  const { data } = await api.post<{ respuesta: string }>('/buscar/preguntar', {
    pregunta,
    resultados,
    historial: historial.map((m) => ({ role: m.role, content: m.content })),
  })
  return data.respuesta
}

export interface ImagenResponse {
  texto: string
  componentes: string[]
}

export async function identificarImagen(file: File): Promise<ImagenResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<ImagenResponse>('/buscar/imagen', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getCotizacionById(cotizacionId: number): Promise<Cotizacion> {
  const { data } = await api.get<Cotizacion>(`/cotizacion/by-id/${cotizacionId}`)
  return data
}

export async function buscarAlternativas(
  nombreProducto: string,
  tiendaExcluir: string
): Promise<OpcionProducto[]> {
  const { data } = await api.post<{ alternativas: OpcionProducto[] }>('/buscar/alternativas', {
    nombre_producto: nombreProducto,
    tienda_excluir: tiendaExcluir,
  })
  return data.alternativas
}

export async function getConfiguracion(): Promise<ConfiguracionNegocio> {
  const { data } = await api.get<ConfiguracionNegocio>('/configuracion')
  return data
}

export async function actualizarMargen(margen: number): Promise<ConfiguracionNegocio> {
  const { data } = await api.put<ConfiguracionNegocio>('/configuracion/margen', { margen })
  return data
}

export async function actualizarIva(iva: number): Promise<ConfiguracionNegocio> {
  const { data } = await api.put<ConfiguracionNegocio>('/configuracion/iva', { iva })
  return data
}

export async function getOpcionesEnvio(): Promise<OpcionEnvio[]> {
  const { data } = await api.get<OpcionEnvio[]>('/configuracion/envio')
  return data
}

export async function actualizarOpcionesEnvio(opciones: OpcionEnvio[]): Promise<OpcionEnvio[]> {
  const { data } = await api.put<OpcionEnvio[]>('/configuracion/envio', { opciones })
  return data
}

export async function getGeminiApiKey(): Promise<{ api_key: string; has_key: boolean }> {
  const { data } = await api.get<{ api_key: string; has_key: boolean }>('/configuracion/gemini-key')
  return data
}

export async function revelarGeminiApiKey(password: string): Promise<string> {
  const { data } = await api.post<{ api_key: string }>('/configuracion/gemini-key/revelar', { password })
  return data.api_key
}

export async function actualizarGeminiApiKey(apiKey: string): Promise<string> {
  const { data } = await api.put<{ api_key: string }>('/configuracion/gemini-key', { api_key: apiKey })
  return data.api_key
}

export async function crearCotizacionDesdeCarrito(
  items: ItemCarrito[],
  cotizacionId?: number,
  cliente?: { nombre: string; correo: string; celular: string },
  envio?: OpcionEnvio | null
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
    cotizacion_id: cotizacionId ?? null,
    cliente_nombre: cliente?.nombre || null,
    cliente_correo: cliente?.correo || null,
    cliente_celular: cliente?.celular || null,
    envio_nombre: envio?.nombre || null,
    envio_precio: envio?.precio ?? null,
  }
  const { data } = await api.post<Cotizacion>('/cotizacion/desde-carrito', payload)
  return data
}

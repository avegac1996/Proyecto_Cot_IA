import api from '@/shared/lib/api'
import type { Cotizacion } from '@/shared/types'

export async function generarCotizacion(sessionId: string): Promise<Cotizacion> {
  const { data } = await api.post<Cotizacion>(`/cotizacion/${sessionId}`)
  return data
}

export async function getCotizacion(sessionId: string): Promise<Cotizacion> {
  const { data } = await api.get<Cotizacion>(`/cotizacion/${sessionId}`)
  return data
}

export async function seleccionarProveedor(itemId: number, tienda: string): Promise<Cotizacion> {
  const { data } = await api.put<Cotizacion>(`/cotizacion/item/${itemId}/seleccionar`, { tienda })
  return data
}

export async function agregarItemCarrito(cotizacionId: number, texto: string): Promise<Cotizacion> {
  const { data } = await api.post<Cotizacion>(`/cotizacion/${cotizacionId}/agregar`, { texto })
  return data
}

export async function finalizarCotizacion(cotizacionId: number): Promise<Cotizacion> {
  const { data } = await api.post<Cotizacion>(`/cotizacion/${cotizacionId}/finalizar`)
  return data
}

export async function descargarPDF(cotizacionId: number): Promise<void> {
  const response = await api.get(`/cotizacion/${cotizacionId}/pdf`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `cotizacion_${cotizacionId}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export async function descargarExcel(cotizacionId: number): Promise<void> {
  const response = await api.get(`/cotizacion/${cotizacionId}/excel`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(
    new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
  )
  const link = document.createElement('a')
  link.href = url
  link.download = `cotizacion_${cotizacionId}.xlsx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export function extractCotizacionError(error: unknown): string {
  const err = error as { response?: { data?: { detail?: { message?: string; code?: string } } } }
  return err.response?.data?.detail?.message || 'Error al generar la cotización'
}

export function isAmbiguitiesPending(error: unknown): boolean {
  const err = error as { response?: { data?: { detail?: { code?: string } } } }
  return err.response?.data?.detail?.code === 'AMBIGUITIES_PENDING'
}

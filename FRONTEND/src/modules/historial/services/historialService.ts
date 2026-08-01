import api from '@/shared/lib/api'
import type { CotizacionListItem, Cotizacion } from '@/shared/types'

interface HistorialResponse {
  total: number
  page: number
  limit: number
  cotizaciones: CotizacionListItem[]
}

export async function getHistorial(page = 1, limit = 20): Promise<HistorialResponse> {
  const { data } = await api.get<HistorialResponse>('/cotizaciones', {
    params: { page, limit },
  })
  return data
}

export async function getCotizacionById(cotizacionId: number): Promise<Cotizacion> {
  const { data } = await api.get<Cotizacion>(`/cotizacion/by-id/${cotizacionId}`)
  return data
}

export async function eliminarCotizacion(cotizacionId: number): Promise<void> {
  await api.delete(`/cotizacion/${cotizacionId}`)
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

export function extractHistorialError(error: unknown): string {
  const err = error as { response?: { data?: { detail?: { message?: string } } } }
  return err.response?.data?.detail?.message || 'Error al cargar el historial'
}

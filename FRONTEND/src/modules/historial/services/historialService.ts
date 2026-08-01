import api from '@/shared/lib/api'
import type { CotizacionListItem } from '@/shared/types'

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

export function extractHistorialError(error: unknown): string {
  const err = error as { response?: { data?: { detail?: { message?: string } } } }
  return err.response?.data?.detail?.message || 'Error al cargar el historial'
}

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

export function extractCotizacionError(error: unknown): string {
  const err = error as { response?: { data?: { detail?: { message?: string; code?: string } } } }
  return err.response?.data?.detail?.message || 'Error al generar la cotización'
}

export function isAmbiguitiesPending(error: unknown): boolean {
  const err = error as { response?: { data?: { detail?: { code?: string } } } }
  return err.response?.data?.detail?.code === 'AMBIGUITIES_PENDING'
}

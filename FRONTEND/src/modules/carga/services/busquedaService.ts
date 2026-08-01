import api from '@/shared/lib/api'
import type { BusquedaResponse, ConfiguracionNegocio } from '@/shared/types'

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

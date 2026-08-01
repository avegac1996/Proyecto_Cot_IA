import api from '@/shared/lib/api'
import type { User } from '@/shared/types'
import type {
  ToggleActiveResponse,
  UsuarioCreatePayload,
  UsuarioListResponse,
} from '../types'

export async function listUsuarios(page = 1, limit = 20): Promise<UsuarioListResponse> {
  const { data } = await api.get<UsuarioListResponse>('/usuarios', {
    params: { page, limit },
  })
  return data
}

export async function createUsuario(payload: UsuarioCreatePayload): Promise<User> {
  const { data } = await api.post<User>('/usuarios', payload)
  return data
}

export async function toggleActiveUsuario(id: number): Promise<ToggleActiveResponse> {
  const { data } = await api.patch<ToggleActiveResponse>(`/usuarios/${id}/toggle-active`)
  return data
}

export function extractErrorMessage(error: unknown, fallback: string): string {
  const err = error as { response?: { data?: { detail?: { message?: string } } } }
  return err.response?.data?.detail?.message || fallback
}

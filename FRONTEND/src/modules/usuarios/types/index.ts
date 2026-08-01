import type { User } from '@/shared/types'

export interface UsuarioCreatePayload {
  username: string
  email: string
  password: string
  rol: 'admin' | 'user'
}

export interface UsuarioListResponse {
  total: number
  page: number
  limit: number
  usuarios: User[]
}

export interface ToggleActiveResponse {
  id: number
  username: string
  activo: boolean
  message: string
}

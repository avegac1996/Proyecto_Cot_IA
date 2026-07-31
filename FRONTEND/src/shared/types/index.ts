export interface User {
  id: number
  username: string
  email: string
  rol: 'admin' | 'user'
  activo: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  rol: 'admin' | 'user'
  username: string
}

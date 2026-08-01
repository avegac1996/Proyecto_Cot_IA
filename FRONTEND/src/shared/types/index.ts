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

export interface Componente {
  texto_original: string
  tipo: string
  valor: string | null
  unidad: string | null
  cantidad: number
  ambiguo: boolean
  ambiguedades: string[]
}

export interface UploadResponse {
  session_id: string
  componentes: Componente[]
  ambiguedades_detectadas: boolean
  total_componentes: number
}

export interface Pregunta {
  id: number
  categoria: string
  pregunta: string
  campo_a_desambiguar: string | null
  componentes_afectados: number[]
}

export interface PreguntasResponse {
  session_id: string
  preguntas: Pregunta[]
  total_preguntas: number
}

export interface CotizacionItem {
  id: number
  producto_nombre: string
  cantidad: number
  precio_unitario: string
  proveedor: string
  margen_aplicado: string
  subtotal: string
  disponible: boolean
}

export interface Cotizacion {
  session_id: string
  cotizacion_id: number
  items: CotizacionItem[]
  total: string
  estado: string
  fecha_creacion: string
}

export interface CotizacionListItem {
  cotizacion_id: number
  session_id: string
  estado: string
  total: string
  total_items: number
  fecha_creacion: string
}

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
  auto_completado?: boolean
  color?: string
  tamano?: string
  tipo_o_modelo?: string
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

export interface OpcionProveedor {
  tienda: string
  precio_base: number
  precio_con_margen: number
  margen_aplicado: number
  disponible: boolean
  url: string | null
  es_propio: boolean
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
  es_propio: boolean
  seleccionado: boolean
  opciones_proveedores: OpcionProveedor[]
}

export interface Cotizacion {
  session_id: string
  cotizacion_id: number
  items: CotizacionItem[]
  total: string
  estado: string
  fecha_creacion: string
  cliente_nombre: string | null
  cliente_correo: string | null
  cliente_celular: string | null
  envio_nombre: string | null
  envio_precio: string | null
}

export interface CotizacionListItem {
  cotizacion_id: number
  session_id: string
  estado: string
  total: string
  total_items: number
  fecha_creacion: string
  cliente_nombre: string | null
  usuario_nombre: string | null
}

export interface OpcionProducto {
  tienda: string
  nombre_producto: string
  precio_base: number | null
  precio_con_margen: number | null
  margen_aplicado: number
  disponible: boolean
  url: string | null
  es_propio: boolean
  es_favorita?: boolean
  variantes?: string[]
}

export interface Sugerencia {
  sugerencia: string
  razon: string
}

export interface ConfirmacionProducto {
  candidato: string | null
  pregunta: string
}

export interface ResultadoComponente {
  termino: string
  cantidad: number
  encontrado_propia: boolean
  opciones: OpcionProducto[]
  sugerencia: Sugerencia | null
  confirmacion?: ConfirmacionProducto | null
}

export interface BusquedaResponse {
  resultados: ResultadoComponente[]
}

export interface ConfiguracionNegocio {
  margen_competencia: number
  tienda_propia: string
  iva: number
}

export interface OpcionEnvio {
  id: string
  nombre: string
  precio: number
}

export interface ItemCarrito {
  termino: string
  cantidad: number
  opcion_seleccionada: OpcionProducto
}

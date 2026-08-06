import api from '@/shared/lib/api'

export interface SelectoresTienda {
  search_url?: string
  product_card?: string
  product_url?: string
  price?: string
  stock_in_classes?: boolean
  product_page_price?: string
  product_page_availability?: string
  store_path?: string
  use_wayback?: boolean
}

export interface Tienda {
  id: number
  nombre: string
  url_base: string
  usa_javascript: boolean
  activa: boolean
  es_favorita: boolean
  ttl_horas: number
  selectores: SelectoresTienda
}

export interface TiendaCreate {
  nombre: string
  url_base: string
  usa_javascript: boolean
  activa: boolean
  es_favorita: boolean
  ttl_horas: number
  selectores: SelectoresTienda
}

export interface TestScrapingResult {
  status: string
  captcha: boolean
  captcha_type: string | null
  message: string
  products_found: number
  sample_products: { nombre: string; precio: number | null }[]
  http_status: number | null
  response_length: number | null
  recommended_scraper: string | null
}

export async function getTiendas(): Promise<Tienda[]> {
  const { data } = await api.get<Tienda[]>('/tiendas')
  return data
}

export async function createTienda(tienda: TiendaCreate): Promise<Tienda> {
  const { data } = await api.post<Tienda>('/tiendas', tienda)
  return data
}

export async function updateTienda(id: number, tienda: Partial<TiendaCreate>): Promise<Tienda> {
  const { data } = await api.put<Tienda>(`/tiendas/${id}`, tienda)
  return data
}

export async function deleteTienda(id: number): Promise<void> {
  await api.delete(`/tiendas/${id}`)
}

export async function testScraping(
  url_base: string,
  usa_javascript: boolean,
  selectores: SelectoresTienda,
  query: string
): Promise<TestScrapingResult> {
  const { data } = await api.post<TestScrapingResult>('/tiendas/test-scraping', {
    url_base,
    usa_javascript,
    selectores,
    query,
  })
  return data
}

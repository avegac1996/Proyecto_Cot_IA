import { useState, useEffect, useCallback } from 'react'
import {
  Store,
  Plus,
  Trash2,
  Pencil,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
  FlaskConical,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
} from 'lucide-react'
import {
  getTiendas,
  createTienda,
  updateTienda,
  deleteTienda,
  testScraping,
  type Tienda,
  type SelectoresTienda,
  type TestScrapingResult,
} from '@/modules/admin/services/tiendaService'

const EMPTY_SELECTORES: SelectoresTienda = {
  search_url: '',
  product_card: 'li.product',
  product_url: 'h2.woocommerce-loop-product__title, h2 a, h2',
  price: '.woocommerce-Price-amount, .price ins .woocommerce-Price-amount, .price',
  stock_in_classes: true,
  product_page_price: 'p.price',
  product_page_availability: '.stock',
  store_path: '/store/',
  use_wayback: false,
}

const EMPTY_TIENDA = {
  nombre: '',
  url_base: '',
  usa_javascript: false,
  activa: true,
  ttl_horas: 24,
  selectores: { ...EMPTY_SELECTORES },
}

export default function TiendasPage() {
  const [tiendas, setTiendas] = useState<Tienda[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState(EMPTY_TIENDA)
  const [isSaving, setIsSaving] = useState(false)
  const [testResult, setTestResult] = useState<TestScrapingResult | null>(null)
  const [isTesting, setIsTesting] = useState(false)
  const [testQuery, setTestQuery] = useState('arduino')

  const cargarTiendas = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await getTiendas()
      setTiendas(data)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al cargar tiendas')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    cargarTiendas()
  }, [cargarTiendas])

  const handleNueva = () => {
    setFormData({ ...EMPTY_TIENDA, selectores: { ...EMPTY_SELECTORES } })
    setEditingId(null)
    setTestResult(null)
    setShowForm(true)
  }

  const handleEditar = (t: Tienda) => {
    setFormData({
      nombre: t.nombre,
      url_base: t.url_base,
      usa_javascript: t.usa_javascript,
      activa: t.activa,
      ttl_horas: t.ttl_horas,
      selectores: { ...EMPTY_SELECTORES, ...t.selectores },
    })
    setEditingId(t.id)
    setTestResult(null)
    setShowForm(true)
  }

  const handleEliminar = async (id: number) => {
    if (!confirm('¿Eliminar esta tienda?')) return
    try {
      await deleteTienda(id)
      await cargarTiendas()
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al eliminar')
    }
  }

  const handleGuardar = async () => {
    setIsSaving(true)
    setError(null)
    try {
      if (editingId) {
        await updateTienda(editingId, formData)
      } else {
        await createTienda(formData)
      }
      setShowForm(false)
      await cargarTiendas()
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al guardar')
    } finally {
      setIsSaving(false)
    }
  }

  const handleTest = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await testScraping(
        formData.url_base,
        formData.usa_javascript,
        formData.selectores,
        testQuery
      )
      setTestResult(result)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setTestResult({
        status: 'error',
        captcha: false,
        captcha_type: null,
        message: e.response?.data?.detail?.message || e.message || 'Error al probar scraping',
        products_found: 0,
        sample_products: [],
        http_status: null,
        response_length: null,
        recommended_scraper: null,
      })
    } finally {
      setIsTesting(false)
    }
  }

  const updateSelectores = (key: keyof SelectoresTienda, value: string | boolean) => {
    setFormData((prev) => ({
      ...prev,
      selectores: { ...prev.selectores, [key]: value },
    }))
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            <Store className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
              Gestión de Tiendas
            </h2>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
              Configura tiendas para web scraping automático
            </p>
          </div>
        </div>
        <button
          onClick={handleNueva}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <Plus className="w-4 h-4" />
          Nueva Tienda
        </button>
      </div>

      {error && (
        <div
          className="flex items-center gap-2 rounded-lg border p-3 text-sm"
          style={{ borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }}
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Lista de tiendas */}
      <div className="grid gap-3">
        {tiendas.map((t) => (
          <div
            key={t.id}
            className="rounded-xl border p-4 flex items-center justify-between"
            style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
          >
            <div className="flex items-center gap-4">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold"
                style={{
                  backgroundColor: t.activa ? '#D1FAE5' : '#FEE2E2',
                  color: t.activa ? '#065F46' : '#991B1B',
                }}
              >
                {t.nombre.charAt(0).toUpperCase()}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium" style={{ color: 'var(--color-text)' }}>
                    {t.nombre}
                  </span>
                  {t.usa_javascript && (
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: '#FEF3C7', color: '#92400E' }}
                    >
                      JS
                    </span>
                  )}
                  {t.selectores.use_wayback && (
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: '#DBEAFE', color: '#1E40AF' }}
                    >
                      Wayback
                    </span>
                  )}
                  {!t.activa && (
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: '#FEE2E2', color: '#991B1B' }}
                    >
                      Inactiva
                    </span>
                  )}
                </div>
                <a
                  href={t.url_base}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs hover:underline"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  {t.url_base}
                </a>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleEditar(t)}
                className="p-2 rounded-lg transition-colors hover:opacity-80"
                style={{ color: 'var(--color-text-muted)' }}
                title="Editar"
              >
                <Pencil className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleEliminar(t.id)}
                className="p-2 rounded-lg transition-colors hover:opacity-80"
                style={{ color: 'var(--color-danger)' }}
                title="Eliminar"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal Formulario */}
      {showForm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          onClick={() => setShowForm(false)}
        >
          <div
            className="rounded-2xl border max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-4"
            style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header modal */}
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold" style={{ color: 'var(--color-text)' }}>
                {editingId ? 'Editar Tienda' : 'Nueva Tienda'}
              </h3>
              <button onClick={() => setShowForm(false)} style={{ color: 'var(--color-text-muted)' }}>
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Campos básicos */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>
                  Nombre
                </label>
                <input
                  type="text"
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  placeholder="Ej: Megatronica"
                  className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>
                  URL base
                </label>
                <input
                  type="text"
                  value={formData.url_base}
                  onChange={(e) => setFormData({ ...formData, url_base: e.target.value })}
                  placeholder="https://tienda.cc/"
                  className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <label className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text)' }}>
                <input
                  type="checkbox"
                  checked={formData.usa_javascript}
                  onChange={(e) => setFormData({ ...formData, usa_javascript: e.target.checked })}
                />
                Usa JavaScript
              </label>
              <label className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text)' }}>
                <input
                  type="checkbox"
                  checked={formData.activa}
                  onChange={(e) => setFormData({ ...formData, activa: e.target.checked })}
                />
                Activa
              </label>
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>
                  TTL (horas)
                </label>
                <input
                  type="number"
                  min={1}
                  value={formData.ttl_horas}
                  onChange={(e) => setFormData({ ...formData, ttl_horas: parseInt(e.target.value) || 24 })}
                  className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                />
              </div>
            </div>

            {/* Selectores */}
            <div className="space-y-3 pt-2">
              <h4 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
                Selectores CSS
              </h4>

              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>
                  URL de búsqueda (usa {'{query}'} como placeholder)
                </label>
                <input
                  type="text"
                  value={formData.selectores.search_url || ''}
                  onChange={(e) => updateSelectores('search_url', e.target.value)}
                  placeholder="https://tienda.cc/?s={query}"
                  className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>
                    Selector card de producto
                  </label>
                  <input
                    type="text"
                    value={formData.selectores.product_card || ''}
                    onChange={(e) => updateSelectores('product_card', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                    style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>
                    Selector nombre/URL producto
                  </label>
                  <input
                    type="text"
                    value={formData.selectores.product_url || ''}
                    onChange={(e) => updateSelectores('product_url', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                    style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>
                    Selector precio
                  </label>
                  <input
                    type="text"
                    value={formData.selectores.price || ''}
                    onChange={(e) => updateSelectores('price', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                    style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>
                    Ruta store (para Wayback)
                  </label>
                  <input
                    type="text"
                    value={formData.selectores.store_path || ''}
                    onChange={(e) => updateSelectores('store_path', e.target.value)}
                    placeholder="/store/"
                    className="w-full px-3 py-2 rounded-lg border outline-none text-sm"
                    style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                  />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text)' }}>
                  <input
                    type="checkbox"
                    checked={formData.selectores.stock_in_classes || false}
                    onChange={(e) => updateSelectores('stock_in_classes', e.target.checked)}
                  />
                  Stock en clases CSS
                </label>
                <label className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text)' }}>
                  <input
                    type="checkbox"
                    checked={formData.selectores.use_wayback || false}
                    onChange={(e) => updateSelectores('use_wayback', e.target.checked)}
                  />
                  Usar Wayback Machine
                </label>
              </div>
            </div>

            {/* Test scraping */}
            <div className="space-y-2 pt-2 border-t" style={{ borderColor: 'var(--color-border)' }}>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
                  Probar scraping
                </h4>
                <input
                  type="text"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  className="w-32 px-2 py-1 rounded border outline-none text-sm"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}
                />
                <button
                  onClick={handleTest}
                  disabled={isTesting || !formData.url_base}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                  style={{ backgroundColor: 'var(--color-primary)' }}
                >
                  {isTesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
                  Probar
                </button>
              </div>

              {testResult && (
                <TestResultCard result={testResult} />
              )}
            </div>

            {/* Botones */}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowForm(false)}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                style={{ color: 'var(--color-text-muted)', border: '1px solid var(--color-border)' }}
              >
                Cancelar
              </button>
              <button
                onClick={handleGuardar}
                disabled={isSaving || !formData.nombre || !formData.url_base}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                style={{ backgroundColor: 'var(--color-primary)' }}
              >
                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                {editingId ? 'Actualizar' : 'Crear'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TestResultCard({ result }: { result: TestScrapingResult }) {
  const isOk = result.status === 'ok' && !result.captcha
  const isCaptchaGreen = result.status === 'captcha'
  const isError = result.status === 'error' || result.status === 'captcha_error'

  let bgColor = '#F0FDF4'
  let borderColor = '#D1FAE5'
  let textColor = '#065F46'
  let Icon = ShieldCheck

  if (isCaptchaGreen) {
    bgColor = '#F0FDF4'
    borderColor = '#86EFAC'
    textColor = '#166534'
    Icon = ShieldAlert
  } else if (isError) {
    bgColor = '#FEF2F2'
    borderColor = '#FECACA'
    textColor = '#991B1B'
    Icon = ShieldX
  }

  return (
    <div
      className="rounded-lg border p-3 space-y-2"
      style={{ backgroundColor: bgColor, borderColor, color: textColor }}
    >
      <div className="flex items-start gap-2">
        <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium">{result.message}</p>
          {result.captcha_type && (
            <p className="text-xs mt-1 opacity-80">Tipo: {result.captcha_type}</p>
          )}
          {result.http_status && (
            <p className="text-xs mt-1 opacity-80">
              HTTP {result.http_status} · {result.response_length} bytes · {result.products_found} productos
            </p>
          )}
          {result.recommended_scraper && (
            <p className="text-xs mt-1 font-medium">
              Scraper recomendado: {result.recommended_scraper}
            </p>
          )}
        </div>
      </div>

      {isOk && result.sample_products.length > 0 && (
        <div className="mt-2 space-y-1">
          {result.sample_products.map((p, i) => (
            <div key={i} className="text-xs flex justify-between px-2 py-1 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.5)' }}>
              <span>{p.nombre}</span>
              <span className="font-medium">${p.precio}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

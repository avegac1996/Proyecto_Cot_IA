import { useState, useEffect } from 'react'
import { Settings, Save, Loader2, AlertCircle, CheckCircle, Truck, Plus, Trash2, Key, Eye, EyeOff, Lock } from 'lucide-react'
import { getConfiguracion, actualizarMargen, actualizarIva, getOpcionesEnvio, actualizarOpcionesEnvio, getGeminiApiKey, actualizarGeminiApiKey, revelarGeminiApiKey } from '@/modules/carga/services/busquedaService'
import type { OpcionEnvio } from '@/shared/types'

export default function ConfiguracionPage() {
  const [margen, setMargen] = useState<number>(5)
  const [margenOriginal, setMargenOriginal] = useState<number>(5)
  const [iva, setIva] = useState<number>(15)
  const [ivaOriginal, setIvaOriginal] = useState<number>(15)
  const [tiendaPropia, setTiendaPropia] = useState<string>('')
  const [opcionesEnvio, setOpcionesEnvio] = useState<OpcionEnvio[]>([])
  const [opcionesEnvioOriginal, setOpcionesEnvioOriginal] = useState<OpcionEnvio[]>([])
  const [geminiKey, setGeminiKey] = useState<string>('')
  const [geminiKeyOriginal, setGeminiKeyOriginal] = useState<string>('')
  const [geminiKeyRevelada, setGeminiKeyRevelada] = useState<string | null>(null)
  const [mostrarPasswordModal, setMostrarPasswordModal] = useState(false)
  const [passwordInput, setPasswordInput] = useState('')
  const [verificandoPassword, setVerificandoPassword] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    cargarConfiguracion()
  }, [])

  const cargarConfiguracion = async () => {
    setIsLoading(true)
    try {
      const config = await getConfiguracion()
      setMargen(config.margen_competencia)
      setMargenOriginal(config.margen_competencia)
      setIva(config.iva)
      setIvaOriginal(config.iva)
      setTiendaPropia(config.tienda_propia)
      const envio = await getOpcionesEnvio()
      setOpcionesEnvio(envio)
      setOpcionesEnvioOriginal(envio)
      const keyResp = await getGeminiApiKey()
      setGeminiKey(keyResp.api_key)
      setGeminiKeyOriginal(keyResp.api_key)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al cargar configuración')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGuardar = async () => {
    setIsSaving(true)
    setError(null)
    setSuccess(false)
    try {
      let config = null
      if (margen !== margenOriginal) {
        config = await actualizarMargen(margen)
      }
      if (iva !== ivaOriginal) {
        config = await actualizarIva(iva)
      }
      if (config) {
        setMargenOriginal(config.margen_competencia)
        setIvaOriginal(config.iva)
      }
      const envioCambiado = JSON.stringify(opcionesEnvio) !== JSON.stringify(opcionesEnvioOriginal)
      if (envioCambiado) {
        const envio = await actualizarOpcionesEnvio(opcionesEnvio)
        setOpcionesEnvioOriginal(envio)
      }
      if (geminiKey !== geminiKeyOriginal && geminiKey.trim() && !geminiKey.includes('*')) {
        const key = await actualizarGeminiApiKey(geminiKey.trim())
        setGeminiKeyOriginal(key)
        setGeminiKeyRevelada(null)
      }
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al guardar')
    } finally {
      setIsSaving(false)
    }
  }

  const handleRevelarKey = async () => {
    setVerificandoPassword(true)
    setPasswordError(null)
    try {
      const key = await revelarGeminiApiKey(passwordInput)
      setGeminiKey(key)
      setGeminiKeyRevelada(key)
      setMostrarPasswordModal(false)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setPasswordError(e.response?.data?.detail?.message || e.message || 'Error al verificar')
    } finally {
      setVerificandoPassword(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
      </div>
    )
  }

  const geminiKeyCambiada = geminiKey !== geminiKeyOriginal && geminiKey.trim() !== '' && !geminiKey.includes('*')
  const hayCambios = margen !== margenOriginal || iva !== ivaOriginal || JSON.stringify(opcionesEnvio) !== JSON.stringify(opcionesEnvioOriginal) || geminiKeyCambiada

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <Settings className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Configuración de Negocio
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Parámetros del sistema de cotización
          </p>
        </div>
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

      {success && (
        <div
          className="flex items-center gap-2 rounded-lg border p-3 text-sm"
          style={{ borderColor: '#D1FAE5', backgroundColor: '#F0FDF4', color: '#065F46' }}
        >
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>Configuración guardada correctamente</span>
        </div>
      )}

      <div
        className="rounded-xl border p-6 space-y-4"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
            Margen de competencia (%)
          </label>
          <p className="text-xs mb-3" style={{ color: 'var(--color-text-muted)' }}>
            Porcentaje aplicado a productos de tiendas externas. Los productos de {tiendaPropia} no incluyen margen.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={0}
              max={100}
              step={0.5}
              value={margen}
              onChange={(e) => setMargen(parseFloat(e.target.value) || 0)}
              disabled={isSaving}
              className="w-32 px-3 py-2.5 rounded-lg border outline-none text-sm"
              style={{
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
            />
            <span className="text-lg font-bold" style={{ color: 'var(--color-text-muted)' }}>%</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
            IVA (%)
          </label>
          <p className="text-xs mb-3" style={{ color: 'var(--color-text-muted)' }}>
            Porcentaje de Impuesto al Valor Agregado aplicado a las cotizaciones. Se mostrará el subtotal sin IVA, el IVA y el total en el PDF.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={0}
              max={100}
              step={0.5}
              value={iva}
              onChange={(e) => setIva(parseFloat(e.target.value) || 0)}
              disabled={isSaving}
              className="w-32 px-3 py-2.5 rounded-lg border outline-none text-sm"
              style={{
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
            />
            <span className="text-lg font-bold" style={{ color: 'var(--color-text-muted)' }}>%</span>
          </div>
        </div>

        <div
          className="rounded-lg p-3 text-xs"
          style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text-muted)' }}
        >
          <p className="font-medium mb-1" style={{ color: 'var(--color-text)' }}>Tienda propia:</p>
          <p>{tiendaPropia} — los productos de esta tienda se muestran sin margen.</p>
        </div>

        {/* Opciones de envío */}
        <div className="pt-2">
          <div className="flex items-center gap-2 mb-3">
            <Truck className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
            <label className="block text-sm font-medium" style={{ color: 'var(--color-text)' }}>
              Opciones de Envío
            </label>
          </div>
          <p className="text-xs mb-3" style={{ color: 'var(--color-text-muted)' }}>
            Configura los métodos de envío y sus precios. Estos aparecerán al cliente antes de generar la cotización.
          </p>
          <div className="space-y-2">
            {opcionesEnvio.map((op, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input
                  type="text"
                  value={op.nombre}
                  onChange={(e) => {
                    const next = [...opcionesEnvio]
                    next[idx] = { ...next[idx], nombre: e.target.value }
                    setOpcionesEnvio(next)
                  }}
                  disabled={isSaving}
                  placeholder="Nombre de la opción"
                  className="flex-1 px-3 py-2 rounded-lg border outline-none text-sm"
                  style={{
                    borderColor: 'var(--color-border)',
                    backgroundColor: 'var(--color-bg)',
                    color: 'var(--color-text)',
                  }}
                />
                <div className="flex items-center gap-1">
                  <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>$</span>
                  <input
                    type="number"
                    min={0}
                    step={0.1}
                    value={op.precio}
                    onChange={(e) => {
                      const next = [...opcionesEnvio]
                      next[idx] = { ...next[idx], precio: parseFloat(e.target.value) || 0 }
                      setOpcionesEnvio(next)
                    }}
                    disabled={isSaving}
                    className="w-20 px-3 py-2 rounded-lg border outline-none text-sm"
                    style={{
                      borderColor: 'var(--color-border)',
                      backgroundColor: 'var(--color-bg)',
                      color: 'var(--color-text)',
                    }}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setOpcionesEnvio(opcionesEnvio.filter((_, i) => i !== idx))
                  }}
                  disabled={isSaving}
                  className="p-2 rounded-lg"
                  style={{ color: 'var(--color-danger)' }}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => {
              const next = [...opcionesEnvio, { id: `op_${Date.now()}`, nombre: '', precio: 0 }]
              setOpcionesEnvio(next)
            }}
            disabled={isSaving}
            className="mt-2 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={{
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-muted)',
              backgroundColor: 'transparent',
            }}
          >
            <Plus className="w-3.5 h-3.5" />
            Agregar opción
          </button>
        </div>

        {/* API Key de Gemini */}
        <div className="pt-2">
          <div className="flex items-center gap-2 mb-3">
            <Key className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
            <label className="block text-sm font-medium" style={{ color: 'var(--color-text)' }}>
              API Key de Gemini (IA)
            </label>
          </div>
          <p className="text-xs mb-3" style={{ color: 'var(--color-text-muted)' }}>
            Clave de API para Google Gemini usada en reconocimiento de imágenes y agente de chat. Si la clave expira, reemplázala aquí.
          </p>
          <div className="flex items-center gap-2">
            <input
              type={geminiKeyRevelada ? 'text' : 'password'}
              value={geminiKey}
              onChange={(e) => { setGeminiKey(e.target.value); setGeminiKeyRevelada(null) }}
              disabled={isSaving}
              placeholder="AIza..."
              className="flex-1 px-3 py-2.5 rounded-lg border outline-none text-sm font-mono"
              style={{
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text)',
              }}
            />
            <button
              type="button"
              onClick={() => {
                if (geminiKeyRevelada) {
                  setGeminiKeyRevelada(null)
                  setGeminiKey(geminiKeyOriginal)
                } else {
                  setPasswordInput('')
                  setPasswordError(null)
                  setMostrarPasswordModal(true)
                }
              }}
              disabled={isSaving}
              className="p-2.5 rounded-lg border"
              style={{
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-muted)',
              }}
              title={geminiKeyRevelada ? 'Ocultar clave' : 'Ver clave'}
            >
              {geminiKeyRevelada ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {geminiKeyRevelada && (
            <p className="text-xs mt-1" style={{ color: '#16a34a' }}>
              Clave revelada. Cámbiala si es necesario y guarda los cambios.
            </p>
          )}
        </div>

        {/* Modal de contraseña para revelar API key */}
        {mostrarPasswordModal && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            onClick={() => setMostrarPasswordModal(false)}
          >
            <div
              className="rounded-xl border p-6 w-full max-w-sm space-y-4"
              style={{
                backgroundColor: 'var(--color-surface)',
                borderColor: 'var(--color-border)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-2">
                <Lock className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
                <h3 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
                  Verificar contraseña
                </h3>
              </div>
              <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                Ingresa tu contraseña para revelar la API key de Gemini.
              </p>
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => { setPasswordInput(e.target.value); setPasswordError(null) }}
                disabled={verificandoPassword}
                placeholder="Tu contraseña"
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleRevelarKey()}
                className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm"
                style={{
                  borderColor: 'var(--color-border)',
                  backgroundColor: 'var(--color-bg)',
                  color: 'var(--color-text)',
                }}
              />
              {passwordError && (
                <p className="text-xs" style={{ color: 'var(--color-danger)' }}>{passwordError}</p>
              )}
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setMostrarPasswordModal(false)}
                  disabled={verificandoPassword}
                  className="flex-1 py-2 rounded-lg text-sm font-medium border"
                  style={{
                    borderColor: 'var(--color-border)',
                    color: 'var(--color-text-muted)',
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleRevelarKey}
                  disabled={verificandoPassword || !passwordInput}
                  className="flex-1 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-60"
                  style={{ backgroundColor: 'var(--color-primary)' }}
                >
                  {verificandoPassword ? (
                    <span className="flex items-center justify-center gap-1">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Verificando...
                    </span>
                  ) : (
                    'Revelar'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        <button
          onClick={handleGuardar}
          disabled={!hayCambios || isSaving}
          className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Guardando...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Guardar cambios
            </>
          )}
        </button>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, FileUp, Loader2, Sparkles, Info } from 'lucide-react'
import { useCotizacionStore } from '@/shared/store/cotizacionStore'
import DropZone from './components/DropZone'
import FilePreview from './components/FilePreview'
import { extractUploadError, uploadFile } from './services/uploadService'

export default function CargaPage() {
  const navigate = useNavigate()
  const setSesion = useCotizacionStore((s) => s.setSesion)
  const [file, setFile] = useState<File | null>(null)
  const [texto, setTexto] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const procesar = async (archivo: File) => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await uploadFile(archivo)
      setSesion(data.session_id, data.componentes)
      navigate(data.ambiguedades_detectadas ? '/preguntas' : '/cotizacion')
    } catch (err) {
      setError(extractUploadError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpload = () => {
    if (file) procesar(file)
  }

  const handleTexto = () => {
    const contenido = texto.trim()
    if (!contenido) return
    procesar(new File([contenido], 'lista.txt', { type: 'text/plain' }))
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <FileUp className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Carga de Componentes
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Sube tu lista en texto, audio o imagen
          </p>
        </div>
      </div>

      <DropZone onFileSelected={setFile} disabled={isLoading} />

      {file && <FilePreview file={file} onRemove={() => setFile(null)} />}

      <div className="flex items-center gap-3">
        <div className="flex-1 border-t" style={{ borderColor: 'var(--color-border)' }} />
        <span className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
          O escribe tu lista
        </span>
        <div className="flex-1 border-t" style={{ borderColor: 'var(--color-border)' }} />
      </div>

      <textarea
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        disabled={isLoading}
        rows={5}
        placeholder={'5 resistencias\n10 leds\n1 arduino\n1 sensor de temperatura\n1 motor'}
        className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm resize-y"
        style={{
          borderColor: 'var(--color-border)',
          backgroundColor: 'var(--color-surface)',
          color: 'var(--color-text)',
        }}
      />

      <button
        onClick={handleTexto}
        disabled={!texto.trim() || isLoading}
        className="w-full py-2.5 rounded-lg font-medium text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 border"
        style={{
          borderColor: 'var(--color-primary)',
          color: 'var(--color-primary)',
          backgroundColor: 'transparent',
        }}
      >
        Procesar texto
      </button>

      {error && (
        <div
          className="flex items-center gap-2 rounded-lg border p-3 text-sm"
          style={{ borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }}
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || isLoading}
        className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        style={{ backgroundColor: 'var(--color-primary)' }}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Procesando...
          </>
        ) : (
          'Procesar lista'
        )}
      </button>

      {/* Info de auto-completado */}
      <div
        className="rounded-xl border p-4 space-y-3"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
          <p className="text-xs font-bold" style={{ color: 'var(--color-text)' }}>
            Auto-completado inteligente
          </p>
        </div>
        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          El sistema completa automáticamente los valores más comunes basándose en las recomendaciones de AV Electronics:
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
            Resistencias → 220Ω 1/4W
          </div>
          <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
            LEDs → 5mm rojo
          </div>
          <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
            Arduino → UNO R3
          </div>
          <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
            Fuente → 9V DC jack+
          </div>
          <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
            Cables → Macho-Macho
          </div>
          <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }} />
            Protoboard → 830 puntos
          </div>
        </div>
        <div
          className="flex items-start gap-2 pt-2 border-t text-xs"
          style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
        >
          <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>
            Solo se preguntará sobre sensores, motores o componentes no reconocidos (máx. 2 preguntas).
            Los items sugeridos (ej: driver para motor) se agregan automáticamente a la cotización.
          </span>
        </div>
      </div>

      <div
        className="rounded-xl border p-4 text-xs"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
      >
        <p className="font-medium mb-1" style={{ color: 'var(--color-text)' }}>Formato sugerido (una línea por componente):</p>
        <p>5 resistencias de 220 ohm</p>
        <p>10 leds rojos 5mm</p>
        <p>1 arduino uno</p>
        <p>1 sensor de temperatura</p>
        <p>1 motor</p>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, FileUp, Loader2 } from 'lucide-react'
import { useCotizacionStore } from '@/shared/store/cotizacionStore'
import DropZone from './components/DropZone'
import FilePreview from './components/FilePreview'
import { extractUploadError, uploadFile } from './services/uploadService'

export default function CargaPage() {
  const navigate = useNavigate()
  const setSesion = useCotizacionStore((s) => s.setSesion)
  const [file, setFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async () => {
    if (!file) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await uploadFile(file)
      setSesion(data.session_id, data.componentes)
      navigate(data.ambiguedades_detectadas ? '/preguntas' : '/cotizacion')
    } catch (err) {
      setError(extractUploadError(err))
    } finally {
      setIsLoading(false)
    }
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
            Carga de Archivos
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Sube tu lista de componentes en texto, audio o imagen
          </p>
        </div>
      </div>

      <DropZone onFileSelected={setFile} disabled={isLoading} />

      {file && <FilePreview file={file} onRemove={() => setFile(null)} />}

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

      <div
        className="rounded-xl border p-4 text-xs"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
      >
        <p className="font-medium mb-1" style={{ color: 'var(--color-text)' }}>Formato sugerido (una línea por componente):</p>
        <p>5 resistencias de 220 ohm</p>
        <p>10 leds rojos 5mm</p>
        <p>1 arduino uno</p>
      </div>
    </div>
  )
}

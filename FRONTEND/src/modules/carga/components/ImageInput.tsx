import { useState, useRef } from 'react'
import { Image as ImageIcon, ScanText, AlertCircle, Sparkles } from 'lucide-react'
import { identificarImagen } from '../services/busquedaService'

interface Props {
  onTextExtracted: (text: string) => void
  disabled?: boolean
}

export default function ImageInput({ onTextExtracted, disabled }: Props) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [componentes, setComponentes] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Solo se permiten imágenes')
      return
    }

    setError(null)
    setComponentes([])
    setPreview(URL.createObjectURL(file))
    setIsProcessing(true)

    try {
      const response = await identificarImagen(file)
      const texto = response.texto.trim()
      if (texto) {
        setComponentes(response.componentes)
        onTextExtracted(texto)
      } else {
        setError('Gemini no identificó componentes en la imagen')
      }
    } catch (err) {
      const e = err as { response?: { data?: { detail?: { message?: string } } }; message?: string }
      setError(e.response?.data?.detail?.message || e.message || 'Error al analizar la imagen')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (disabled || isProcessing) return
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="space-y-2">
      <div
        className="rounded-lg border-2 border-dashed p-4 text-center transition-colors cursor-pointer"
        style={{
          borderColor: preview ? 'var(--color-primary)' : 'var(--color-border)',
          backgroundColor: 'var(--color-bg)',
        }}
        onClick={() => !disabled && !isProcessing && fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        {preview ? (
          <div className="space-y-2">
            <img src={preview} alt="Preview" className="max-h-32 mx-auto rounded" />
            {isProcessing ? (
              <div className="flex items-center justify-center gap-2 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                <Sparkles className="w-3 h-3 animate-pulse" style={{ color: 'var(--color-primary)' }} />
                Analizando con Gemini...
              </div>
            ) : (
              <div className="space-y-1">
                <div className="flex items-center justify-center gap-1 text-xs" style={{ color: 'var(--color-primary)' }}>
                  <ScanText className="w-3 h-3" />
                  {componentes.length} componente(s) identificado(s) — click para otra imagen
                </div>
                {componentes.length > 0 && (
                  <div className="text-left space-y-0.5 mt-2 p-2 rounded text-xs" style={{ backgroundColor: 'var(--color-surface)' }}>
                    {componentes.map((comp, i) => (
                      <div key={i} className="flex items-center gap-1" style={{ color: 'var(--color-text)' }}>
                        <span style={{ color: 'var(--color-primary)' }}>●</span> {comp}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1 py-2" style={{ color: 'var(--color-text-muted)' }}>
            <ImageIcon className="w-6 h-6" />
            <span className="text-xs">Arrastra o click para subir imagen</span>
            <span className="text-xs flex items-center gap-1" style={{ color: 'var(--color-primary)' }}>
              <Sparkles className="w-3 h-3" />
              Análisis con Google Gemini Vision
            </span>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />
      </div>

      {error && (
        <div
          className="flex items-center gap-2 rounded-lg border p-2 text-xs"
          style={{ borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }}
        >
          <AlertCircle className="w-3 h-3 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  )
}

import { useState, useRef } from 'react'
import { Image as ImageIcon, Loader2, ScanText, AlertCircle } from 'lucide-react'

interface Props {
  onTextExtracted: (text: string) => void
  disabled?: boolean
}

export default function ImageInput({ onTextExtracted, disabled }: Props) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Solo se permiten imágenes')
      return
    }

    setError(null)
    setPreview(URL.createObjectURL(file))
    setIsProcessing(true)

    try {
      const Tesseract = await import('tesseract.js')
      const { data } = await Tesseract.recognize(file, 'spa+eng', {
        logger: () => {},
      })
      const text = data.text.trim()
      if (text) {
        onTextExtracted(text)
      } else {
        setError('No se detectó texto en la imagen')
      }
    } catch {
      setError('Error al procesar la imagen con OCR')
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
                <Loader2 className="w-3 h-3 animate-spin" />
                Extrayendo texto...
              </div>
            ) : (
              <div className="flex items-center justify-center gap-1 text-xs" style={{ color: 'var(--color-primary)' }}>
                <ScanText className="w-3 h-3" />
                Texto extraído — click para otra imagen
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1 py-2" style={{ color: 'var(--color-text-muted)' }}>
            <ImageIcon className="w-6 h-6" />
            <span className="text-xs">Arrastra o click para subir imagen</span>
            <span className="text-xs opacity-60">OCR con Tesseract.js (español + inglés)</span>
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

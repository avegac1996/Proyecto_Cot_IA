import { useCallback, useState } from 'react'
import { FileAudio, FileImage, FileText, UploadCloud } from 'lucide-react'
import { detectarTipo } from '../services/uploadService'

interface Props {
  onFileSelected: (file: File) => void
  disabled?: boolean
}

export default function DropZone({ onFileSelected, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) return
      if (!detectarTipo(file.name)) {
        setError('Formato no soportado. Use: .txt, .csv, .mp3, .wav, .m4a, .ogg, .jpg, .png, .webp')
        return
      }
      setError(null)
      onFileSelected(file)
    },
    [onFileSelected]
  )

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          if (!disabled) handleFile(e.dataTransfer.files[0])
        }}
        className="rounded-xl border-2 border-dashed p-10 text-center transition-colors cursor-pointer"
        style={{
          borderColor: isDragging ? 'var(--color-primary)' : 'var(--color-border)',
          backgroundColor: isDragging ? 'var(--color-bg)' : 'var(--color-surface)',
          opacity: disabled ? 0.6 : 1,
        }}
        onClick={() => {
          if (disabled) return
          const input = document.createElement('input')
          input.type = 'file'
          input.accept = '.txt,.csv,.mp3,.wav,.m4a,.ogg,.jpg,.jpeg,.png,.webp'
          input.onchange = () => handleFile(input.files?.[0])
          input.click()
        }}
      >
        <UploadCloud className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--color-primary)' }} />
        <p className="font-medium mb-1" style={{ color: 'var(--color-text)' }}>
          Arrastra tu lista de componentes aquí
        </p>
        <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
          o haz clic para seleccionar un archivo
        </p>
        <div className="flex justify-center gap-4 text-xs" style={{ color: 'var(--color-text-muted)' }}>
          <span className="flex items-center gap-1"><FileText className="w-4 h-4" /> Texto (.txt, .csv)</span>
          <span className="flex items-center gap-1"><FileAudio className="w-4 h-4" /> Audio (.mp3, .wav)</span>
          <span className="flex items-center gap-1"><FileImage className="w-4 h-4" /> Imagen (.jpg, .png)</span>
        </div>
      </div>
      {error && (
        <p className="mt-2 text-sm" style={{ color: 'var(--color-danger)' }}>{error}</p>
      )}
    </div>
  )
}

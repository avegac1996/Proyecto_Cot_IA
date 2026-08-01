import { FileText, X } from 'lucide-react'

interface Props {
  file: File
  onRemove: () => void
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function FilePreview({ file, onRemove }: Props) {
  return (
    <div
      className="flex items-center gap-3 rounded-xl border p-4"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <FileText className="w-8 h-8 flex-shrink-0" style={{ color: 'var(--color-primary)' }} />
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate" style={{ color: 'var(--color-text)' }}>
          {file.name}
        </p>
        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          {formatSize(file.size)}
        </p>
      </div>
      <button
        onClick={onRemove}
        className="p-1.5 rounded-lg transition-colors"
        style={{ color: 'var(--color-danger)' }}
        title="Quitar archivo"
      >
        <X className="w-5 h-5" />
      </button>
    </div>
  )
}

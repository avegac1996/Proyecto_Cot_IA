import { useState, useRef } from 'react'
import { FileText, Loader2, AlertCircle, Upload } from 'lucide-react'

interface Props {
  onTextExtracted: (text: string) => void
  disabled?: boolean
}

export default function FileInput({ onTextExtracted, disabled }: Props) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    setError(null)
    setFileName(file.name)
    setIsProcessing(true)

    try {
      const ext = file.name.split('.').pop()?.toLowerCase()
      let text = ''

      if (ext === 'pdf') {
        const pdfjs = await import('pdfjs-dist')
        const pdfjsWorker = await import('pdfjs-dist/build/pdf.worker.min.mjs')
        pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker.default
        const arrayBuffer = await file.arrayBuffer()
        const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i)
          const content = await page.getTextContent()
          text += content.items.map((item) => ('str' in item ? item.str : '')).join(' ') + '\n'
        }
      } else if (ext === 'docx') {
        const mammoth = await import('mammoth')
        const arrayBuffer = await file.arrayBuffer()
        const result = await mammoth.extractRawText({ arrayBuffer })
        text = result.value
      } else if (ext === 'xlsx' || ext === 'xls') {
        const XLSX = await import('xlsx')
        const arrayBuffer = await file.arrayBuffer()
        const workbook = XLSX.read(arrayBuffer, { type: 'array' })
        for (const sheetName of workbook.SheetNames) {
          const sheet = workbook.Sheets[sheetName]
          text += XLSX.utils.sheet_to_txt(sheet) + '\n'
        }
      } else if (ext === 'txt' || ext === 'csv') {
        text = await file.text()
      } else {
        setError(`Formato .${ext} no soportado. Use: PDF, DOCX, XLSX, TXT, CSV`)
        setIsProcessing(false)
        return
      }

      text = text.trim()
      if (text) {
        onTextExtracted(text)
      } else {
        setError('No se extrajo texto del archivo')
      }
    } catch {
      setError('Error al procesar el archivo')
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
          borderColor: fileName ? 'var(--color-primary)' : 'var(--color-border)',
          backgroundColor: 'var(--color-bg)',
        }}
        onClick={() => !disabled && !isProcessing && fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        {fileName ? (
          <div className="space-y-1">
            <div className="flex items-center justify-center gap-2 text-xs" style={{ color: 'var(--color-text)' }}>
              <FileText className="w-4 h-4" />
              <span className="truncate max-w-48">{fileName}</span>
            </div>
            {isProcessing ? (
              <div className="flex items-center justify-center gap-2 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                <Loader2 className="w-3 h-3 animate-spin" />
                Extrayendo texto...
              </div>
            ) : (
              <div className="text-xs" style={{ color: 'var(--color-primary)' }}>
                Texto extraído — click para otro archivo
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1 py-2" style={{ color: 'var(--color-text-muted)' }}>
            <Upload className="w-6 h-6" />
            <span className="text-xs">Arrastra o click para subir archivo</span>
            <span className="text-xs opacity-60">PDF, DOCX, XLSX, TXT, CSV</span>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.xlsx,.xls,.txt,.csv"
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

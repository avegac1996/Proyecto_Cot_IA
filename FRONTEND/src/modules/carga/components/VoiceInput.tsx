import { Mic, Square, Loader2 } from 'lucide-react'
import { useSpeechRecognition } from '@/shared/hooks/useSpeechRecognition'

interface Props {
  onTranscript: (text: string) => void
  disabled?: boolean
}

export default function VoiceInput({ onTranscript, disabled }: Props) {
  const { isListening, transcript, error, isSupported, startListening, stopListening, resetTranscript } =
    useSpeechRecognition()

  if (!isSupported) {
    return (
      <div
        className="flex items-center gap-2 rounded-lg border p-3 text-xs"
        style={{
          borderColor: 'var(--color-border)',
          color: 'var(--color-text-muted)',
        }}
      >
        <Mic className="w-4 h-4" />
        Reconocimiento de voz no disponible en este navegador
      </div>
    )
  }

  const handleToggle = () => {
    if (isListening) {
      stopListening()
      if (transcript) {
        onTranscript(transcript)
        resetTranscript()
      }
    } else {
      startListening()
    }
  }

  return (
    <div className="space-y-2">
      <button
        onClick={handleToggle}
        disabled={disabled}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        style={{
          backgroundColor: isListening ? 'var(--color-danger)' : 'var(--color-surface)',
          color: isListening ? '#fff' : 'var(--color-text)',
          border: `1px solid ${isListening ? 'var(--color-danger)' : 'var(--color-border)'}`,
        }}
      >
        {isListening ? (
          <>
            <Square className="w-4 h-4" />
            Detener y usar texto
          </>
        ) : (
          <>
            <Mic className="w-4 h-4" />
            Hablar
          </>
        )}
      </button>

      {isListening && (
        <div
          className="flex items-center gap-2 rounded-lg border p-2 text-xs"
          style={{
            borderColor: 'var(--color-primary)',
            backgroundColor: 'var(--color-bg)',
            color: 'var(--color-text)',
          }}
        >
          <Loader2 className="w-3 h-3 animate-spin" style={{ color: 'var(--color-primary)' }} />
          <span className="truncate">{transcript || 'Escuchando...'}</span>
        </div>
      )}

      {error && (
        <div
          className="rounded-lg border p-2 text-xs"
          style={{
            borderColor: 'var(--color-danger)',
            color: 'var(--color-danger)',
          }}
        >
          {error}
        </div>
      )}
    </div>
  )
}

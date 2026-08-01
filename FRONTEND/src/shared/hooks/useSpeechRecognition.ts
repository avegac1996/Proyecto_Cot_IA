import { useState, useRef, useCallback, useEffect } from 'react'

interface SpeechRecognitionEvent extends Event {
  results: {
    length: number
    [index: number]: {
      length: number
      [index: number]: { transcript: string; confidence: number }
      isFinal: boolean
    }
  }
  resultIndex: number
}

interface SpeechRecognitionType extends EventTarget {
  lang: string
  continuous: boolean
  interimResults: boolean
  start(): void
  stop(): void
  abort(): void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: Event) => void) | null
  onend: (() => void) | null
}

declare global {
  interface Window {
    SpeechRecognition?: { new (): SpeechRecognitionType }
    webkitSpeechRecognition?: { new (): SpeechRecognitionType }
  }
}

export function useSpeechRecognition(onEnd?: (finalTranscript: string) => void) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionType | null>(null)
  const onEndRef = useRef(onEnd)
  const transcriptRef = useRef('')

  useEffect(() => {
    onEndRef.current = onEnd
  }, [onEnd])

  const isSupported =
    typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition)

  useEffect(() => {
    if (!isSupported) return

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition!
    const recognition = new SR()
    recognition.lang = 'es-ES'
    recognition.continuous = false
    recognition.interimResults = true

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let text = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        text += event.results[i][0].transcript
      }
      transcriptRef.current = text
      setTranscript(text)
    }

    recognition.onerror = (event: Event) => {
      const e = event as { error?: string }
      if (e.error === 'not-allowed') {
        setError('Permiso de micrófono denegado')
      } else if (e.error === 'no-speech') {
        setError('No se detectó voz')
      } else {
        setError('Error de reconocimiento de voz')
      }
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
      if (transcriptRef.current && onEndRef.current) {
        onEndRef.current(transcriptRef.current)
      }
    }

    recognitionRef.current = recognition

    return () => {
      recognition.abort()
    }
  }, [isSupported])

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return
    setError(null)
    setTranscript('')
    transcriptRef.current = ''
    try {
      recognitionRef.current.start()
      setIsListening(true)
    } catch {
      // Already started
    }
  }, [])

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return
    recognitionRef.current.stop()
    setIsListening(false)
  }, [])

  const resetTranscript = useCallback(() => {
    setTranscript('')
    transcriptRef.current = ''
    setError(null)
  }, [])

  return {
    isListening,
    transcript,
    error,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  }
}

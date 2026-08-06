import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Bot, User, Sparkles } from 'lucide-react'
import type { ResultadoComponente } from '@/shared/types'
import { preguntarAgente, type MensajeChat } from '../services/busquedaService'

interface Props {
  resultados: ResultadoComponente[]
  terminoBusqueda?: string
  preguntaInicial?: string | null
  onPreguntaConsumida?: () => void
}

export default function AgenteChat({ resultados, terminoBusqueda, preguntaInicial, onPreguntaConsumida }: Props) {
  const [mensajes, setMensajes] = useState<MensajeChat[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [mensajes, isLoading])

  const enviarMensaje = async (texto: string, historialPrevio?: MensajeChat[]) => {
    const base = historialPrevio ?? mensajes
    const nuevosMensajes = [...base, { role: 'user' as const, content: texto }]
    setMensajes(nuevosMensajes)
    setIsLoading(true)

    try {
      const respuesta = await preguntarAgente(texto, resultados, nuevosMensajes)
      setMensajes((prev) => [...prev, { role: 'assistant', content: respuesta }])
    } catch {
      setMensajes((prev) => [
        ...prev,
        { role: 'assistant', content: 'Lo siento, no pude procesar tu pregunta. Intenta de nuevo.' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  // Auto-enviar pregunta inicial (ej: componente no encontrado)
  useEffect(() => {
    if (preguntaInicial) {
      onPreguntaConsumida?.()
      enviarMensaje(preguntaInicial)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preguntaInicial])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    setInput('')
    await enviarMensaje(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const inputStyle = {
    backgroundColor: 'var(--color-bg)',
    border: '1px solid var(--color-border)',
    color: 'var(--color-text)',
  }

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 border-b flex items-center gap-2"
        style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)' }}
      >
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <div>
          <h3 className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
            Asistente IA
          </h3>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            {resultados.length > 0
              ? 'Pregunta sobre los componentes encontrados'
              : terminoBusqueda
                ? `Pregunta sobre: "${terminoBusqueda}"`
                : 'Pregunta sobre tu búsqueda'}
          </p>
        </div>
      </div>

      {/* Messages */}
      {mensajes.length > 0 && (
        <div ref={scrollRef} className="max-h-64 overflow-y-auto px-4 py-3 space-y-3">
          {mensajes.map((msg, idx) => (
            <div key={idx} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                style={{
                  backgroundColor: msg.role === 'user' ? 'var(--color-bg)' : 'var(--color-primary)',
                }}
              >
                {msg.role === 'user' ? (
                  <User className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
                ) : (
                  <Bot className="w-4 h-4 text-white" />
                )}
              </div>
              <div
                className="rounded-lg px-3 py-2 text-sm max-w-[80%] whitespace-pre-wrap"
                style={{
                  backgroundColor: msg.role === 'user' ? 'var(--color-primary)' : 'var(--color-bg)',
                  color: msg.role === 'user' ? '#fff' : 'var(--color-text)',
                }}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-2.5">
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                style={{ backgroundColor: 'var(--color-primary)' }}
              >
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div
                className="rounded-lg px-3 py-2 flex items-center"
                style={{ backgroundColor: 'var(--color-bg)' }}
              >
                <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--color-text-muted)' }} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Input */}
      <div className="p-3 border-t" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={resultados.length > 0
              ? "Ej: ¿Cuál es la diferencia entre estos sensores?"
              : "Ej: ¿Qué componente me recomiendas buscar?"}
            className="flex-1 px-3 py-2 rounded-lg text-sm outline-none"
            style={inputStyle}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="px-3 py-2 rounded-lg text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  )
}

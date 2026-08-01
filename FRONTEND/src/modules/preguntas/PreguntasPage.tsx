import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, CheckCircle, Loader2, MessagesSquare } from 'lucide-react'
import { useCotizacionStore } from '@/shared/store/cotizacionStore'
import type { Pregunta } from '@/shared/types'
import QuestionCard from './components/QuestionCard'
import { enviarRespuestas, extractPreguntasError, getPreguntas } from './services/preguntasService'

export default function PreguntasPage() {
  const navigate = useNavigate()
  const { sessionId, componentes } = useCotizacionStore()
  const [preguntas, setPreguntas] = useState<Pregunta[]>([])
  const [respuestas, setRespuestas] = useState<Record<number, string>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      setIsLoading(false)
      return
    }
    getPreguntas(sessionId)
      .then((data) => setPreguntas(data.preguntas))
      .catch((err) => setError(extractPreguntasError(err)))
      .finally(() => setIsLoading(false))
  }, [sessionId])

  const handleSubmit = async () => {
    if (!sessionId) return
    const payload = preguntas
      .filter((p) => respuestas[p.id]?.trim())
      .map((p) => ({ pregunta_id: p.id, respuesta: respuestas[p.id].trim() }))

    if (payload.length < preguntas.length) {
      setError('Responde todas las preguntas para continuar')
      return
    }

    setIsSending(true)
    setError(null)
    try {
      await enviarRespuestas(sessionId, payload)
      navigate('/cotizacion')
    } catch (err) {
      setError(extractPreguntasError(err))
    } finally {
      setIsSending(false)
    }
  }

  if (!sessionId) {
    return (
      <div
        className="rounded-xl border p-12 text-center"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
      >
        <MessagesSquare className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--color-text-muted)' }} />
        <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--color-text)' }}>
          No hay una sesión activa
        </h2>
        <p className="text-sm mb-6" style={{ color: 'var(--color-text-muted)' }}>
          Primero carga una lista de componentes para iniciar una cotización
        </p>
        <button
          onClick={() => navigate('/carga')}
          className="px-5 py-2.5 rounded-lg font-medium text-white text-sm"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          Ir a Carga
        </button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <MessagesSquare className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Preguntas de Aclaración
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Detectamos {componentes.filter((c) => c.ambiguo).length} componente(s) con datos faltantes
          </p>
        </div>
      </div>

      {preguntas.length === 0 ? (
        <div
          className="rounded-xl border p-8 text-center"
          style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
        >
          <CheckCircle className="w-10 h-10 mx-auto mb-3" style={{ color: '#16a34a' }} />
          <p className="font-medium mb-1" style={{ color: 'var(--color-text)' }}>
            No hay ambigüedades pendientes
          </p>
          <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
            Tu lista está completa, puedes generar la cotización
          </p>
          <button
            onClick={() => navigate('/cotizacion')}
            className="px-5 py-2.5 rounded-lg font-medium text-white text-sm"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            Ir a Cotización
          </button>
        </div>
      ) : (
        <>
          {preguntas.map((p) => (
            <QuestionCard
              key={p.id}
              pregunta={p}
              value={respuestas[p.id] ?? ''}
              onChange={(v) => setRespuestas((prev) => ({ ...prev, [p.id]: v }))}
              disabled={isSending}
            />
          ))}

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
            onClick={handleSubmit}
            disabled={isSending}
            className="w-full py-2.5 rounded-lg font-medium text-white text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            {isSending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Enviando respuestas...
              </>
            ) : (
              'Confirmar respuestas'
            )}
          </button>
        </>
      )}
    </div>
  )
}

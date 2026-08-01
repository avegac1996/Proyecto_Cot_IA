import api from '@/shared/lib/api'
import type { PreguntasResponse } from '@/shared/types'

export interface RespuestasResponse {
  session_id: string
  componentes_actualizados: boolean
  ambiguedades_restantes: number
}

export async function getPreguntas(sessionId: string): Promise<PreguntasResponse> {
  const { data } = await api.get<PreguntasResponse>(`/preguntas/${sessionId}`)
  return data
}

export async function enviarRespuestas(
  sessionId: string,
  respuestas: { pregunta_id: number; respuesta: string }[]
): Promise<RespuestasResponse> {
  const { data } = await api.post<RespuestasResponse>(
    `/preguntas/${sessionId}/respuestas`,
    { respuestas }
  )
  return data
}

export function extractPreguntasError(error: unknown): string {
  const err = error as { response?: { data?: { detail?: { message?: string } } } }
  return err.response?.data?.detail?.message || 'Error al procesar las preguntas'
}

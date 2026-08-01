import api from '@/shared/lib/api'
import type { UploadResponse } from '@/shared/types'

const EXTENSIONES_TIPO: Record<string, string> = {
  '.txt': 'texto',
  '.csv': 'texto',
  '.mp3': 'audio',
  '.wav': 'audio',
  '.m4a': 'audio',
  '.ogg': 'audio',
  '.jpg': 'imagen',
  '.jpeg': 'imagen',
  '.png': 'imagen',
  '.webp': 'imagen',
}

export function detectarTipo(filename: string): string | null {
  const ext = '.' + filename.toLowerCase().split('.').pop()
  return EXTENSIONES_TIPO[ext] ?? null
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const tipo = detectarTipo(file.name)
  if (!tipo) {
    throw new Error('Tipo de archivo no soportado')
  }
  const formData = new FormData()
  formData.append('file', file)
  formData.append('tipo', tipo)

  const { data } = await api.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export function extractUploadError(error: unknown): string {
  const err = error as { response?: { data?: { detail?: { message?: string } } }; message?: string }
  return err.response?.data?.detail?.message || err.message || 'Error al cargar el archivo'
}

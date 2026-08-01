import { HelpCircle } from 'lucide-react'
import type { Pregunta } from '@/shared/types'

interface Props {
  pregunta: Pregunta
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export default function QuestionCard({ pregunta, value, onChange, disabled }: Props) {
  return (
    <div
      className="rounded-xl border p-4"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <div className="flex items-start gap-3 mb-3">
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          <HelpCircle className="w-4 h-4 text-white" />
        </div>
        <div>
          <span
            className="inline-block px-2 py-0.5 rounded text-xs font-medium mb-1"
            style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text-muted)' }}
          >
            {pregunta.categoria}
          </span>
          <p className="text-sm font-medium" style={{ color: 'var(--color-text)' }}>
            {pregunta.pregunta}
          </p>
        </div>
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="Escribe tu respuesta..."
        className="w-full px-3 py-2.5 rounded-lg border outline-none text-sm"
        style={{
          borderColor: 'var(--color-border)',
          backgroundColor: 'var(--color-bg)',
          color: 'var(--color-text)',
        }}
      />
    </div>
  )
}

import { create } from 'zustand'
import type { Componente, Cotizacion } from '@/shared/types'

interface CotizacionState {
  sessionId: string | null
  componentes: Componente[]
  cotizacion: Cotizacion | null
  setSesion: (sessionId: string, componentes: Componente[]) => void
  setComponentes: (componentes: Componente[]) => void
  setCotizacion: (cotizacion: Cotizacion | null) => void
  reset: () => void
}

export const useCotizacionStore = create<CotizacionState>((set) => ({
  sessionId: null,
  componentes: [],
  cotizacion: null,

  setSesion: (sessionId, componentes) =>
    set({ sessionId, componentes, cotizacion: null }),

  setComponentes: (componentes) => set({ componentes }),

  setCotizacion: (cotizacion) => set({ cotizacion }),

  reset: () => set({ sessionId: null, componentes: [], cotizacion: null }),
}))

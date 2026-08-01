import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuthStore } from '@/shared/store/authStore'
import LoginPage from '@/modules/login/LoginPage'
import AppShell from '@/app/AppShell'

const CargaPage = lazy(() => import('@/modules/carga/CargaPage'))
const PreguntasPage = lazy(() => import('@/modules/preguntas/PreguntasPage'))
const CotizacionPage = lazy(() => import('@/modules/cotizacion/CotizacionPage'))
const HistorialPage = lazy(() => import('@/modules/historial/HistorialPage'))
const UsuariosPage = lazy(() => import('@/modules/usuarios/UsuariosPage'))

function PageFallback() {
  return (
    <div className="flex justify-center py-16">
      <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-primary)' }} />
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user)
  if (user?.rol !== 'admin') return <Navigate to="/carga" replace />
  return <>{children}</>
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Navigate to="/carga" replace />} />
          <Route path="/carga" element={<Suspense fallback={<PageFallback />}><CargaPage /></Suspense>} />
          <Route path="/preguntas" element={<Suspense fallback={<PageFallback />}><PreguntasPage /></Suspense>} />
          <Route path="/cotizacion" element={<Suspense fallback={<PageFallback />}><CotizacionPage /></Suspense>} />
          <Route path="/historial" element={<Suspense fallback={<PageFallback />}><HistorialPage /></Suspense>} />
          <Route
            path="/usuarios"
            element={
              <AdminRoute>
                <Suspense fallback={<PageFallback />}><UsuariosPage /></Suspense>
              </AdminRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

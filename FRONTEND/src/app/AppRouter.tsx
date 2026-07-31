import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/shared/store/authStore'
import LoginPage from '@/modules/login/LoginPage'
import HomePage from '@/app/HomePage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

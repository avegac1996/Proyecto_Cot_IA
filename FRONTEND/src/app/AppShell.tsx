import { Outlet } from 'react-router-dom'
import Header from '@/modules/header/Header'
import Footer from '@/modules/footer/Footer'

export default function AppShell() {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--color-bg)' }}>
      <Header />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

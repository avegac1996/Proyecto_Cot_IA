import { Outlet } from 'react-router-dom'
import Sidebar from '@/modules/header/Header'
import Footer from '@/modules/footer/Footer'

export default function AppShell() {
  return (
    <div
      className="min-h-screen p-4 pt-20 md:pt-6 md:p-6"
      style={{ backgroundColor: 'var(--color-bg)' }}
    >
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-6 items-start">
        <Sidebar />
        <div
          className="flex-1 min-w-0 flex flex-col min-h-[calc(100vh-3rem)]"
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)',
            overflow: 'hidden',
          }}
        >
          <main className="flex-1 p-6 md:p-8">
            <Outlet />
          </main>
          <Footer />
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  FileUp,
  History,
  Users,
  Settings,
  Store,
  Menu,
  X,
} from 'lucide-react'
import { useAuthStore } from '@/shared/store/authStore'
import ThemeToggle from './ThemeToggle'
import UserMenu from './UserMenu'

const TABS = [
  { to: '/carga', label: 'Carga', icon: FileUp },
  { to: '/historial', label: 'Historial', icon: History },
]

const ADMIN_TABS = [
  { to: '/usuarios', label: 'Usuarios', icon: Users },
  { to: '/admin/tiendas', label: 'Tiendas', icon: Store },
  { to: '/admin/configuracion', label: 'Config', icon: Settings },
]

export default function Header() {
  const user = useAuthStore((s) => s.user)
  const tabs = user?.rol === 'admin' ? [...TABS, ...ADMIN_TABS] : TABS
  const [mobileOpen, setMobileOpen] = useState(false)

  const sidebarContent = (
    <>
      {/* Logo + brand */}
      <div className="mb-6">
        <img
          src="/logo.png"
          alt="AV Electronics"
          className="h-12 w-auto object-contain mb-3"
        />
        <p
          className="text-xs font-bold uppercase tracking-wider"
          style={{ color: 'var(--color-text-muted)' }}
        >
          AV Electronics
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1.5">
        <p
          className="text-xs font-semibold uppercase tracking-wider mb-2"
          style={{ color: 'var(--color-text-muted)' }}
        >
          Menú
        </p>
        {tabs.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setMobileOpen(false)}
            className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all"
            style={({ isActive }) => ({
              color: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)',
              backgroundColor: isActive ? 'var(--color-primary-light)' : 'transparent',
            })}
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom controls */}
      <div className="pt-4 mt-4 border-t flex flex-col gap-3" style={{ borderColor: 'var(--color-border)' }}>
        <ThemeToggle />
        <UserMenu />
      </div>
    </>
  )

  const sidebarStyle: React.CSSProperties = {
    backgroundColor: 'var(--color-sidebar)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow)',
    padding: '24px',
  }

  return (
    <>
      {/* Mobile top bar */}
      <div
        className="md:hidden fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 py-3"
        style={{
          backgroundColor: 'var(--color-sidebar)',
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        <div className="flex items-center gap-2">
          <img src="/logo.png" alt="AV Electronics" className="h-8 w-auto object-contain" />
          <span
            className="text-xs font-bold uppercase tracking-wider"
            style={{ color: 'var(--color-text-muted)' }}
          >
            AV Electronics
          </span>
        </div>
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg"
          style={{ color: 'var(--color-text)', backgroundColor: 'var(--color-bg)' }}
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Desktop sidebar */}
      <aside
        className="hidden md:flex flex-col w-64 shrink-0 sticky top-6"
        style={{ ...sidebarStyle, maxHeight: 'calc(100vh - 3rem)' }}
      >
        {sidebarContent}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0"
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            onClick={() => setMobileOpen(false)}
          />
          <aside
            className="relative flex flex-col w-72 max-w-[85vw] h-full overflow-y-auto"
            style={sidebarStyle}
          >
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute top-4 right-4 p-1.5 rounded-lg"
              style={{ color: 'var(--color-text-muted)' }}
              aria-label="Cerrar menú"
            >
              <X className="w-5 h-5" />
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  )
}

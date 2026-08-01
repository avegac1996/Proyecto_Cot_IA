import { NavLink } from 'react-router-dom'
import {
  FileUp,
  MessagesSquare,
  FileText,
  History,
  Users,
} from 'lucide-react'
import { useAuthStore } from '@/shared/store/authStore'
import ThemeToggle from './ThemeToggle'
import UserMenu from './UserMenu'

const TABS = [
  { to: '/carga', label: 'Carga', icon: FileUp },
  { to: '/preguntas', label: 'Preguntas', icon: MessagesSquare },
  { to: '/cotizacion', label: 'Cotización', icon: FileText },
  { to: '/historial', label: 'Historial', icon: History },
]

const ADMIN_TABS = [{ to: '/usuarios', label: 'Usuarios', icon: Users }]

export default function Header() {
  const user = useAuthStore((s) => s.user)
  const tabs = user?.rol === 'admin' ? [...TABS, ...ADMIN_TABS] : TABS

  return (
    <header
      className="sticky top-0 z-40 border-b"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <div className="max-w-7xl mx-auto px-4 flex items-center gap-4 h-16">
        <NavLink to="/carga" className="flex items-center gap-2 shrink-0">
          <img
            src="/logo.png"
            alt="AV Electronics"
            className="h-10 w-auto object-contain"
          />
        </NavLink>

        <nav className="flex-1 flex items-center gap-1 overflow-x-auto">
          {tabs.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors"
              style={({ isActive }) => ({
                color: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)',
                backgroundColor: isActive ? 'var(--color-bg)' : 'transparent',
              })}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden lg:inline">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2 shrink-0">
          <ThemeToggle />
          <UserMenu />
        </div>
      </div>
    </header>
  )
}

export default function Footer() {
  return (
    <footer
      className="px-6 md:px-8 py-4 border-t"
      style={{ borderColor: 'var(--color-border)' }}
    >
      <div
        className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs"
        style={{ color: 'var(--color-text-muted)' }}
      >
        <p>AV Electronics — Sistema Inteligente de Cotización de Componentes Electrónicos</p>
        <p>v1.0.0 · © 2026</p>
      </div>
    </footer>
  )
}

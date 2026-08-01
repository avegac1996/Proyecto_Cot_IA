export default function Footer() {
  return (
    <footer
      className="border-t py-4"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <div
        className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs"
        style={{ color: 'var(--color-text-muted)' }}
      >
        <p>CotIA — Sistema Inteligente de Cotización de Componentes Electrónicos</p>
        <p>v1.0.0 · © 2026</p>
      </div>
    </footer>
  )
}

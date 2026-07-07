import { useEffect } from 'react'
import { X } from 'lucide-react'

export function TenderFullscreenWorkspace({ mode, title, subtitle, onClose, children }) {
  useEffect(() => {
    if (!mode) return undefined

    const previousOverflow = document.body.style.overflow
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose?.()
      }
    }

    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [mode, onClose])

  if (!mode) return null

  return (
    <div
      className="fullscreen-workspace-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose?.()
      }}
      role="presentation"
    >
      <section
        aria-label={title}
        aria-modal="true"
        className={`fullscreen-workspace ${mode}`}
        role="dialog"
      >
        <header className="fullscreen-workspace-header">
          <div className="fullscreen-workspace-title">
            <span>{subtitle}</span>
            <strong>{title}</strong>
          </div>
          <button
            aria-label="Закрыть полноэкранный режим"
            className="icon-button fullscreen-workspace-close"
            onClick={onClose}
            title="Закрыть"
            type="button"
          >
            <X size={18} />
          </button>
        </header>
        <div className="fullscreen-workspace-body">{children}</div>
      </section>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store/useStore'
import { Info, X, Loader2 } from 'lucide-react'

export const ResultModal: React.FC = () => {
  const { t } = useTranslation()
  const { activeInterpretation, isInterpreting, interpretationToken, setActiveInterpretation } = useStore()
  // Si el usuario cierra el modal mientras la IA todavía está pensando, no debe reabrirse
  // solo porque una interpretación vieja en segundo plano termine de resolver. Se resetea con
  // interpretationToken, que solo avanza en acciones explícitas del usuario (nuevo análisis o
  // reproducir un ítem del historial) — nunca por la resolución async de un fetch en curso.
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    setDismissed(false)
  }, [interpretationToken])

  const shouldShow = !dismissed && (isInterpreting || !!activeInterpretation)
  if (!shouldShow) return null

  const handleClose = () => {
    setDismissed(true)
    setActiveInterpretation(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal Container */}
      <div className="relative glass-panel w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#16171d]">
          <h3 className="font-bold text-lg text-white font-outfit flex items-center gap-2">
            <Info className="h-5 w-5 text-teal-400" />
            {t('modal.title')}
          </h3>
          <button
            onClick={handleClose}
            className="p-1 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal content */}
        <div className="p-6 overflow-y-auto leading-relaxed text-sm text-gray-300 whitespace-pre-wrap max-h-[60vh] custom-scroll">
          {activeInterpretation ? (
            activeInterpretation
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-gray-400">
              <Loader2 className="h-7 w-7 animate-spin text-teal-400" />
              <p className="text-sm font-medium">{t('modal.loading')}</p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 px-6 py-4 border-t border-white/5 bg-[#16171d]">
          <button
            onClick={handleClose}
            className="btn btn-sm btn-ghost hover:bg-white/5 text-white rounded-xl px-4"
          >
            {t('modal.close')}
          </button>
        </div>
      </div>
    </div>
  )
}

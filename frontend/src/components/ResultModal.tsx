import React from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store/useStore'
import { Info, X } from 'lucide-react'

export const ResultModal: React.FC = () => {
  const { t } = useTranslation()
  const { activeInterpretation, setActiveInterpretation } = useStore()

  if (!activeInterpretation) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => setActiveInterpretation(null)}
      />
      
      {/* Modal Container */}
      <div className="relative glass-panel w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#16171d]">
          <h3 className="font-bold text-lg text-white font-outfit flex items-center gap-2">
            <Info className="h-5 w-5 text-teal-400" />
            {t('modal.title')}
          </h3>
          <button 
            onClick={() => setActiveInterpretation(null)}
            className="p-1 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal content */}
        <div className="p-6 overflow-y-auto leading-relaxed text-sm text-gray-300 whitespace-pre-wrap max-h-[60vh] custom-scroll">
          {activeInterpretation}
        </div>

        <div className="flex justify-end gap-3 px-6 py-4 border-t border-white/5 bg-[#16171d]">
          <button
            onClick={() => setActiveInterpretation(null)}
            className="btn btn-sm btn-ghost hover:bg-white/5 text-white rounded-xl px-4"
          >
            {t('modal.close')}
          </button>
        </div>
      </div>
    </div>
  )
}

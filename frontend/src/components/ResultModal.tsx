import React, { useEffect, useState } from 'react'
import { useStore } from '../store/useStore'
import { X, Loader2, Bot } from 'lucide-react'
import { GeoBotResponseViewer } from './demo/GeoBotResponseViewer'

export const ResultModal: React.FC = () => {
  const { activeInterpretation, isInterpreting, interpretationToken, setActiveInterpretation } = useStore()
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
        className="absolute inset-0 bg-black/70 backdrop-blur-md"
        onClick={handleClose}
      />

      {/* Modal Container */}
      <div className="relative glass-panel w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh] border border-teal-500/30">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#16171d]">
          <h3 className="font-bold text-lg text-white font-outfit flex items-center gap-2">
            <Bot className="h-5 w-5 text-teal-400" />
            <span>Diagnóstico Territorial GeoBot</span>
          </h3>
          <button
            onClick={handleClose}
            className="p-1 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal content */}
        <div className="p-6 overflow-y-auto max-h-[60vh] custom-scroll bg-[#0b0c10]">
          {activeInterpretation ? (
            <GeoBotResponseViewer text={activeInterpretation} />
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-gray-400">
              <Loader2 className="h-7 w-7 animate-spin text-teal-400" />
              <p className="text-sm font-medium">Generando informe geoespacial estructurado con GeoBot IA...</p>
            </div>
          )}
        </div>

        <div className="flex justify-between items-center px-6 py-4 border-t border-white/5 bg-[#16171d]">
          <span className="text-[10px] text-gray-500 font-mono">GeoBot AI Engine v2.0 • Google Earth Engine</span>
          <button
            onClick={handleClose}
            className="btn btn-sm bg-teal-500 hover:bg-teal-400 text-[#111318] font-bold rounded-xl px-5 border-none"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  )
}

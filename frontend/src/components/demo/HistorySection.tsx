import React from 'react'
import { MapPin } from 'lucide-react'

interface HistorySectionProps {
  analysisHistory: any[]
  replayHistory: (item: any) => void
  t: (key: string) => string
  isEn: boolean
  approachesConfig: Record<string, { name: string; enName: string; indices: string[] }>
}

export const HistorySection: React.FC<HistorySectionProps> = ({
  analysisHistory,
  replayHistory,
  t,
  isEn,
  approachesConfig,
}) => {
  if (!analysisHistory || analysisHistory.length === 0) return null

  return (
    <div className="glass-panel p-6 rounded-xl flex flex-col gap-4 text-left">
      <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
        <i className="fas fa-history text-teal-400 text-sm"></i>
        {t('demo.historyTitle')}
      </h4>
      <div className="flex flex-col gap-2 max-h-[160px] overflow-y-auto custom-scroll">
        {analysisHistory.map((item, idx) => (
          <div
            key={idx}
            onClick={() => replayHistory(item)}
            className="p-2.5 border border-white/5 hover:border-teal-500/20 hover:bg-[#1e2028]/40 rounded-lg text-xs cursor-pointer flex justify-between items-center transition-colors"
            title={item.location_name}
          >
            <div className="flex items-center gap-2">
              <MapPin className="h-3.5 w-3.5 text-teal-400 flex-shrink-0" />
              <span className="text-gray-300 font-bold truncate max-w-[150px]">
                {(isEn ? approachesConfig[item.approach]?.enName : approachesConfig[item.approach]?.name) || item.approach}
              </span>
            </div>
            <span className="text-[10px] text-gray-500 font-semibold">{item.timestamp}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

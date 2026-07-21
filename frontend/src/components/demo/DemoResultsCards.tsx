import React from 'react'
import { MapPin } from 'lucide-react'

interface DemoResultsCardsProps {
  selectedLocation: { name: string; lat: number; lng: number } | null
  selectedApproach: string
  t: (key: string) => string
  isEn: boolean
  approachesConfig: Record<string, { name: string; enName: string; indices: string[] }>
}

export const DemoResultsCards: React.FC<DemoResultsCardsProps> = ({
  selectedLocation,
  selectedApproach,
  t,
  isEn,
  approachesConfig,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="glass-panel p-5 rounded-xl flex gap-4 items-start">
        <MapPin className="h-6 w-6 text-teal-400 flex-shrink-0" />
        <div>
          <h4 className="font-bold text-white text-sm">{t('demo.resultLocationTitle')}</h4>
          <p className="text-gray-400 text-xs mt-1 leading-relaxed truncate max-w-[180px]" title={selectedLocation?.name}>
            {selectedLocation ? selectedLocation.name : t('demo.resultLocationDesc')}
          </p>
        </div>
      </div>
      <div className="glass-panel p-5 rounded-xl flex gap-4 items-start">
        <i className="fas fa-crosshairs text-teal-400 text-lg flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-white text-sm">{t('demo.resultApproachTitle')}</h4>
          <p className="text-gray-400 text-xs mt-1">
            {selectedApproach ? (isEn ? approachesConfig[selectedApproach]?.enName : approachesConfig[selectedApproach]?.name) : t('demo.resultApproachDesc')}
          </p>
        </div>
      </div>
      <div className="glass-panel p-5 rounded-xl flex gap-4 items-start">
        <i className="fas fa-satellite text-teal-400 text-lg flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-white text-sm">{t('demo.resultApisTitle')}</h4>
          <p className="text-gray-400 text-xs mt-1">{t('demo.resultApisDesc')}</p>
        </div>
      </div>
    </div>
  )
}

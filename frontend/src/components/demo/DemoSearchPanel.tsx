import React from 'react'
import { Search, RefreshCw } from 'lucide-react'

interface DemoSearchPanelProps {
  searchQuery: string
  setSearchQuery: (val: string) => void
  handleSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleSearchSubmit: (e: React.FormEvent) => void
  suggestions: any[]
  showSuggestions: boolean
  setShowSuggestions: (val: boolean) => void
  handleSelectSuggestion: (s: any) => void
  searchContainerRef: React.RefObject<HTMLDivElement | null>
  selectedLocation: { name: string; lat: number; lng: number } | null
  liveMetrics: any
  selectedApproach: string
  setSelectedApproach: (val: string) => void
  activeAnalysis: any
  selectedRadius: number
  setSelectedRadius: (val: number) => void
  useCustomDates: boolean
  setUseCustomDates: (val: boolean) => void
  startDate: string
  setStartDate: (val: string) => void
  endDate: string
  setEndDate: (val: string) => void
  user: any
  t: (key: string) => string
  triggerAnalysis: () => void
  isAnalyzing: boolean
  pollingStatus: string | null
}

export const DemoSearchPanel: React.FC<DemoSearchPanelProps> = ({
  searchQuery,
  handleSearchChange,
  handleSearchSubmit,
  suggestions,
  showSuggestions,
  setShowSuggestions,
  handleSelectSuggestion,
  searchContainerRef,
  selectedLocation,
  liveMetrics,
  selectedApproach,
  setSelectedApproach,
  activeAnalysis,
  selectedRadius,
  setSelectedRadius,
  useCustomDates,
  setUseCustomDates,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  user,
  t,
  triggerAnalysis,
  isAnalyzing,
  pollingStatus,
}) => {
  return (
    <div className="flex flex-col gap-6">
      {/* Search Input Box */}
      <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
        <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
          <Search className="h-4 w-4 text-teal-400" />
          {t('demo.searchLabel')}
        </h4>
        <div ref={searchContainerRef} className="relative">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
              placeholder={t('demo.searchPlaceholder')}
              className="input input-sm flex-1 bg-[#111318] border-white/10 focus:border-teal-500 rounded-lg text-xs text-white"
              autoComplete="off"
            />
            <button type="submit" className="btn btn-sm btn-ghost hover:bg-[#1e2028] border border-white/10 text-teal-400 rounded-lg">
              <Search className="h-3.5 w-3.5" />
            </button>
          </form>
          {showSuggestions && suggestions.length > 0 && (
            <ul className="absolute z-50 top-full mt-1 w-full bg-[#16171d] border border-white/10 rounded-xl shadow-2xl overflow-hidden">
              {suggestions.map((s) => (
                <li
                  key={s.place_id}
                  onMouseDown={() => handleSelectSuggestion(s)}
                  className="px-4 py-2.5 text-xs text-gray-200 hover:bg-teal-500/10 hover:text-teal-300 cursor-pointer flex items-start gap-2 border-b border-white/5 last:border-0 transition-colors"
                >
                  <i className="fas fa-map-marker-alt text-teal-400 mt-0.5 flex-shrink-0" />
                  <span className="leading-tight">{s.description}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedLocation && (
          <div className="bg-[#111318] border border-white/5 p-4 rounded-xl text-left flex flex-col gap-1">
            <div className="font-bold text-white text-xs leading-normal line-clamp-1">{selectedLocation.name}</div>
            <div className="text-[10px] text-gray-500 font-semibold font-mono">
              {selectedLocation.lat.toFixed(5)}, {selectedLocation.lng.toFixed(5)}
            </div>
          </div>
        )}

        {/* Live metrics (Skeletons / Loaded) */}
        {liveMetrics && (
          <div className="bg-[#111318]/50 border border-white/5 p-4 rounded-xl flex flex-col gap-3 text-left">
            <h5 className="text-[10px] uppercase font-bold text-gray-400 tracking-wider flex items-center gap-1.5">
              <i className="fas fa-broadcast-tower text-teal-400"></i>
              {t('demo.livePanelTitle')}
            </h5>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="flex flex-col gap-1">
                <span className="text-gray-500 font-semibold text-[10px]">{t('demo.elevation')}</span>
                <span className={`font-bold ${(!user || user.preferences?.layers?.elevation !== false) ? 'text-white' : 'text-gray-600'}`}>
                  {(!user || user.preferences?.layers?.elevation !== false) ? liveMetrics.elevation : 'Desactivado'}
                </span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-gray-500 font-semibold text-[10px]">{t('demo.aqi')}</span>
                <span className={`font-bold ${(!user || user.preferences?.layers?.aqi !== false) ? 'text-white' : 'text-gray-600'}`}>
                  {(!user || user.preferences?.layers?.aqi !== false) ? liveMetrics.aqi : 'Desactivado'}
                </span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-gray-500 font-semibold text-[10px]">{t('demo.solar')}</span>
                <span className={`font-bold ${(!user || user.preferences?.layers?.solar !== false) ? 'text-white' : 'text-gray-600'}`}>
                  {(!user || user.preferences?.layers?.solar !== false) ? liveMetrics.solar : 'Desactivado'}
                </span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-gray-500 font-semibold text-[10px]">{t('demo.slope')}</span>
                <span className={`font-bold ${(!user || user.preferences?.layers?.slope !== false) ? 'text-white' : 'text-gray-600'}`}>
                  {(!user || user.preferences?.layers?.slope !== false) ? liveMetrics.slope : 'Desactivado'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Select Approach */}
      <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
        <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
          <i className="fas fa-crosshairs text-teal-400 text-sm"></i>
          {t('demo.selectApproachLabel')}
        </h4>
        <select
          value={selectedApproach}
          onChange={(e) => setSelectedApproach(e.target.value)}
          className="select select-sm bg-[#111318] border-white/10 focus:border-teal-500 rounded-lg text-xs text-white w-full"
        >
          <option value="">{t('demo.chooseApproachOpt')}</option>
          <optgroup label="Sectores Industriales">
            <option value="mining">Minería Sostenible</option>
            <option value="agriculture">Agroindustria Inteligente</option>
            <option value="energy">Energías Renovables</option>
            <option value="real-estate">Desarrollo Inmobiliario</option>
          </optgroup>
          <optgroup label="Análisis General">
            <option value="fire-risk">Riesgo de Incendio Forestal</option>
            <option value="flood-risk">Riesgo de Inundación</option>
            <option value="water-management">Gestión Hídrica</option>
            <option value="environmental">Calidad Ambiental</option>
            <option value="land-planning">Planificación Territorial</option>
          </optgroup>
        </select>

        {selectedApproach && activeAnalysis && activeAnalysis.approach === selectedApproach && (
          <div className="mt-2 text-left flex flex-col gap-3">
            <div className="text-gray-400 text-xs font-semibold">{t('demo.indicesAndData')}</div>
            <div className="flex flex-col gap-2">
              {Object.entries(activeAnalysis.indices || {})
                .filter(([key]) => {
                  const lowKey = key.toLowerCase()
                  if (user && user.preferences?.layers) {
                    if (lowKey === 'ndvi' && user.preferences.layers.ndvi === false) return false
                    if (lowKey === 'ndwi' && user.preferences.layers.ndwi === false) return false
                    if (lowKey === 'ndmi' && user.preferences.layers.ndmi === false) return false
                  }
                  return true
                })
                .map(([key, val]) => (
                  <div key={key} className="flex justify-between items-center text-xs py-1.5 border-b border-white/5">
                    <span className="text-gray-400 font-semibold">{key}</span>
                    <span className="text-white font-bold font-mono">{typeof val === 'number' ? (val as number).toFixed(4) : String(val)}</span>
                  </div>
                ))}
            </div>

            {/* Export PDF Executive Report */}
            <button
              type="button"
              onClick={() => window.open(`/api/v1/analyze/export/${activeAnalysis.task_id}`, '_blank')}
              className="btn btn-xs bg-[#16171d] hover:bg-[#1e2028] border border-white/10 text-teal-400 rounded-lg flex items-center justify-center gap-1.5 w-full mt-1 font-semibold"
            >
              <i className="fas fa-file-pdf text-[11px]"></i>
              <span>Exportar Reporte Ejecutivo PDF</span>
            </button>
          </div>
        )}
      </div>

      {/* Analysis Radius */}
      <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
        <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
          <i className="fas fa-ruler-combined text-teal-400 text-sm"></i>
          {t('demo.radiusLabel')}
        </h4>
        <select
          value={selectedRadius}
          onChange={(e) => setSelectedRadius(Number(e.target.value))}
          className="select select-sm bg-[#111318] border-white/10 focus:border-teal-500 rounded-lg text-xs text-white w-full"
        >
          <option value={2000}>2 kilómetros (~12.57 km²)</option>
          <option value={5000}>5 kilómetros (~78.54 km²)</option>
          <option value={10000}>10 kilómetros (~314.16 km²)</option>
        </select>
        <div className="text-[10px] text-gray-500 leading-normal text-left">
          <i className="fas fa-info-circle"></i> {t('demo.radiusDesc')}
        </div>

        {/* Custom Historical Date Range (Premium) */}
        <div className="border-t border-white/5 pt-3 mt-1 flex flex-col gap-2 text-left">
          <label className="flex items-center gap-2 text-xs font-semibold text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={useCustomDates && !!user}
              disabled={!user}
              onChange={(e) => setUseCustomDates(e.target.checked)}
              className="checkbox checkbox-xs checkbox-primary"
            />
            {user ? (
              <span>📅 Rango Histórico (Premium)</span>
            ) : (
              <span className="text-gray-500 flex items-center gap-1">
                <i className="fas fa-lock text-[10px]"></i>
                📅 Rango Histórico (Premium)
              </span>
            )}
          </label>

          {!user && (
            <p className="text-[9px] text-gray-500 leading-snug">
              Inicia sesión para comparar imágenes históricas de los últimos 3 años.
            </p>
          )}

          {useCustomDates && user && (
            <div className="grid grid-cols-2 gap-2 mt-1">
              <div className="flex flex-col gap-1">
                <span className="text-[9px] text-gray-400 font-semibold">Desde</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="input input-xs bg-[#111318] border-white/10 text-white rounded text-[10px]"
                />
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[9px] text-gray-400 font-semibold">Hasta</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="input input-xs bg-[#111318] border-white/10 text-white rounded text-[10px]"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Trigger Analysis Action Button & Polling Status */}
      <div className="flex flex-col gap-2">
        <button
          onClick={triggerAnalysis}
          disabled={isAnalyzing || !selectedLocation || !selectedApproach}
          className="btn bg-gradient-to-r from-teal-500 to-emerald-500 text-black border-none font-bold text-sm hover:opacity-90 rounded-xl w-full py-3 shadow-lg shadow-teal-500/10 disabled:opacity-40"
        >
          {isAnalyzing ? (
            <span className="flex items-center gap-2 justify-center">
              <RefreshCw className="h-4 w-4 animate-spin" />
              Procesando Satélite...
            </span>
          ) : (
            <span>🛰️ Analizar Zona Seleccionada</span>
          )}
        </button>

        {pollingStatus && (
          <div className="text-teal-400 text-xs text-center animate-pulse italic flex items-center justify-center gap-1.5 mt-1">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            <span>{pollingStatus}</span>
          </div>
        )}
      </div>
    </div>
  )
}

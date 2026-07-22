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
      {/* Step 1: Select Approach (Featured First) */}
      <div className="glass-panel p-6 rounded-xl flex flex-col gap-4 border border-teal-500/30 shadow-xl shadow-teal-950/20">
        <div className="flex items-center justify-between">
          <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
            <span className="w-5 h-5 rounded-full bg-teal-500 text-[#111318] flex items-center justify-center text-xs font-bold">1</span>
            {t('demo.selectApproachLabel')}
          </h4>
          <span className="text-[10px] uppercase font-bold tracking-wider text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded-full border border-teal-500/20">
            Auto-Configuración ON
          </span>
        </div>

        <select
          value={selectedApproach}
          onChange={(e) => setSelectedApproach(e.target.value)}
          className="select select-sm bg-[#111318] border-teal-500/40 focus:border-teal-400 rounded-lg text-xs text-white w-full font-semibold"
        >
          <option value="">{t('demo.chooseApproachOpt')}</option>
          <optgroup label="Sectores Industriales">
            <option value="agriculture">🌾 Agroindustria Inteligente (NDVI, NDMI, SAVI, NDRE, BSI)</option>
            <option value="mining">⛏️ Minería Sostenible (NDVI, NDWI, BSI, NDBI, Slope)</option>
            <option value="energy">☀️ Energías Renovables (Solar, Slope, Aspect, NDBI)</option>
            <option value="real-estate">🏢 Desarrollo Inmobiliario (NDBI, Slope, LST, MNDWI)</option>
          </optgroup>
          <optgroup label="Análisis Ambiental y Riesgos">
            <option value="fire-risk">🔥 Riesgo de Incendio Forestal (NBR, NDMI, NDVI, Slope)</option>
            <option value="flood-risk">🌊 Riesgo de Inundación (MNDWI, NDWI, NDBI, DEM)</option>
            <option value="water-management">💧 Gestión Hídrica (NDWI, MNDWI, NDMI, NDVI)</option>
            <option value="environmental">🍃 Calidad Ambiental (EVI, NDVI, NDMI, AQI, BSI)</option>
            <option value="land-planning">🗺️ Planificación Territorial (Slope, NDBI, BSI, NDVI)</option>
          </optgroup>
        </select>

        {/* Auto-selected Layers Notification */}
        {selectedApproach && (
          <div className="bg-[#111318] border border-teal-500/20 p-3 rounded-lg flex flex-col gap-2 text-left">
            <div className="flex items-center justify-between text-[10px] text-gray-400 font-bold uppercase tracking-wider">
              <span>Capas activadas para este enfoque:</span>
              <span className="text-teal-400">Automático</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {selectedApproach === 'agriculture' && (
                <>
                  <span className="badge badge-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/40">NDVI</span>
                  <span className="badge badge-xs bg-orange-500/20 text-orange-300 border-orange-500/40">NDMI</span>
                  <span className="badge badge-xs bg-teal-500/20 text-teal-300 border-teal-500/40">SAVI</span>
                  <span className="badge badge-xs bg-lime-500/20 text-lime-300 border-lime-500/40">NDRE</span>
                  <span className="badge badge-xs bg-amber-500/20 text-amber-300 border-amber-500/40">BSI</span>
                </>
              )}
              {selectedApproach === 'mining' && (
                <>
                  <span className="badge badge-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/40">NDVI</span>
                  <span className="badge badge-xs bg-blue-500/20 text-blue-300 border-blue-500/40">NDWI</span>
                  <span className="badge badge-xs bg-amber-500/20 text-amber-300 border-amber-500/40">BSI</span>
                  <span className="badge badge-xs bg-indigo-500/20 text-indigo-300 border-indigo-500/40">NDBI</span>
                  <span className="badge badge-xs bg-purple-500/20 text-purple-300 border-purple-500/40">Pendiente</span>
                </>
              )}
              {selectedApproach === 'energy' && (
                <>
                  <span className="badge badge-xs bg-yellow-500/20 text-yellow-300 border-yellow-500/40">Solar</span>
                  <span className="badge badge-xs bg-purple-500/20 text-purple-300 border-purple-500/40">Elevación</span>
                  <span className="badge badge-xs bg-amber-500/20 text-amber-300 border-amber-500/40">Aspect</span>
                  <span className="badge badge-xs bg-indigo-500/20 text-indigo-300 border-indigo-500/40">NDBI</span>
                </>
              )}
              {selectedApproach === 'real-estate' && (
                <>
                  <span className="badge badge-xs bg-indigo-500/20 text-indigo-300 border-indigo-500/40">NDBI</span>
                  <span className="badge badge-xs bg-purple-500/20 text-purple-300 border-purple-500/40">Pendiente</span>
                  <span className="badge badge-xs bg-red-500/20 text-red-300 border-red-500/40">LST</span>
                  <span className="badge badge-xs bg-sky-500/20 text-sky-300 border-sky-500/40">MNDWI</span>
                </>
              )}
              {selectedApproach === 'fire-risk' && (
                <>
                  <span className="badge badge-xs bg-red-500/20 text-red-300 border-red-500/40">NBR</span>
                  <span className="badge badge-xs bg-orange-500/20 text-orange-300 border-orange-500/40">NDMI</span>
                  <span className="badge badge-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/40">NDVI</span>
                  <span className="badge badge-xs bg-purple-500/20 text-purple-300 border-purple-500/40">Pendiente</span>
                </>
              )}
              {selectedApproach === 'flood-risk' && (
                <>
                  <span className="badge badge-xs bg-sky-500/20 text-sky-300 border-sky-500/40">MNDWI</span>
                  <span className="badge badge-xs bg-blue-500/20 text-blue-300 border-blue-500/40">NDWI</span>
                  <span className="badge badge-xs bg-indigo-500/20 text-indigo-300 border-indigo-500/40">NDBI</span>
                  <span className="badge badge-xs bg-purple-500/20 text-purple-300 border-purple-500/40">DEM</span>
                </>
              )}
              {selectedApproach === 'water-management' && (
                <>
                  <span className="badge badge-xs bg-blue-500/20 text-blue-300 border-blue-500/40">NDWI</span>
                  <span className="badge badge-xs bg-sky-500/20 text-sky-300 border-sky-500/40">MNDWI</span>
                  <span className="badge badge-xs bg-orange-500/20 text-orange-300 border-orange-500/40">NDMI</span>
                  <span className="badge badge-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/40">NDVI</span>
                </>
              )}
              {selectedApproach === 'environmental' && (
                <>
                  <span className="badge badge-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/40">EVI</span>
                  <span className="badge badge-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/40">NDVI</span>
                  <span className="badge badge-xs bg-orange-500/20 text-orange-300 border-orange-500/40">NDMI</span>
                  <span className="badge badge-xs bg-sky-500/20 text-sky-300 border-sky-500/40">AQI</span>
                  <span className="badge badge-xs bg-amber-500/20 text-amber-300 border-amber-500/40">BSI</span>
                </>
              )}
              {selectedApproach === 'land-planning' && (
                <>
                  <span className="badge badge-xs bg-purple-500/20 text-purple-300 border-purple-500/40">Pendiente</span>
                  <span className="badge badge-xs bg-indigo-500/20 text-indigo-300 border-indigo-500/40">NDBI</span>
                  <span className="badge badge-xs bg-amber-500/20 text-amber-300 border-amber-500/40">BSI</span>
                  <span className="badge badge-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/40">NDVI</span>
                </>
              )}
            </div>
          </div>
        )}

        {selectedApproach && activeAnalysis && activeAnalysis.approach === selectedApproach && (
          <div className="mt-2 text-left flex flex-col gap-3">
            <div className="text-gray-400 text-xs font-semibold">{t('demo.indicesAndData')}</div>
            <div className="flex flex-col gap-2">
              {Object.entries(activeAnalysis.indices || {}).map(([key, val]) => (
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

      {/* Step 2: Location Search */}
      <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
        <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
          <span className="w-5 h-5 rounded-full bg-teal-500 text-[#111318] flex items-center justify-center text-xs font-bold">2</span>
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

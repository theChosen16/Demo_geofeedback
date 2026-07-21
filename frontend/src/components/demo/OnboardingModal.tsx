import React from 'react'

interface OnboardingModalProps {
  showOnboarding: boolean
  onboardingStep: number
  setOnboardingStep: (step: number) => void
  onboardingSector: string
  setOnboardingSector: (val: string) => void
  onboardingRole: string
  setOnboardingRole: (val: string) => void
  onboardingLocation: string
  setOnboardingLocation: (val: string) => void
  onboardingLayers: {
    ndvi: boolean
    ndwi: boolean
    ndmi: boolean
    elevation: boolean
    slope: boolean
    lst: boolean
    aqi: boolean
    solar: boolean
  }
  setOnboardingLayers: React.Dispatch<React.SetStateAction<{
    ndvi: boolean
    ndwi: boolean
    ndmi: boolean
    elevation: boolean
    slope: boolean
    lst: boolean
    aqi: boolean
    solar: boolean
  }>>
  handleSaveOnboarding: (skip?: boolean) => void
  isSavingOnboarding: boolean
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  showOnboarding,
  onboardingStep,
  setOnboardingStep,
  onboardingSector,
  setOnboardingSector,
  onboardingRole,
  setOnboardingRole,
  onboardingLocation,
  setOnboardingLocation,
  onboardingLayers,
  setOnboardingLayers,
  handleSaveOnboarding,
  isSavingOnboarding,
}) => {
  if (!showOnboarding) return null

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="relative w-full max-w-lg bg-[#16171d] border border-white/10 p-6 rounded-2xl shadow-2xl text-left flex flex-col gap-5 overflow-hidden">
        
        {/* Ambient Background Gradient */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />

        {/* Title / Header */}
        <div>
          <div className="text-[10px] text-teal-400 font-bold uppercase tracking-wider mb-1">
            Paso {onboardingStep} de 2 • Personalización
          </div>
          <h3 className="text-lg font-bold text-white font-outfit">
            Personaliza tu experiencia territorial
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Esta información opcional nos ayuda a adaptar los indicadores y mapas a tus intereses.
          </p>
        </div>

        {/* Step 1: Metadata Questions */}
        {onboardingStep === 1 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-gray-300 font-semibold">Sector o Industria de Interés</label>
              <select
                value={onboardingSector}
                onChange={(e) => setOnboardingSector(e.target.value)}
                className="select select-sm bg-[#111318] border-white/10 text-white rounded-lg text-xs"
              >
                <option value="">Selecciona una opción...</option>
                <option value="agriculture">Agricultura y Forestal</option>
                <option value="mining">Minería y Recursos Naturales</option>
                <option value="energy">Energía y Renovables</option>
                <option value="real-estate">Inmobiliaria y Construcción</option>
                <option value="environmental">Medio Ambiente y Conservación</option>
                <option value="academia">Academia e Investigación</option>
                <option value="other">Otro / General</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-gray-300 font-semibold">Tu Rol o Cargo</label>
              <input
                type="text"
                value={onboardingRole}
                onChange={(e) => setOnboardingRole(e.target.value)}
                placeholder="Ej: Consultor Ambiental, Ingeniero, Administrador"
                className="input input-sm bg-[#111318] border-white/10 text-white rounded-lg text-xs"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-gray-300 font-semibold">Ubicación Territorial de Interés Principal</label>
              <input
                type="text"
                value={onboardingLocation}
                onChange={(e) => setOnboardingLocation(e.target.value)}
                placeholder="Ej: Copiapó, Región Metropolitana, Valparaíso"
                className="input input-sm bg-[#111318] border-white/10 text-white rounded-lg text-xs"
              />
            </div>
          </div>
        )}

        {/* Step 2: Layer selections */}
        {onboardingStep === 2 && (
          <div className="flex flex-col gap-4 max-h-[300px] overflow-y-auto pr-1 custom-scroll">
            <div>
              <div className="text-xs text-teal-400 font-bold mb-2 uppercase tracking-wide">APIs de Base (Recomendadas)</div>
              <div className="flex flex-col gap-2.5">
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.ndvi}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, ndvi: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">NDVI (Índice de Vegetación)</div>
                    <div className="text-[10px] text-gray-500">Mide la salud y densidad de la cubierta vegetal.</div>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.ndwi}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, ndwi: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">NDWI (Índice de Inundación y Agua)</div>
                    <div className="text-[10px] text-gray-500">Detecta acumulación de agua y cuerpos hídricos superficiales.</div>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.ndmi}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, ndmi: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">NDMI (Índice de Humedad del Suelo)</div>
                    <div className="text-[10px] text-gray-500">Evalúa el estrés hídrico de la vegetación y humedad en suelo.</div>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.elevation}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, elevation: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">Elevación (Modelo Digital DEM)</div>
                    <div className="text-[10px] text-gray-500">Determina la altitud del terreno en metros respecto al nivel del mar.</div>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.slope}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, slope: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">Pendiente (Inclinación del Relieve)</div>
                    <div className="text-[10px] text-gray-500">Mide los grados de pendiente física de la ladera analizada.</div>
                  </div>
                </label>
              </div>
            </div>

            <div className="border-t border-white/5 pt-3">
              <div className="text-xs text-gray-400 font-bold mb-2 uppercase tracking-wide">Capas de Información Adicional (Opcionales)</div>
              <div className="flex flex-col gap-2.5">
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.lst}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, lst: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">Temperatura Superficial (LST)</div>
                    <div className="text-[10px] text-gray-500">Temperatura térmica de la superficie terrestre.</div>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.aqi}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, aqi: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">Calidad del Aire (AQI)</div>
                    <div className="text-[10px] text-gray-500">Índice de contaminación atmosférica en tiempo real.</div>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onboardingLayers.solar}
                    onChange={(e) => setOnboardingLayers({ ...onboardingLayers, solar: e.target.checked })}
                    className="checkbox checkbox-sm checkbox-primary mt-0.5"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">Potencial Solar Fotovoltaico</div>
                    <div className="text-[10px] text-gray-500">Estimación de radiación y viabilidad solar.</div>
                  </div>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between border-t border-white/10 pt-4 mt-2">
          <button
            onClick={() => handleSaveOnboarding(true)}
            className="text-xs text-gray-400 hover:text-white font-semibold transition-colors"
          >
            Omitir por ahora
          </button>

          <div className="flex items-center gap-2">
            {onboardingStep === 2 && (
              <button
                onClick={() => setOnboardingStep(1)}
                className="btn btn-sm btn-ghost text-xs text-gray-300 font-bold"
              >
                Atrás
              </button>
            )}
            {onboardingStep === 1 ? (
              <button
                onClick={() => setOnboardingStep(2)}
                className="btn btn-sm bg-gradient-to-r from-teal-500 to-emerald-500 text-black border-none font-bold text-xs hover:opacity-90"
              >
                Siguiente
              </button>
            ) : (
              <button
                onClick={() => handleSaveOnboarding(false)}
                disabled={isSavingOnboarding}
                className="btn btn-sm bg-gradient-to-r from-teal-500 to-emerald-500 text-black border-none font-bold text-xs hover:opacity-90"
              >
                {isSavingOnboarding ? 'Guardando...' : 'Guardar Preferencias'}
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}

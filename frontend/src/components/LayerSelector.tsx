import React, { useRef, useEffect } from 'react'
import { useStore } from '../store/useStore'
import {
  Leaf,
  Droplet,
  Flame,
  Mountain,
  Wind,
  Sun,
  Thermometer,
  Satellite,
  ChevronRight,
} from 'lucide-react'

// ─────────────────────────────────────────────────────────────────────────────
// Catalogue of every layer the platform can expose
// ─────────────────────────────────────────────────────────────────────────────
export interface LayerDef {
  key: string
  label: string
  enLabel: string
  description: string
  enDescription: string
  icon: React.ReactNode
  color: string       // Tailwind accent colour token (bg-*/text-*/border-*)
  badge: 'satellite' | 'api'
  formula?: string
}

export const ALL_LAYERS: LayerDef[] = [
  // ── Satellite indices (GEE) ────────────────────────────────────────────────
  {
    key: 'ndvi',
    label: 'Vegetación (NDVI)',
    enLabel: 'Vegetation (NDVI)',
    description: 'Salud y densidad de la cubierta vegetal mediante luz infrarroja.',
    enDescription: 'Vegetation health and density via near-infrared light.',
    icon: <Leaf className="h-5 w-5" />,
    color: 'emerald',
    badge: 'satellite',
    formula: '(NIR−Red)/(NIR+Red)',
  },
  {
    key: 'ndwi',
    label: 'Agua Superficial (NDWI)',
    enLabel: 'Surface Water (NDWI)',
    description: 'Detección de cuerpos de agua, ríos y zonas de inundación.',
    enDescription: 'Detection of water bodies, rivers and flood zones.',
    icon: <Droplet className="h-5 w-5" />,
    color: 'blue',
    badge: 'satellite',
    formula: '(Green−NIR)/(Green+NIR)',
  },
  {
    key: 'ndmi',
    label: 'Humedad (NDMI)',
    enLabel: 'Moisture (NDMI)',
    description: 'Estrés hídrico en vegetación y riesgo de incendio forestal.',
    enDescription: 'Vegetation water stress and wildfire risk assessment.',
    icon: <Flame className="h-5 w-5" />,
    color: 'orange',
    badge: 'satellite',
    formula: '(NIR−SWIR)/(NIR+SWIR)',
  },
  // ── Google APIs ────────────────────────────────────────────────────────────
  {
    key: 'elevation',
    label: 'Elevación y Pendiente',
    enLabel: 'Elevation & Slope',
    description: 'Altitud topográfica y gradiente de pendiente del terreno.',
    enDescription: 'Topographic altitude and terrain slope gradient.',
    icon: <Mountain className="h-5 w-5" />,
    color: 'slate',
    badge: 'api',
  },
  {
    key: 'aqi',
    label: 'Calidad del Aire (AQI)',
    enLabel: 'Air Quality (AQI)',
    description: 'Índice de calidad del aire y concentración de contaminantes.',
    enDescription: 'Air quality index and pollutant concentration.',
    icon: <Wind className="h-5 w-5" />,
    color: 'sky',
    badge: 'api',
  },
  {
    key: 'solar',
    label: 'Potencial Solar',
    enLabel: 'Solar Potential',
    description: 'Irradiancia solar y potencial fotovoltaico en techos y superficies.',
    enDescription: 'Solar irradiance and rooftop photovoltaic potential.',
    icon: <Sun className="h-5 w-5" />,
    color: 'yellow',
    badge: 'api',
  },
  {
    key: 'lst',
    label: 'Temperatura Superficial (LST)',
    enLabel: 'Land Surface Temp (LST)',
    description: 'Temperatura de la superficie terrestre para islas de calor urbanas.',
    enDescription: 'Land surface temperature for urban heat island mapping.',
    icon: <Thermometer className="h-5 w-5" />,
    color: 'red',
    badge: 'satellite',
    formula: 'Landsat Band 10',
  },
]

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; ring: string }> = {
  emerald: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', ring: 'ring-emerald-500/40' },
  blue:    { bg: 'bg-blue-500/10',    border: 'border-blue-500/30',    text: 'text-blue-400',    ring: 'ring-blue-500/40'    },
  orange:  { bg: 'bg-orange-500/10',  border: 'border-orange-500/30',  text: 'text-orange-400',  ring: 'ring-orange-500/40'  },
  slate:   { bg: 'bg-slate-500/10',   border: 'border-slate-500/30',   text: 'text-slate-300',   ring: 'ring-slate-500/40'   },
  sky:     { bg: 'bg-sky-500/10',     border: 'border-sky-500/30',     text: 'text-sky-400',     ring: 'ring-sky-500/40'     },
  yellow:  { bg: 'bg-yellow-500/10',  border: 'border-yellow-500/30',  text: 'text-yellow-400',  ring: 'ring-yellow-500/40'  },
  red:     { bg: 'bg-red-500/10',     border: 'border-red-500/30',     text: 'text-red-400',     ring: 'ring-red-500/40'     },
}

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────
export const LayerSelector: React.FC = () => {
  const { selectedLayers, toggleLayer, setSelectedLayers } = useStore()
  const containerRef = useRef<HTMLDivElement>(null)

  // Scroll-driven entrance animation
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('translate-y-0')
            entry.target.classList.remove('opacity-0', 'translate-y-6')
          }
        })
      },
      { threshold: 0.15 }
    )
    const cards = containerRef.current?.querySelectorAll('[data-layer-card]')
    cards?.forEach((card) => observer.observe(card))
    return () => observer.disconnect()
  }, [])

  const activeCount = selectedLayers.size

  const selectAll = () => setSelectedLayers(new Set(ALL_LAYERS.map((l) => l.key)))
  const clearAll  = () => setSelectedLayers(new Set(['ndvi'])) // keep at least one

  return (
    <section
      id="capas"
      className="py-16 lg:py-20 bg-[#0b0c10] border-b border-white/5 relative overflow-hidden"
    >
      {/* decorative blobs */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] rounded-full bg-teal-500/4 blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full bg-purple-500/4 blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 relative z-10">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 mb-4">
            <Satellite className="h-4 w-4 text-teal-400" />
            <span className="text-xs font-semibold text-teal-400 tracking-wider uppercase">
              Configura tu análisis
            </span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-white font-outfit mb-3 tracking-tight">
            Elige las capas de datos
          </h2>
          <p className="text-base text-[#94a3b8] max-w-2xl mx-auto">
            Selecciona qué información satelital y ambiental quieres visualizar en la demo interactiva.
            Puedes cambiarlas en cualquier momento antes de lanzar el análisis.
          </p>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-teal-500 text-[#111318] text-xs font-bold">
              {activeCount}
            </span>
            <span>
              {activeCount === 1 ? 'capa activa' : 'capas activas'}
            </span>
            <span className="text-gray-600">de {ALL_LAYERS.length}</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-gray-400 hover:text-white hover:border-white/25 transition-colors"
            >
              Seleccionar todas
            </button>
            <button
              onClick={clearAll}
              className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-gray-400 hover:text-red-400 hover:border-red-500/30 transition-colors"
            >
              Limpiar
            </button>
          </div>
        </div>

        {/* Layer grid */}
        <div
          ref={containerRef}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3"
        >
          {ALL_LAYERS.map((layer, i) => {
            const c = COLOR_MAP[layer.color] ?? COLOR_MAP['slate']
            const isActive = selectedLayers.has(layer.key)

            return (
              <button
                key={layer.key}
                data-layer-card
                onClick={() => toggleLayer(layer.key)}
                style={{ transitionDelay: `${i * 40}ms` }}
                className={[
                  'group relative flex flex-col gap-3 p-4 rounded-xl border text-left',
                  'transition-all duration-300 cursor-pointer opacity-0 translate-y-6',
                  isActive
                    ? `${c.border} ${c.bg} ring-1 ${c.ring} shadow-lg shadow-teal-950/20 opacity-100 scale-100`
                    : 'border-white/10 bg-white/5 backdrop-blur-md opacity-40 hover:opacity-85 hover:border-white/25 hover:bg-white/10 scale-[0.98] hover:scale-100',
                ].join(' ')}
              >
                {/* badge */}
                <div className="absolute top-3 right-3">
                  <span
                    className={`text-[10px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded-full border transition-all ${
                      isActive
                        ? layer.badge === 'satellite'
                          ? 'text-purple-400 border-purple-500/30 bg-purple-500/10'
                          : 'text-sky-400 border-sky-500/30 bg-sky-500/10'
                        : 'text-gray-500 border-white/10 bg-white/5 opacity-60'
                    }`}
                  >
                    {layer.badge === 'satellite' ? 'SAT' : 'API'}
                  </span>
                </div>

                {/* icon */}
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all duration-200 group-hover:scale-105 ${
                    isActive
                      ? `${c.bg} ${c.border} ${c.text}`
                      : 'bg-white/5 border-white/10 text-gray-500 group-hover:text-gray-300 group-hover:border-white/20'
                  }`}
                >
                  {layer.icon}
                </div>

                {/* text */}
                <div className="pr-8">
                  <p className={`text-sm font-bold mb-0.5 transition-colors ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>
                    {layer.label}
                  </p>
                  <p className={`text-xs leading-relaxed transition-colors ${isActive ? 'text-gray-400' : 'text-gray-500/80 group-hover:text-gray-400'}`}>
                    {layer.description}
                  </p>
                  {layer.formula && (
                    <p className={`mt-1.5 text-[10px] font-mono transition-colors ${isActive ? 'text-gray-500' : 'text-gray-600/70'}`}>
                      {layer.formula}
                    </p>
                  )}
                </div>

                {/* active indicator */}
                <div
                  className={`absolute bottom-3 right-3 w-2 h-2 rounded-full transition-all duration-200 ${
                    isActive
                      ? `${c.text.replace('text-', 'bg-')} scale-100 shadow-[0_0_8px_rgba(45,212,191,0.6)]`
                      : 'bg-white/10 border border-white/20 scale-75 opacity-40'
                  }`}
                />
              </button>
            )
          })}
        </div>

        {/* CTA */}
        <div className="mt-8 flex justify-center">
          <a
            href="#demo"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 text-[#111318] font-bold text-sm hover:opacity-90 transition-opacity shadow-lg"
          >
            Ir a la demo interactiva
            <ChevronRight className="h-4 w-4" />
          </a>
        </div>
      </div>
    </section>
  )
}

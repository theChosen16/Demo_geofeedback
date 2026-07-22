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
  emerald: { bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', text: 'text-emerald-400', ring: 'ring-emerald-500/50' },
  blue:    { bg: 'bg-blue-500/15',    border: 'border-blue-500/40',    text: 'text-blue-400',    ring: 'ring-blue-500/50'    },
  orange:  { bg: 'bg-orange-500/15',  border: 'border-orange-500/40',  text: 'text-orange-400',  ring: 'ring-orange-500/50'  },
  slate:   { bg: 'bg-indigo-500/15',  border: 'border-indigo-500/40',  text: 'text-indigo-300',  ring: 'ring-indigo-500/50'  },
  sky:     { bg: 'bg-sky-500/15',     border: 'border-sky-500/40',     text: 'text-sky-400',     ring: 'ring-sky-500/50'     },
  yellow:  { bg: 'bg-amber-500/15',   border: 'border-amber-500/40',   text: 'text-amber-400',   ring: 'ring-amber-500/50'   },
  red:     { bg: 'bg-rose-500/15',    border: 'border-rose-500/40',    text: 'text-rose-400',    ring: 'ring-rose-500/50'    },
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
          {ALL_LAYERS.map((layer) => {
            const c = COLOR_MAP[layer.color] ?? COLOR_MAP['slate']
            const isActive = selectedLayers.has(layer.key)

            return (
              <button
                key={layer.key}
                data-layer-card
                type="button"
                onClick={() => toggleLayer(layer.key)}
                className={[
                  'group relative flex flex-col gap-3 p-4 rounded-xl border text-left',
                  'transition-all duration-150 cursor-pointer opacity-0 translate-y-6',
                  isActive
                    ? `${c.border} ${c.bg} ring-2 ${c.ring} shadow-xl shadow-teal-950/20 opacity-100 scale-100 backdrop-blur-md`
                    : 'border-white/10 bg-white/[0.04] backdrop-blur-md opacity-60 hover:opacity-95 hover:border-white/25 hover:bg-white/[0.08] scale-[0.99] hover:scale-100',
                ].join(' ')}
              >
                {/* badge */}
                <div className="absolute top-3 right-3">
                  <span
                    className={`text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full border transition-all ${
                      isActive
                        ? layer.badge === 'satellite'
                          ? 'text-purple-300 border-purple-500/40 bg-purple-500/20'
                          : 'text-sky-300 border-sky-500/40 bg-sky-500/20'
                        : 'text-gray-400 border-white/10 bg-white/5 opacity-80'
                    }`}
                  >
                    {layer.badge === 'satellite' ? 'SAT' : 'API'}
                  </span>
                </div>

                {/* icon - vibrant and clear in both selected and unselected states */}
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all duration-150 group-hover:scale-105 ${
                    isActive
                      ? `${c.bg} ${c.border} ${c.text} shadow-sm`
                      : `${c.bg} ${c.border} ${c.text} opacity-70 group-hover:opacity-100`
                  }`}
                >
                  {layer.icon}
                </div>

                {/* text */}
                <div className="pr-8">
                  <p className={`text-sm font-bold mb-0.5 transition-colors ${isActive ? 'text-white' : 'text-gray-300 group-hover:text-white'}`}>
                    {layer.label}
                  </p>
                  <p className={`text-xs leading-relaxed transition-colors ${isActive ? 'text-gray-300' : 'text-gray-400 group-hover:text-gray-300'}`}>
                    {layer.description}
                  </p>
                  {layer.formula && (
                    <p className={`mt-1.5 text-[10px] font-mono transition-colors ${isActive ? 'text-teal-400/80' : 'text-gray-500 group-hover:text-gray-400'}`}>
                      {layer.formula}
                    </p>
                  )}
                </div>

                {/* active indicator */}
                <div
                  className={`absolute bottom-3 right-3 w-2.5 h-2.5 rounded-full transition-all duration-150 ${
                    isActive
                      ? `${c.text.replace('text-', 'bg-')} scale-100 shadow-[0_0_10px_rgba(45,212,191,0.8)]`
                      : 'bg-white/20 border border-white/30 scale-75 opacity-50'
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

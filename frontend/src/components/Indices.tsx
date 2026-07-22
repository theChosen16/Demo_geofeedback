import React from 'react'
import { Leaf, Droplet, Flame, Lightbulb, Satellite, Mountain, Sun, Layers } from 'lucide-react'

export const Indices: React.FC = () => {

  const allIndices = [
    {
      key: 'ndvi',
      title: 'NDVI — Índice Vegetación',
      formula: '(B8 - B4) / (B8 + B4)',
      bands: 'Sentinel-2 NIR (B8) y Red (B4)',
      desc: 'Mide la densidad foliar y la salud fotosintética de bosques y cultivos.',
      icon: <Leaf className="h-5 w-5 text-emerald-400" />,
      badgeBg: 'bg-emerald-500/10 border-emerald-500/25',
    },
    {
      key: 'ndwi',
      title: 'NDWI — Agua Superficial',
      formula: '(B3 - B8) / (B3 + B8)',
      bands: 'Sentinel-2 Green (B3) y NIR (B8)',
      desc: 'Delimita lagunas, ríos, humedales y embalses hídricos.',
      icon: <Droplet className="h-5 w-5 text-blue-400" />,
      badgeBg: 'bg-blue-500/10 border-blue-500/25',
    },
    {
      key: 'mndwi',
      title: 'MNDWI — Agua Modificado',
      formula: '(B3 - B11) / (B3 + B11)',
      bands: 'Sentinel-2 Green (B3) y SWIR1 (B11)',
      desc: 'Optimizado para detectar cuerpos de agua en zonas urbanas o construidas.',
      icon: <Droplet className="h-5 w-5 text-sky-400" />,
      badgeBg: 'bg-sky-500/10 border-sky-500/25',
    },
    {
      key: 'ndmi',
      title: 'NDMI — Humedad Canopia',
      formula: '(B8 - B11) / (B8 + B11)',
      bands: 'Sentinel-2 NIR (B8) y SWIR1 (B11)',
      desc: 'Evalúa el contenido de humedad interna de la masa vegetal y estrés hídrico.',
      icon: <Flame className="h-5 w-5 text-orange-400" />,
      badgeBg: 'bg-orange-500/10 border-orange-500/25',
    },
    {
      key: 'nbr',
      title: 'NBR — Severidad de Incendio',
      formula: '(B8 - B12) / (B8 + B12)',
      bands: 'Sentinel-2 NIR (B8) y SWIR2 (B12)',
      desc: 'Detecta vulnerabilidad a incendios forestales y severidad de quemado.',
      icon: <Flame className="h-5 w-5 text-red-400" />,
      badgeBg: 'bg-red-500/10 border-red-500/25',
    },
    {
      key: 'ndbi',
      title: 'NDBI — Huella Construida',
      formula: '(B11 - B8) / (B11 + B8)',
      bands: 'Sentinel-2 SWIR1 (B11) y NIR (B8)',
      desc: 'Distingue áreas urbanas, asfalto, hormigón y faenas mineras de superficie.',
      icon: <Mountain className="h-5 w-5 text-indigo-400" />,
      badgeBg: 'bg-indigo-500/10 border-indigo-500/25',
    },
    {
      key: 'savi',
      title: 'SAVI — Suelo Ajustado',
      formula: '((B8 - B4) / (B8 + B4 + 0.5)) * 1.5',
      bands: 'Sentinel-2 NIR (B8) y Red (B4)',
      desc: 'Corrección del efecto de brillo del suelo para vegetación escasa o zonas áridas.',
      icon: <Leaf className="h-5 w-5 text-teal-400" />,
      badgeBg: 'bg-teal-500/10 border-teal-500/25',
    },
    {
      key: 'evi',
      title: 'EVI — Vegetación Mejorado',
      formula: '2.5 * ((B8-B4)/(B8+6B4-7.5B2+1))',
      bands: 'Sentinel-2 NIR, Red y Blue',
      desc: 'Alta sensibilidad en selvas y doseles de alta biomasa sin saturación.',
      icon: <Leaf className="h-5 w-5 text-emerald-400" />,
      badgeBg: 'bg-emerald-500/10 border-emerald-500/25',
    },
    {
      key: 'bsi',
      title: 'BSI — Suelo Desnudo',
      formula: '((SWIR1+Red)-(NIR+Blue))/((SWIR1+Red)+(NIR+Blue))',
      bands: 'Sentinel-2 B11, B4, B8, B2',
      desc: 'Monitorea áreas sin cobertura vegetal, erosión y movimiento de tierras.',
      icon: <Layers className="h-5 w-5 text-amber-400" />,
      badgeBg: 'bg-amber-500/10 border-amber-500/25',
    },
    {
      key: 'ndre',
      title: 'NDRE — Clorofila Cultivos',
      formula: '(B8 - B5) / (B8 + B5)',
      bands: 'Sentinel-2 NIR (B8) y Red Edge (B5)',
      desc: 'Sensible al contenido de nitrógeno y clorofila en agricultura de precisión.',
      icon: <Leaf className="h-5 w-5 text-lime-400" />,
      badgeBg: 'bg-lime-500/10 border-lime-500/25',
    },
    {
      key: 'aspect',
      title: 'Aspect — Orientación Ladera',
      formula: 'ee.Terrain.aspect(elevation)',
      bands: 'Copernicus DEM GLO-30 Topografía',
      desc: 'Orientación de laderas (0-360°) para cálculo de radiación y viabilidad solar.',
      icon: <Sun className="h-5 w-5 text-yellow-400" />,
      badgeBg: 'bg-yellow-500/10 border-yellow-500/25',
    },
  ]

  return (
    <section id="indices" className="py-20 lg:py-32 bg-[#0b0c10] border-y border-white/5 relative overflow-hidden">
      {/* Decorative blurred blob */}
      <div className="absolute left-1/3 top-1/4 w-[350px] h-[350px] rounded-full bg-purple-500/5 blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 mb-4">
            <Satellite className="h-4 w-4 text-teal-400" />
            <span className="text-xs font-semibold text-teal-400 tracking-wider uppercase">
              Algoritmos Espectrales GEE
            </span>
          </div>
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight">
            Índices Satelitales y Espaciales
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            Procesamiento espectral multiespectral en tiempo real alimentado por Google Earth Engine.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {allIndices.map((idx) => (
            <div key={idx.key} className="glass-panel p-6 rounded-2xl flex flex-col justify-between hover:border-teal-500/30 transition-all">
              <div>
                <div className={`w-10 h-10 rounded-xl border flex items-center justify-center mb-4 ${idx.badgeBg}`}>
                  {idx.icon}
                </div>
                <h3 className="text-lg font-bold text-white mb-1 font-outfit">
                  {idx.title}
                </h3>
                <p className="text-[11px] font-mono text-teal-400 mb-3">{idx.formula}</p>
                <p className="text-xs text-gray-400 mb-4 font-mono">
                  <strong className="text-gray-300">Entrada:</strong> {idx.bands}
                </p>
                <p className="text-gray-300 text-xs leading-relaxed">
                  {idx.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Science explainer panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gradient-to-br from-emerald-950/20 to-black/40 border border-emerald-500/10 p-8 rounded-2xl">
            <h4 className="flex items-center gap-2 text-emerald-400 font-bold text-lg mb-4 font-outfit">
              <Lightbulb className="h-5 w-5 animate-pulse" />
              ¿Cómo funciona la Reflectancia Espectral?
            </h4>
            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">
              Cada elemento en la superficie terrestre (agua, vegetación, hormigón, suelo) refleja la radiación solar de forma única en distintas longitudes de onda del espectro electromagnético. Sentinel-2 captura 13 bandas espectrales desde el visible hasta el infrarrojo de onda corta (SWIR). GeoFeedback combina estas bandas para calcular índices cuantitativos de precisión en tiempo real.
            </p>
          </div>

          <div className="bg-gradient-to-br from-blue-950/20 to-black/40 border border-blue-500/10 p-8 rounded-2xl flex flex-col justify-between">
            <div>
              <h4 className="flex items-center gap-2 text-blue-400 font-bold text-lg mb-4 font-outfit">
                <Satellite className="h-5 w-5" />
                Constelación Sentinel-2 & DEM GLO-30
              </h4>
              <p className="text-gray-300 text-sm leading-relaxed mb-6">
                Los satélites Sentinel-2A y 2B de la Agencia Espacial Europea (ESA) sobrevuelan la Tierra con una frecuencia de revisita de 5 días y una resolución espacial de hasta 10 metros por píxel, complementados por el Modelo Digital de Elevación Copernicus DEM.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-black/30 p-4 rounded-xl text-center border border-white/5">
                <div className="text-2xl mb-1">🇪🇺</div>
                <div className="text-[10px] text-gray-500 leading-tight">Agencia Espacial Europea</div>
              </div>
              <div className="bg-black/30 p-4 rounded-xl text-center border border-white/5">
                <div className="text-lg font-bold text-teal-400 font-outfit mb-1">10m</div>
                <div className="text-[10px] text-gray-500 leading-tight">Resolución Píxel</div>
              </div>
              <div className="bg-black/30 p-4 rounded-xl text-center border border-white/5">
                <div className="text-lg font-bold text-teal-400 font-outfit mb-1">GEE</div>
                <div className="text-[10px] text-gray-500 leading-tight">Google Earth Engine</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

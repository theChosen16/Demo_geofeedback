import React from 'react'
import { useTranslation } from 'react-i18next'
import { Satellite, MapPin, BarChart3, Presentation, Mountain, Wind, Sun, Trees, Search, Map, Image, Database, Compass, CheckCircle } from 'lucide-react'

export const Solution: React.FC = () => {
  const { t } = useTranslation()

  return (
    <section id="solucion" className="py-20 lg:py-32 bg-[#111318] relative overflow-hidden">
      {/* Background radial highlight */}
      <div className="absolute right-1/4 bottom-1/4 w-[400px] h-[400px] rounded-full bg-teal-500/5 blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-24">
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight">
            {t('solution.title')}
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            {t('solution.subtitle')}
          </p>
        </div>

        {/* Category 1: Satelital */}
        <div className="mb-16">
          <h3 className="flex items-center gap-3 text-2xl font-bold text-white font-outfit mb-8 border-b border-white/5 pb-4">
            <Satellite className="h-6 w-6 text-teal-400" />
            {t('solution.catSatellite')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex gap-4 items-start">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400">
                <i className="fab fa-google text-2xl"></i>
              </div>
              <div>
                <h4 className="text-lg font-bold text-white mb-1">Google Earth Engine</h4>
                <p className="text-gray-400 text-sm">Sentinel-2 Processing (NDVI, NDWI, NDMI)</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex gap-4 items-start">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400">
                <Map className="h-6 w-6" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-white mb-1">Map Tiles API</h4>
                <p className="text-gray-400 text-sm">Custom map tiles and overlays</p>
              </div>
            </div>
          </div>
        </div>

        {/* Category 2: Ubicacion */}
        <div className="mb-16">
          <h3 className="flex items-center gap-3 text-2xl font-bold text-white font-outfit mb-8 border-b border-white/5 pb-4">
            <MapPin className="h-6 w-6 text-teal-400" />
            {t('solution.catLocation')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <Compass className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Geocoding API</h4>
                <p className="text-gray-400 text-xs">Address to coordinate conversion</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <MapPin className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Geolocation API</h4>
                <p className="text-gray-400 text-xs">Real-time user location</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <Search className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Places API (New)</h4>
                <p className="text-gray-400 text-xs">Places and infrastructure search</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <CheckCircle className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Address Validation</h4>
                <p className="text-gray-400 text-xs">Postal address validation</p>
              </div>
            </div>
          </div>
        </div>

        {/* Category 3: Analisis */}
        <div className="mb-16">
          <h3 className="flex items-center gap-3 text-2xl font-bold text-white font-outfit mb-8 border-b border-white/5 pb-4">
            <BarChart3 className="h-6 w-6 text-teal-400" />
            {t('solution.catAnalysis')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <Mountain className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Elevation API</h4>
                <p className="text-gray-400 text-xs">Real-time topographic data</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <Wind className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Air Quality API</h4>
                <p className="text-gray-400 text-xs">Air quality at 500m resolution</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <Sun className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Solar API</h4>
                <p className="text-gray-400 text-xs">Rooftop photovoltaic potential</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400 w-fit">
                <Trees className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white mb-1">Pollen API</h4>
                <p className="text-gray-400 text-xs">Pollen and allergen levels</p>
              </div>
            </div>
          </div>
        </div>

        {/* Category 4: Visualizacion */}
        <div>
          <h3 className="flex items-center gap-3 text-2xl font-bold text-white font-outfit mb-8 border-b border-white/5 pb-4">
            <Presentation className="h-6 w-6 text-teal-400" />
            {t('solution.catVisualization')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex gap-4 items-start">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400">
                <Map className="h-6 w-6" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-white mb-1">Maps JavaScript API</h4>
                <p className="text-gray-400 text-sm">Interactive web maps</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex gap-4 items-start">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400">
                <Image className="h-6 w-6" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-white mb-1">Maps Static API</h4>
                <p className="text-gray-400 text-sm">Static maps for PDF reports</p>
              </div>
            </div>
            <div className="glass-panel p-6 rounded-xl hover:border-white/20 transition-all duration-200 flex gap-4 items-start">
              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-teal-400">
                <Database className="h-6 w-6" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-white mb-1">Maps Datasets API</h4>
                <p className="text-gray-400 text-sm">Geospatial dataset management</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

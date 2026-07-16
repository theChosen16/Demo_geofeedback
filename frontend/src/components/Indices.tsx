import React from 'react'
import { useTranslation } from 'react-i18next'
import { Leaf, Droplet, Flame, Lightbulb, Satellite } from 'lucide-react'

export const Indices: React.FC = () => {
  const { t } = useTranslation()

  return (
    <section id="indices" className="py-20 lg:py-32 bg-[#0b0c10] border-y border-white/5 relative overflow-hidden">
      {/* Decorative blurred blob */}
      <div className="absolute left-1/3 top-1/4 w-[350px] h-[350px] rounded-full bg-purple-500/5 blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-24">
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight">
            {t('indices.title')}
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            {t('indices.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {/* NDVI */}
          <div className="glass-panel p-8 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="bg-emerald-500/10 border border-emerald-500/25 w-12 h-12 rounded-xl flex items-center justify-center mb-6 text-emerald-400">
                <Leaf className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2 font-outfit">
                {t('indices.ndviTitle')}
              </h3>
              <p className="text-xs font-mono text-gray-500 mb-4">{t('indices.ndviFormula')}</p>
              <ul className="text-sm space-y-2 mb-6">
                <li><strong className="text-gray-300">Bandas:</strong> (B8 - B4) / (B8 + B4)</li>
                <li><strong className="text-gray-300">Rango:</strong> -1 a +1</li>
              </ul>
              <p className="text-gray-400 text-sm leading-relaxed">
                {t('indices.ndviDesc')}
              </p>
            </div>
          </div>

          {/* NDWI */}
          <div className="glass-panel p-8 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="bg-blue-500/10 border border-blue-500/25 w-12 h-12 rounded-xl flex items-center justify-center mb-6 text-blue-400">
                <Droplet className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2 font-outfit">
                {t('indices.ndwiTitle')}
              </h3>
              <p className="text-xs font-mono text-gray-500 mb-4">{t('indices.ndwiFormula')}</p>
              <ul className="text-sm space-y-2 mb-6">
                <li><strong className="text-gray-300">Bandas:</strong> (B3 - B8) / (B3 + B8)</li>
                <li><strong className="text-gray-300">Rango:</strong> -1 a +1</li>
              </ul>
              <p className="text-gray-400 text-sm leading-relaxed">
                {t('indices.ndwiDesc')}
              </p>
            </div>
          </div>

          {/* NDMI */}
          <div className="glass-panel p-8 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="bg-cyan-500/10 border border-cyan-500/25 w-12 h-12 rounded-xl flex items-center justify-center mb-6 text-cyan-400">
                <Flame className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2 font-outfit">
                {t('indices.ndmiTitle')}
              </h3>
              <p className="text-xs font-mono text-gray-500 mb-4">{t('indices.ndmiFormula')}</p>
              <ul className="text-sm space-y-2 mb-6">
                <li><strong className="text-gray-300">Bandas:</strong> (B8 - B11) / (B8 + B11)</li>
                <li><strong className="text-gray-300">Rango:</strong> -1 a +1</li>
              </ul>
              <p className="text-gray-400 text-sm leading-relaxed">
                {t('indices.ndmiDesc')}
              </p>
            </div>
          </div>
        </div>

        {/* Science explainer panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gradient-to-br from-emerald-950/20 to-black/40 border border-emerald-500/10 p-8 rounded-2xl">
            <h4 className="flex items-center gap-2 text-emerald-400 font-bold text-lg mb-4 font-outfit">
              <Lightbulb className="h-5 w-5 animate-pulse" />
              {t('indices.howItWorksTitle')}
            </h4>
            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">
              {t('indices.howItWorksDesc')}
            </p>
          </div>

          <div className="bg-gradient-to-br from-blue-950/20 to-black/40 border border-blue-500/10 p-8 rounded-2xl flex flex-col justify-between">
            <div>
              <h4 className="flex items-center gap-2 text-blue-400 font-bold text-lg mb-4 font-outfit">
                <Satellite className="h-5 w-5" />
                {t('indices.sentinelTitle')}
              </h4>
              <p className="text-gray-300 text-sm leading-relaxed mb-6">
                {t('indices.sentinelDesc')}
              </p>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-black/30 p-4 rounded-xl text-center border border-white/5">
                <div className="text-2xl mb-1">🇪🇺</div>
                <div className="text-[10px] text-gray-500 leading-tight">ESA operated</div>
              </div>
              <div className="bg-black/30 p-4 rounded-xl text-center border border-white/5">
                <div className="text-lg font-bold text-teal-400 font-outfit mb-1">€200M</div>
                <div className="text-[10px] text-gray-500 leading-tight">Cost/sat</div>
              </div>
              <div className="bg-black/30 p-4 rounded-xl text-center border border-white/5">
                <div className="text-lg font-bold text-teal-400 font-outfit mb-1">FREE</div>
                <div className="text-[10px] text-gray-500 leading-tight">Open Data</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

import React from 'react'
import { useTranslation } from 'react-i18next'
import { ShieldAlert, Droplet, Landmark } from 'lucide-react'

export const Problem: React.FC = () => {
  const { t } = useTranslation()

  return (
    <section id="problema" className="py-20 lg:py-32 bg-[#0b0c10] border-y border-white/5 relative overflow-hidden">
      {/* Decorative background blur */}
      <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-72 h-72 rounded-full bg-purple-500/5 blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-24">
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight">
            {t('problem.title')}
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            {t('problem.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Card 1: Ley 21.364 */}
          <div className="glass-panel p-8 lg:p-10 rounded-2xl transition-all duration-300 hover:-translate-y-2 hover:border-teal-500/30 group">
            <div className="bg-red-500/10 border border-red-500/25 w-14 h-14 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <ShieldAlert className="h-7 w-7 text-red-400" />
            </div>
            <h3 className="text-xl lg:text-2xl font-bold text-white mb-3 font-outfit">
              {t('problem.lawTitle')}
            </h3>
            <p className="text-gray-400 leading-relaxed text-sm lg:text-base">
              {t('problem.lawDesc')}
            </p>
          </div>

          {/* Card 2: Mega-sequia */}
          <div className="glass-panel p-8 lg:p-10 rounded-2xl transition-all duration-300 hover:-translate-y-2 hover:border-teal-500/30 group">
            <div className="bg-teal-500/10 border border-teal-500/25 w-14 h-14 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <Droplet className="h-7 w-7 text-teal-400" />
            </div>
            <h3 className="text-xl lg:text-2xl font-bold text-white mb-3 font-outfit">
              {t('problem.droughtTitle')}
            </h3>
            <p className="text-gray-400 leading-relaxed text-sm lg:text-base">
              {t('problem.droughtDesc')}
            </p>
          </div>

          {/* Card 3: Alto Costo */}
          <div className="glass-panel p-8 lg:p-10 rounded-2xl transition-all duration-300 hover:-translate-y-2 hover:border-teal-500/30 group">
            <div className="bg-purple-500/10 border border-purple-500/25 w-14 h-14 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <Landmark className="h-7 w-7 text-purple-400" />
            </div>
            <h3 className="text-xl lg:text-2xl font-bold text-white mb-3 font-outfit">
              {t('problem.costTitle')}
            </h3>
            <p className="text-gray-400 leading-relaxed text-sm lg:text-base">
              {t('problem.costDesc')}
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

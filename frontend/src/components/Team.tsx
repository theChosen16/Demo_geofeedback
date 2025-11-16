import React from 'react'
import { useTranslation } from 'react-i18next'
import { Users, User } from 'lucide-react'

export const Team: React.FC = () => {
  const { t } = useTranslation()

  return (
    <section id="equipo" className="py-20 lg:py-32 bg-[#111318] relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-24">
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight flex items-center justify-center gap-3">
            <Users className="h-8 w-8 text-teal-400" />
            {t('team.title')}
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            {t('team.subtitle')}
          </p>
        </div>

        <div className="flex flex-col md:flex-row justify-center items-center gap-12 max-w-4xl mx-auto">
          {/* Consuelo */}
          <div className="glass-panel w-full md:w-80 p-8 rounded-2xl text-center flex flex-col items-center hover:border-teal-500/30 transition-all duration-300">
            <div className="bg-white/5 border border-white/10 w-24 h-24 rounded-full flex items-center justify-center mb-6 text-gray-300 shadow-inner">
              <User className="h-12 w-12" />
            </div>
            <h3 className="text-xl font-bold text-white mb-1 font-outfit">Consuelo Sebastian Silva</h3>
            <p className="text-sm font-semibold text-teal-400 mb-6 uppercase tracking-wider">{t('team.roleCoFounderFem')}</p>
            <a
              href="https://www.linkedin.com/in/consuelo-sebastian-silva-b15407342/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 btn btn-outline btn-sm hover:bg-teal-400 hover:text-[#111318] border-teal-400/20 hover:border-teal-400 rounded-xl px-4 w-full h-10 font-bold"
            >
              <i className="fab fa-linkedin text-base"></i>
              {t('team.viewLinkedin')}
            </a>
          </div>

          {/* Alejandro */}
          <div className="glass-panel w-full md:w-80 p-8 rounded-2xl text-center flex flex-col items-center hover:border-teal-500/30 transition-all duration-300">
            <div className="bg-white/5 border border-white/10 w-24 h-24 rounded-full flex items-center justify-center mb-6 text-gray-300 shadow-inner">
              <User className="h-12 w-12" />
            </div>
            <h3 className="text-xl font-bold text-white mb-1 font-outfit">Alejandro Hernandez Aguirre</h3>
            <p className="text-sm font-semibold text-teal-400 mb-6 uppercase tracking-wider">{t('team.roleCoFounder')}</p>
            <a
              href="https://www.linkedin.com/in/alejandro-hern%C3%A1ndez-aguirre-bb8967246/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 btn btn-outline btn-sm hover:bg-teal-400 hover:text-[#111318] border-teal-400/20 hover:border-teal-400 rounded-xl px-4 w-full h-10 font-bold"
            >
              <i className="fab fa-linkedin text-base"></i>
              {t('team.viewLinkedin')}
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}

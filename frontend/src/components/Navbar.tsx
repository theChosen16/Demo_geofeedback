import { useTranslation } from 'react-i18next'
import { useStore } from '../store/useStore'
import { Globe, Code } from 'lucide-react'

export const Navbar: React.FC = () => {
  const { t, i18n } = useTranslation()
  const { language, setLanguage, activeTab, setActiveTab } = useStore()

  const toggleLanguage = () => {
    const nextLang = language === 'es' ? 'en' : 'es'
    setLanguage(nextLang)
    i18n.changeLanguage(nextLang)
  }

  const handleNavClick = (tab: 'inicio' | 'demo' | 'servicios' | 'contacto', href: string) => {
    setActiveTab(tab)
    const element = document.querySelector(href)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <>
      {/* Mobile Top Header */}
      <div className="flex lg:hidden justify-between align-center px-6 py-4 bg-[#16171d]/90 backdrop-blur-md border-b border-white/5 sticky top-0 z-40">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => handleNavClick('inicio', '#inicio')}>
          <Globe className="h-6 w-6 text-teal-400 animate-spin-slow" />
          <span className="font-extrabold text-xl tracking-tight text-white font-outfit">GeoFeedback</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleLanguage}
            className="btn btn-sm btn-ghost border border-white/10 hover:bg-white/5 text-xs px-2 h-8 min-h-0 text-white rounded-lg flex items-center gap-1"
          >
            <span>{language === 'es' ? '🇺🇸' : '🇨🇱'}</span>
            <span>{language === 'es' ? 'EN' : 'ES'}</span>
          </button>
        </div>
      </div>

      {/* Desktop Navigation */}
      <nav className="hidden lg:block w-full border-b border-white/5 bg-[#111318]/70 backdrop-blur-md fixed top-0 left-0 right-0 z-50 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => handleNavClick('inicio', '#inicio')}>
            <div className="bg-teal-500/10 p-2 rounded-xl border border-teal-500/25">
              <Globe className="h-6 w-6 text-teal-400" />
            </div>
            <span className="font-bold text-2xl tracking-tight text-white font-outfit">GeoFeedback</span>
          </div>

          <div className="flex items-center gap-8">
            <button
              onClick={() => handleNavClick('inicio', '#problema')}
              className="text-gray-400 hover:text-white font-medium text-sm transition-colors duration-200"
            >
              {t('navbar.problem')}
            </button>
            <button
              onClick={() => handleNavClick('inicio', '#solucion')}
              className="text-gray-400 hover:text-white font-medium text-sm transition-colors duration-200"
            >
              {t('navbar.solution')}
            </button>
            <button
              onClick={() => handleNavClick('demo', '#demo')}
              className="text-gray-400 hover:text-white font-medium text-sm transition-colors duration-200"
            >
              {t('navbar.demo')}
            </button>
            <button
              onClick={() => handleNavClick('servicios', '#servicios')}
              className="text-gray-400 hover:text-white font-medium text-sm transition-colors duration-200"
            >
              {t('navbar.services')}
            </button>

            <a
              href="/api/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline btn-sm text-teal-400 hover:bg-teal-400 hover:text-[#111318] border-teal-400/30 hover:border-teal-400 rounded-xl px-4 h-9 font-semibold text-xs tracking-wider"
            >
              <Code className="h-3.5 w-3.5 mr-1" />
              {t('navbar.api')}
            </a>

            <button
              onClick={toggleLanguage}
              className="btn btn-ghost btn-sm hover:bg-white/5 text-gray-300 font-semibold flex items-center gap-1.5 border border-white/10 rounded-xl px-3"
            >
              <span>{language === 'es' ? '🇺🇸' : '🇨🇱'}</span>
              <span className="text-xs">{language === 'es' ? 'EN' : 'ES'}</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Tab Navigation */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#16171d]/90 backdrop-blur-md border-t border-white/5 flex justify-around items-center h-16 py-2 shadow-2xl">
        <button
          onClick={() => handleNavClick('inicio', '#inicio')}
          className={`flex flex-col items-center justify-center w-1/4 gap-1 text-xs transition-colors duration-200 ${activeTab === 'inicio' ? 'text-teal-400' : 'text-gray-400'}`}
        >
          <Globe className="h-5 w-5" />
          <span>Inicio</span>
        </button>
        <button
          onClick={() => handleNavClick('demo', '#demo')}
          className={`flex flex-col items-center justify-center w-1/4 gap-1 text-xs transition-colors duration-200 ${activeTab === 'demo' ? 'text-teal-400' : 'text-gray-400'}`}
        >
          <i className="fas fa-map-marked-alt text-base"></i>
          <span>Demo</span>
        </button>
        <button
          onClick={() => handleNavClick('servicios', '#servicios')}
          className={`flex flex-col items-center justify-center w-1/4 gap-1 text-xs transition-colors duration-200 ${activeTab === 'servicios' ? 'text-teal-400' : 'text-gray-400'}`}
        >
          <i className="fas fa-rocket text-base"></i>
          <span>Servicios</span>
        </button>
        <button
          onClick={() => handleNavClick('contacto', '#contacto')}
          className={`flex flex-col items-center justify-center w-1/4 gap-1 text-xs transition-colors duration-200 ${activeTab === 'contacto' ? 'text-teal-400' : 'text-gray-400'}`}
        >
          <i className="fas fa-envelope text-base"></i>
          <span>Contacto</span>
        </button>
      </nav>
    </>
  )
}

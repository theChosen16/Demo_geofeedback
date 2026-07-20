import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store/useStore'
import { Globe, Code, LogOut } from 'lucide-react'
import { GoogleLoginButton } from './GoogleLoginButton'

const UserMenu: React.FC = () => {
  const { t } = useTranslation()
  const { user, setUser, setAnalysisHistory } = useStore()
  const [open, setOpen] = useState(false)

  if (!user) return <GoogleLoginButton />

  const initial = (user.name || user.email).charAt(0).toUpperCase()

  const handleLogout = async () => {
    try {
      const res = await fetch('/api/v1/auth/logout', { method: 'POST' })
      if (!res.ok) throw new Error(`logout respondió ${res.status}`)
      // Solo limpiar el estado local si el backend realmente invalidó la cookie de sesión:
      // si esto se limpiara igual ante un fallo de red, la UI mostraría "sesión cerrada"
      // mientras la cookie httpOnly sigue siendo válida, y una recarga de página
      // reautenticaría silenciosamente a quien esté frente a la pantalla.
      setUser(null)
      setAnalysisHistory([])
    } catch (err) {
      console.error('Error cerrando sesión:', err)
      alert('No se pudo cerrar la sesión (problema de red). Intenta de nuevo.')
    } finally {
      setOpen(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full border border-white/10 hover:bg-white/5 pl-1 pr-3 py-1"
        title={user.email}
      >
        {user.picture_url ? (
          <img src={user.picture_url} alt={user.name || user.email} className="h-7 w-7 rounded-full" referrerPolicy="no-referrer" />
        ) : (
          <span className="h-7 w-7 rounded-full bg-teal-500/20 text-teal-300 flex items-center justify-center text-xs font-bold">
            {initial}
          </span>
        )}
        <span className="text-xs text-gray-200 font-semibold max-w-[120px] truncate">{user.name || user.email}</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-[#16171d] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
          <div className="px-4 py-3 text-xs text-gray-400 border-b border-white/5 truncate">{user.email}</div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-4 py-2.5 text-xs text-gray-300 hover:bg-white/5 hover:text-white flex items-center gap-2"
          >
            <LogOut className="h-3.5 w-3.5" />
            {t('auth.logout')}
          </button>
        </div>
      )}
    </div>
  )
}

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
          <UserMenu />
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

            <UserMenu />
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

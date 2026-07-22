import { useTranslation } from 'react-i18next'
import { Globe } from 'lucide-react'

export const Footer: React.FC = () => {
  const { t } = useTranslation()

  return (
    <footer className="bg-[#0b0c10] border-t border-white/5 py-12 lg:py-16 text-gray-400">
      <div className="max-w-7xl mx-auto px-6 flex flex-col items-center justify-center gap-6">
        <div className="flex items-center gap-2 text-white font-bold text-lg font-outfit">
          <Globe className="h-5 w-5 text-teal-400" />
          <span>GeoFeedback Chile</span>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-8 text-sm">
          <a href="#demo" className="hover:text-white transition-colors duration-200">{t('demo.title')}</a>
          <a href="/api/docs" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors duration-200">API</a>
          <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors duration-200">GitHub</a>
        </div>

        <div className="flex items-center gap-4">
          <a
            href="https://github.com/theChosen16/Demo_geofeedback"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub Repository"
            className="bg-white/5 hover:bg-white/10 text-white p-3 rounded-full border border-white/10 transition-colors duration-200 flex items-center justify-center w-11 h-11"
          >
            <i className="fab fa-github text-lg"></i>
          </a>
        </div>

        <div className="text-xs text-gray-500 text-center max-w-md border-t border-white/5 pt-6 w-full leading-relaxed">
          Temas profesionales y contratación de servicios gestionados por{' '}
          <a
            href="https://agenticworkflow.cl/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-teal-400 underline hover:text-teal-300"
          >
            Agentic Workflow
          </a>.
        </div>
      </div>
    </footer>
  )
}

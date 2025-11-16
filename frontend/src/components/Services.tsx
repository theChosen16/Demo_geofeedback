import React from 'react'
import { useTranslation } from 'react-i18next'
import { Check, Info, FileText, CheckSquare, AlertTriangle, Play, Bell, Calendar, Sparkles } from 'lucide-react'

export const Services: React.FC = () => {
  const { t } = useTranslation()

  return (
    <section id="servicios" className="py-20 lg:py-32 bg-[#0b0c10] border-y border-white/5 relative overflow-hidden">
      {/* Decorative blurred background highlights */}
      <div className="absolute top-1/4 left-1/3 w-[350px] h-[350px] bg-teal-500/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] bg-purple-500/5 blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-24">
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight flex items-center justify-center gap-3">
            <Sparkles className="h-8 w-8 text-teal-400" />
            {t('services.title')}
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            {t('services.subtitle')}
          </p>
        </div>

        {/* Planes de suscripcion */}
        <h3 className="text-2xl font-bold text-white mb-8 font-outfit text-center lg:text-left flex items-center gap-2 justify-center lg:justify-start">
          <i className="fas fa-tags text-teal-400"></i>
          {t('services.plansTitle')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch mb-20">
          {/* Plan 1: Monitoreo */}
          <div className="glass-panel p-8 rounded-2xl flex flex-col justify-between border border-white/5 hover:border-white/15 transition-all">
            <div>
              <div className="text-center mb-6">
                <span className="bg-teal-500/10 text-teal-400 border border-teal-500/25 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
                  {t('services.planMonitoring')}
                </span>
                <div className="text-3xl font-extrabold text-white mt-4 font-outfit">
                  $700.000 <span className="text-xs text-gray-500 font-normal">{t('services.perMonth')}</span>
                </div>
              </div>

              <ul className="text-sm space-y-3.5 mb-8 text-gray-400">
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span><strong>Licencia Comercial GEE</strong> incluida</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Infraestructura Google Cloud gestionada</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Dashboard en tiempo real personalizado</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Alertas por email</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Soporte por email</span>
                </li>
              </ul>
            </div>

            <a
              href="#contacto"
              className="btn btn-outline border-teal-500/20 hover:bg-teal-500 hover:border-teal-500 hover:text-[#111318] text-teal-400 rounded-xl w-full h-11 font-bold"
            >
              {t('services.startNow')}
            </a>
          </div>

          {/* Plan 2: Profesional */}
          <div className="glass-panel p-8 rounded-2xl flex flex-col justify-between border-2 border-teal-500/50 relative transform md:scale-105 shadow-2xl bg-[#16171d]/90">
            <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-teal-500 to-emerald-600 text-[#111318] font-bold text-[10px] uppercase tracking-widest px-3 py-1 rounded-full shadow-md">
              Recomendado
            </div>
            
            <div>
              <div className="text-center mb-6">
                <span className="bg-gradient-to-r from-teal-500 to-emerald-600 text-[#111318] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                  {t('services.planProfessional')}
                </span>
                <div className="text-3xl font-extrabold text-white mt-4 font-outfit">
                  $2.800.000 <span className="text-xs text-gray-400 font-normal">{t('services.perMonth')}</span>
                </div>
              </div>

              <ul className="text-sm space-y-3.5 mb-8 text-gray-300">
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span><strong>Todas las funciones de Monitoreo</strong></span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span><strong>Alta Capacidad de Cómputo</strong> (High-EECU)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span><strong>Ingesta de Datos Privados</strong> (Drones/Satélites)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Exportación Full-Resolution sin límites</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>API para integrar data a tus sistemas</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Alertas en tiempo real (email + SMS)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Reportes automáticos</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Soporte prioritario</span>
                </li>
              </ul>
            </div>

            <a
              href="#contacto"
              className="btn btn-primary bg-gradient-to-r from-teal-500 to-emerald-600 border-none hover:opacity-90 text-[#111318] rounded-xl w-full h-11 font-bold shadow-lg"
            >
              {t('services.choosePlan')}
            </a>
          </div>

          {/* Plan 3: Ingenieria */}
          <div className="glass-panel p-8 rounded-2xl flex flex-col justify-between border border-white/5 hover:border-white/15 transition-all">
            <div>
              <div className="text-center mb-6">
                <span className="bg-purple-500/10 text-purple-400 border border-purple-500/25 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
                  {t('services.planEngineering')}
                </span>
                <div className="text-3xl font-extrabold text-white mt-4 font-outfit">
                  Contactar
                </div>
              </div>

              <ul className="text-sm space-y-3.5 mb-8 text-gray-400">
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Servicios de Ingeniería Ambiental</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Estudios de Impacto Ambiental (EIA/DIA)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Consultoría GIS personalizada</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Monitoreo de cumplimiento ambiental</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="h-4.5 w-4.5 text-teal-400 flex-shrink-0 mt-0.5" />
                  <span>Gestor de proyecto dedicado</span>
                </li>
              </ul>
            </div>

            <a
              href="#contacto"
              className="btn btn-outline border-purple-500/20 hover:bg-purple-500 hover:border-purple-500 hover:text-white text-purple-400 rounded-xl w-full h-11 font-bold"
            >
              {t('services.contactUs')}
            </a>
          </div>
        </div>

        {/* Why GEE section banner */}
        <div className="glass-panel p-6 lg:p-8 rounded-2xl mb-20 border-l-4 border-teal-500">
          <h4 className="flex items-center gap-2 font-bold text-white text-lg mb-4 font-outfit">
            <Info className="h-5 w-5 text-teal-400" />
            {t('services.whyGeeTitle')}
          </h4>
          <p className="text-gray-300 text-sm leading-relaxed mb-4">
            {t('services.whyGeeDesc1')}
          </p>
          <p className="text-gray-300 text-sm leading-relaxed mb-6">
            {t('services.whyGeeDesc2')}
          </p>
          <div className="text-xs text-gray-500 border-t border-white/5 pt-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <span>{t('services.whyGeePriceDetail')}</span>
            <a
              href="https://cloud.google.com/earth-engine/pricing?hl=es_419"
              target="_blank"
              rel="noopener noreferrer"
              className="text-teal-400 hover:underline inline-flex items-center gap-1 font-semibold"
            >
              <span>{t('services.officialPricing')}</span>
              <Play className="h-2.5 w-2.5 rotate-90" />
            </a>
          </div>
        </div>

        {/* Environmental Engineering services */}
        <h3 className="text-2xl font-bold text-white mb-8 font-outfit text-center lg:text-left flex items-center gap-2 justify-center lg:justify-start">
          <i className="fas fa-leaf text-teal-400"></i>
          {t('services.engServicesTitle')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-20">
          <div className="glass-panel p-6 rounded-xl">
            <div className="bg-white/5 p-3 rounded-lg border border-white/10 w-fit text-teal-400 mb-4">
              <FileText className="h-5 w-5" />
            </div>
            <h4 className="font-bold text-white text-base mb-2 font-outfit">{t('services.cardEiaTitle')}</h4>
            <p className="text-gray-400 text-xs leading-relaxed">{t('services.cardEiaDesc')}</p>
          </div>

          <div className="glass-panel p-6 rounded-xl">
            <div className="bg-white/5 p-3 rounded-lg border border-white/10 w-fit text-teal-400 mb-4">
              <CheckSquare className="h-5 w-5" />
            </div>
            <h4 className="font-bold text-white text-base mb-2 font-outfit">{t('services.cardRcaTitle')}</h4>
            <p className="text-gray-400 text-xs leading-relaxed">{t('services.cardRcaDesc')}</p>
          </div>

          <div className="glass-panel p-6 rounded-xl">
            <div className="bg-white/5 p-3 rounded-lg border border-white/10 w-fit text-teal-400 mb-4">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <h4 className="font-bold text-white text-base mb-2 font-outfit">{t('services.cardRiskTitle')}</h4>
            <p className="text-gray-400 text-xs leading-relaxed">{t('services.cardRiskDesc')}</p>
          </div>

          <div className="glass-panel p-6 rounded-xl">
            <div className="bg-white/5 p-3 rounded-lg border border-white/10 w-fit text-teal-400 mb-4">
              <i className="fas fa-project-diagram text-lg"></i>
            </div>
            <h4 className="font-bold text-white text-base mb-2 font-outfit">{t('services.cardGisTitle')}</h4>
            <p className="text-gray-400 text-xs leading-relaxed">{t('services.cardGisDesc')}</p>
          </div>
        </div>

        {/* Dashboard demo details */}
        <h3 className="text-2xl font-bold text-white mb-4 font-outfit text-center lg:text-left flex items-center gap-2 justify-center lg:justify-start">
          <i className="fas fa-server text-teal-400"></i>
          {t('services.dashboardDemoTitle')}
        </h3>
        <p className="text-gray-400 text-sm max-w-3xl leading-relaxed text-center lg:text-left mb-8">
          {t('services.dashboardDemoDesc')}
        </p>

        <div className="glass-panel p-8 rounded-2xl shadow-2xl">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-[#111318]/50 border border-white/5 p-6 rounded-xl text-center">
              <div className="text-gray-400 text-xs mb-2 font-semibold">Procesamiento (EECU)</div>
              <div className="text-3xl font-extrabold text-teal-400 font-outfit">98%</div>
            </div>
            <div className="bg-[#111318]/50 border border-white/5 p-6 rounded-xl text-center">
              <div className="text-gray-400 text-xs mb-2 font-semibold">Latencia Análisis</div>
              <div className="text-3xl font-extrabold text-blue-400 font-outfit">120ms</div>
            </div>
            <div className="bg-[#111318]/50 border border-white/5 p-6 rounded-xl text-center">
              <div className="text-gray-400 text-xs mb-2 font-semibold">Imágenes/seg</div>
              <div className="text-3xl font-extrabold text-amber-500 font-outfit">2.5k</div>
            </div>
            <div className="bg-[#111318]/50 border border-white/5 p-6 rounded-xl text-center">
              <div className="text-gray-400 text-xs mb-2 font-semibold">Zonas de Riesgo</div>
              <div className="text-3xl font-extrabold text-red-500 font-outfit">8</div>
            </div>
          </div>

          {/* Latest Alerts feed */}
          <div className="border-t border-white/5 pt-6">
            <h4 className="flex items-center gap-2 font-bold text-white text-base mb-4 font-outfit">
              <Bell className="h-4.5 w-4.5 text-teal-400" />
              {t('services.latestAlerts')}
            </h4>

            <div className="flex flex-col gap-3">
              {/* Alert 1 */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-red-500/10 bg-red-500/5 hover:bg-red-500/10 transition-colors">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-bold text-white">Caída de NDVI detectada - Sector Norte</div>
                    <div className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                      <Calendar className="h-3 w-3" />
                      <span>Hace 2 horas - Posible sequía o tala</span>
                    </div>
                  </div>
                </div>
                <span className="bg-red-500/25 border border-red-500/30 text-red-300 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider w-fit">
                  CRÍTICO
                </span>
              </div>

              {/* Alert 2 */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-blue-500/10 bg-blue-500/5 hover:bg-blue-500/10 transition-colors">
                <div className="flex items-start gap-3">
                  <Info className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-bold text-white">Incremento NDWI - Quebrada El Francés</div>
                    <div className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                      <Calendar className="h-3 w-3" />
                      <span>Hace 5 horas - Posible acumulación de agua</span>
                    </div>
                  </div>
                </div>
                <span className="bg-blue-500/25 border border-blue-500/30 text-blue-300 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider w-fit">
                  MODERADO
                </span>
              </div>

              {/* Alert 3 */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-emerald-500/10 bg-emerald-500/5 hover:bg-emerald-500/10 transition-colors">
                <div className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-bold text-white">Monitoreo completado - Área Costera</div>
                    <div className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                      <Calendar className="h-3 w-3" />
                      <span>Hace 1 día - Sin anomalías detectadas</span>
                    </div>
                  </div>
                </div>
                <span className="bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider w-fit">
                  OK
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center mt-12">
          <a
            href="#contacto"
            className="btn btn-primary bg-gradient-to-r from-teal-500 to-emerald-600 border-none hover:opacity-90 hover:scale-105 text-[#111318] px-8 h-12 font-bold rounded-xl transition-all shadow-xl inline-flex items-center gap-2"
          >
            <MailIcon className="h-4 w-4" />
            <span>{t('services.requestFullDemo')}</span>
          </a>
        </div>
      </div>
    </section>
  )
}

const MailIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <rect width="20" height="16" x="2" y="4" rx="2" />
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
  </svg>
)

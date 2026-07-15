import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Mail, Send, CheckCircle, Loader2 } from 'lucide-react'

export const Contact: React.FC = () => {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [company, setCompany] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setErrorMsg(null)
    setIsSuccess(false)

    try {
      const payload = { name, company: company || undefined, email, message }
      const response = await fetch('/api/v1/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        setIsSuccess(true)
        setName('')
        setCompany('')
        setEmail('')
        setMessage('')
      } else {
        const errorData = await response.json().catch(() => ({}))
        setErrorMsg(errorData.detail || 'Error al enviar el mensaje. Intente de nuevo.')
      }
    } catch (error) {
      setErrorMsg('Error de red. Verifique su conexión e intente nuevamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section id="contacto" className="py-20 lg:py-32 bg-[#0b0c10] relative overflow-hidden">
      {/* Decorative blurred highlight */}
      <div className="absolute right-1/3 top-1/2 w-[300px] h-[300px] rounded-full bg-purple-500/5 blur-3xl pointer-events-none" />

      <div className="max-w-4xl mx-auto px-6 relative z-10">
        <div className="text-center mb-12 lg:mb-16">
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight flex items-center justify-center gap-3">
            <Mail className="h-8 w-8 text-teal-400" />
            {t('contact.title')}
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            {t('contact.subtitle')}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel p-8 lg:p-12 rounded-2xl shadow-2xl flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="form-control w-full">
              <label className="label">
                <span className="label-text text-gray-300 font-medium text-sm">{t('contact.nameLabel')}</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t('contact.namePlaceholder')}
                className="input input-bordered w-full bg-[#111318] border-white/10 hover:border-white/20 focus:border-teal-500 rounded-xl text-white placeholder-gray-600 transition-colors"
                required
              />
            </div>

            <div className="form-control w-full">
              <label className="label">
                <span className="label-text text-gray-300 font-medium text-sm">{t('contact.companyLabel')}</span>
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder={t('contact.companyPlaceholder')}
                className="input input-bordered w-full bg-[#111318] border-white/10 hover:border-white/20 focus:border-teal-500 rounded-xl text-white placeholder-gray-600 transition-colors"
              />
            </div>
          </div>

          <div className="form-control w-full">
            <label className="label">
              <span className="label-text text-gray-300 font-medium text-sm">{t('contact.emailLabel')}</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('contact.emailPlaceholder')}
              className="input input-bordered w-full bg-[#111318] border-white/10 hover:border-white/20 focus:border-teal-500 rounded-xl text-white placeholder-gray-600 transition-colors"
              required
            />
          </div>

          <div className="form-control w-full">
            <label className="label">
              <span className="label-text text-gray-300 font-medium text-sm">{t('contact.messageLabel')}</span>
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={t('contact.messagePlaceholder')}
              className="textarea textarea-bordered w-full h-36 bg-[#111318] border-white/10 hover:border-white/20 focus:border-teal-500 rounded-xl text-white placeholder-gray-600 transition-colors leading-relaxed"
              required
            />
          </div>

          {errorMsg && (
            <div className="text-red-400 text-sm font-semibold flex items-center gap-2 mt-2">
              <i className="fas fa-exclamation-circle"></i>
              <span>{errorMsg}</span>
            </div>
          )}

          {isSuccess && (
            <div className="bg-emerald-500/10 border border-emerald-500/25 p-4 rounded-xl text-emerald-400 text-sm font-semibold flex items-center gap-3">
              <CheckCircle className="h-5 w-5 flex-shrink-0" />
              <span>{t('contact.successMsg')}</span>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary bg-gradient-to-r from-teal-500 to-emerald-600 border-none hover:opacity-90 hover:scale-[1.01] text-[#111318] rounded-xl h-12 font-bold transition-all mt-4 flex items-center justify-center gap-2"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Enviando...</span>
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span>{t('contact.sendBtn')}</span>
              </>
            )}
          </button>
        </form>
      </div>
    </section>
  )
}

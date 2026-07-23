import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store/useStore'
import { Send, X, Bot, RefreshCw, Loader2 } from 'lucide-react'
import { GeoBotResponseViewer } from './demo/GeoBotResponseViewer'

export const Chatbot: React.FC = () => {
  const { t } = useTranslation()
  const { 
    isChatOpen, 
    setChatOpen, 
    chatMessages, 
    addChatMessage, 
    clearChat,
    activeAnalysis 
  } = useStore()

  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chatMessages, isChatOpen])

  const handleSend = async () => {
    if (!input.trim() || isSending) return
    
    const userMsg = input.trim()
    setInput('')
    setErrorMsg(null)
    
    // Add user message to local state
    addChatMessage({ role: 'user', text: userMsg })
    setIsSending(true)

    try {
      // Build history for backend structure (limit to last 20 messages)
      const historyPayload = chatMessages
        .filter(m => m.id !== 'welcome')
        .map(m => ({
          role: m.role,
          text: m.text
        }))

      // Prepare context if there is an active analysis
      let contextPayload = null
      if (activeAnalysis) {
        contextPayload = {
          location_name: activeAnalysis.location_name,
          lat: activeAnalysis.lat,
          lng: activeAnalysis.lng,
          radius: activeAnalysis.radius,
          approach: activeAnalysis.approach,
          indices: activeAnalysis.indices,
          meta_date: (activeAnalysis.meta_date && activeAnalysis.meta_date !== 'Desconocida')
            ? activeAnalysis.meta_date
            : (activeAnalysis.chart_data && activeAnalysis.chart_data.length > 0
                ? activeAnalysis.chart_data[activeAnalysis.chart_data.length - 1].date
                : 'Desconocida')
        }
      }

      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMsg,
          context: contextPayload,
          history: historyPayload
        })
      })

      if (response.ok) {
        const data = await response.json()
        addChatMessage({ role: 'assistant', text: data.response })
      } else {
        const err = await response.json().catch(() => ({}))
        setErrorMsg(err.detail || 'Fallo de IA. Intente de nuevo.')
        addChatMessage({ role: 'assistant', text: 'Lo siento, he experimentado una dificultad para procesar tu pregunta. Por favor, intenta de nuevo.' })
      }
    } catch (error) {
      setErrorMsg('Error de conexión con el servicio de IA.')
      addChatMessage({ role: 'assistant', text: 'Lo siento, no he podido contactar al servicio de inteligencia. Por favor verifica tu conexión.' })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        onClick={() => setChatOpen(!isChatOpen)}
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-teal-500 to-emerald-600 hover:scale-105 active:scale-95 text-[#111318] p-4 rounded-full shadow-2xl transition-all duration-200 border-none flex items-center justify-center"
        title={t('chatbot.title')}
      >
        <Bot className="h-6 w-6" />
      </button>

      {/* Slide-out Sidebar Drawer */}
      <div 
        className={`fixed top-0 bottom-0 right-0 z-50 w-full sm:w-[400px] bg-[#16171d] border-l border-white/5 shadow-2xl flex flex-col transition-all duration-300 ${isChatOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#111318]">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-teal-400" />
            <h4 className="font-bold text-white text-sm font-outfit">{t('chatbot.title')}</h4>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={clearChat}
              className="p-1 rounded hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
              title="Reiniciar chat"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <button 
              onClick={() => setChatOpen(false)}
              className="p-1 rounded hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Messages Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scroll bg-[#111318]/45">
          {chatMessages.map((msg) => (
            <div 
              key={msg.id} 
              className={`chat ${msg.role === 'user' ? 'chat-end' : 'chat-start'}`}
            >
              <div 
                className={`chat-bubble text-sm leading-relaxed rounded-2xl max-w-[85%] ${msg.role === 'user' ? 'bg-teal-500 text-[#111318] font-medium' : 'bg-[#1e2028] text-gray-200 border border-white/5'}`}
              >
                {msg.role === 'user' ? msg.text : <GeoBotResponseViewer text={msg.text} />}
              </div>
            </div>
          ))}
          {isSending && (
            <div className="chat chat-start">
              <div className="chat-bubble bg-[#1e2028] text-gray-400 text-sm border border-white/5 rounded-2xl flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-teal-400" />
                <span>Escribiendo...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Footer */}
        {errorMsg && (
          <div className="px-4 py-2 bg-red-500/10 border-t border-red-500/20 text-xs text-red-400 flex items-center justify-between">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="hover:text-white font-bold">✕</button>
          </div>
        )}
        <div className="p-4 border-t border-white/5 bg-[#111318]">
          <div className="flex items-center gap-2 bg-[#16171d] border border-white/10 hover:border-white/20 focus-within:border-teal-500 rounded-xl px-3 py-1.5 transition-colors">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend()
              }}
              placeholder={t('chatbot.placeholder')}
              className="flex-1 bg-transparent text-sm text-white placeholder-gray-600 focus:outline-none h-9"
              disabled={isSending}
            />
            <button
              onClick={handleSend}
              className={`p-1.5 rounded-lg transition-colors flex items-center justify-center ${input.trim() ? 'bg-teal-400 text-[#111318] hover:opacity-90' : 'text-gray-600 cursor-not-allowed'}`}
              disabled={!input.trim() || isSending}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

import { create } from 'zustand'

export interface Location {
  lat: number
  lng: number
  name: string
}

export interface AnalysisResult {
  task_id: string
  location_name: string
  lat: number
  lng: number
  radius: number
  approach: string
  timestamp: string
  indices?: {
    ndvi?: number
    ndwi?: number
    ndmi?: number
    [key: string]: number | undefined
  }
  chart_data?: {
    date: string
    ndvi: number
    ndwi: number
    ndmi: number
  }[]
  interpreted_result?: string
  status?: string
  meta_date?: string
  map_layer?: {
    url: string
  }
}

export interface LiveMetrics {
  elevation: string
  aqi: string
  solar: string
  slope: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  timestamp: Date
}

interface AppState {
  // Localization
  language: 'es' | 'en'
  setLanguage: (lang: 'es' | 'en') => void

  // Selected parameters
  selectedLocation: Location | null
  setSelectedLocation: (loc: Location | null) => void
  selectedApproach: string
  setSelectedApproach: (appr: string) => void
  selectedRadius: number
  setSelectedRadius: (rad: number) => void

  // Live sidebar metrics
  liveMetrics: LiveMetrics | null
  setLiveMetrics: (metrics: LiveMetrics | null) => void

  // Analysis state
  isAnalyzing: boolean
  setIsAnalyzing: (status: boolean) => void
  activeAnalysis: AnalysisResult | null
  setActiveAnalysis: (analysis: AnalysisResult | null) => void
  activeInterpretation: string | null
  setActiveInterpretation: (text: string | null) => void
  analysisHistory: AnalysisResult[]
  setAnalysisHistory: (history: AnalysisResult[]) => void
  addAnalysisToHistory: (analysis: AnalysisResult) => void

  // Chatbot
  isChatOpen: boolean
  setChatOpen: (open: boolean) => void
  chatMessages: ChatMessage[]
  addChatMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  clearChat: () => void

  // Public counters
  stats: { visits: number; analyses: number }
  setStats: (stats: { visits: number; analyses: number }) => void

  // Active UI tab (for mobile routing)
  activeTab: 'inicio' | 'demo' | 'servicios' | 'contacto'
  setActiveTab: (tab: 'inicio' | 'demo' | 'servicios' | 'contacto') => void
}

export const useStore = create<AppState>((set) => ({
  language: 'es',
  setLanguage: (lang) => set({ language: lang }),

  selectedLocation: null,
  setSelectedLocation: (loc) => set({ selectedLocation: loc }),

  selectedApproach: '',
  setSelectedApproach: (appr) => set({ selectedApproach: appr }),

  selectedRadius: 2000,
  setSelectedRadius: (rad) => set({ selectedRadius: rad }),

  liveMetrics: null,
  setLiveMetrics: (metrics) => set({ liveMetrics: metrics }),

  isAnalyzing: false,
  setIsAnalyzing: (status) => set({ isAnalyzing: status }),

  activeAnalysis: null,
  setActiveAnalysis: (analysis) => set({ activeAnalysis: analysis }),

  activeInterpretation: null,
  setActiveInterpretation: (text) => set({ activeInterpretation: text }),

  analysisHistory: [],
  setAnalysisHistory: (history) => set({ analysisHistory: history }),
  addAnalysisToHistory: (analysis) =>
    set((state) => ({
      analysisHistory: [analysis, ...state.analysisHistory.slice(0, 9)], // limit to 10 items
    })),

  isChatOpen: false,
  setChatOpen: (open) => set({ isChatOpen: open }),
  chatMessages: [
    {
      id: 'welcome',
      role: 'assistant',
      text: '¡Hola! Soy el asistente de IA de GeoFeedback. Puedo ayudarte a comprender los análisis territoriales, explicar índices satelitales como NDVI o NDWI, o responder preguntas sobre la plataforma. ¿En qué puedo ayudarte hoy?',
      timestamp: new Date(),
    },
  ],
  addChatMessage: (msg) =>
    set((state) => ({
      chatMessages: [
        ...state.chatMessages,
        {
          ...msg,
          id: Math.random().toString(36).substring(7),
          timestamp: new Date(),
        },
      ],
    })),
  clearChat: () =>
    set({
      chatMessages: [
        {
          id: 'welcome',
          role: 'assistant',
          text: '¡Hola! Soy el asistente de IA de GeoFeedback. Puedo ayudarte a comprender los análisis territoriales, explicar índices satelitales como NDVI o NDWI, o responder preguntas sobre la plataforma. ¿En qué puedo ayudarte hoy?',
          timestamp: new Date(),
        },
      ],
    }),

  stats: { visits: 0, analyses: 0 },
  setStats: (stats) => set({ stats }),

  activeTab: 'inicio',
  setActiveTab: (tab) => set({ activeTab: tab }),
}))

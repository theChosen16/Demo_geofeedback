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
    clouds?: number
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

export interface AuthUser {
  email: string
  name?: string | null
  picture_url?: string | null
  onboarding_completed?: boolean
  preferences?: any
}

interface AppState {
  // Localization
  language: 'es' | 'en'
  setLanguage: (lang: 'es' | 'en') => void

  // Sesión (Google Sign-In)
  user: AuthUser | null
  setUser: (user: AuthUser | null) => void

  // Selected parameters
  selectedLocation: Location | null
  setSelectedLocation: (loc: Location | null) => void
  selectedApproach: string
  setSelectedApproach: (appr: string) => void
  selectedRadius: number
  setSelectedRadius: (rad: number) => void
  // Layer picker — set of active GEE layer keys chosen before the demo
  selectedLayers: Set<string>
  setSelectedLayers: (layers: Set<string>) => void
  toggleLayer: (key: string) => void

  // Live sidebar metrics (partial updates merge over the current values)
  liveMetrics: LiveMetrics | null
  setLiveMetrics: (metrics: Partial<LiveMetrics> | null) => void

  // Analysis state
  isAnalyzing: boolean
  setIsAnalyzing: (status: boolean) => void
  activeAnalysis: AnalysisResult | null
  setActiveAnalysis: (analysis: AnalysisResult | null) => void
  activeInterpretation: string | null
  setActiveInterpretation: (text: string | null) => void
  isInterpreting: boolean
  setIsInterpreting: (status: boolean) => void
  // Se incrementa cada vez que hay una interpretación nueva que mostrar (análisis en vivo o
  // reproducido del historial). ResultModal lo usa para "despertar" el modal si el usuario ya
  // lo había cerrado antes, sin reabrirse solo cuando una interpretación vieja en segundo plano
  // termina de resolver.
  interpretationToken: number
  bumpInterpretationToken: () => void
  analysisHistory: AnalysisResult[]
  setAnalysisHistory: (history: AnalysisResult[]) => void
  addAnalysisToHistory: (analysis: AnalysisResult) => void
  // Parcha el chart_data de una entrada ya agregada al historial (el Pulso Territorial llega
  // en una llamada separada y a veces resuelve después de que la entrada ya fue agregada).
  updateHistoryChartData: (taskId: string, chartData: AnalysisResult['chart_data']) => void

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

  user: null,
  setUser: (user) => set({ user }),

  selectedLocation: null,
  setSelectedLocation: (loc) => set({ selectedLocation: loc }),

  selectedApproach: '',
  setSelectedApproach: (appr) => set({ selectedApproach: appr }),

  // Default layers active: all three satellite indices + elevation
  selectedLayers: new Set(['ndvi', 'ndwi', 'ndmi', 'elevation']),
  setSelectedLayers: (layers) => set({ selectedLayers: layers }),
  toggleLayer: (key) =>
    set((state) => {
      const next = new Set(state.selectedLayers)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return { selectedLayers: next }
    }),

  selectedRadius: 2000,
  setSelectedRadius: (rad) => set({ selectedRadius: rad }),

  liveMetrics: null,
  setLiveMetrics: (metrics) =>
    set((state) => ({
      liveMetrics: metrics && {
        elevation: 'N/D',
        aqi: 'N/D',
        solar: 'N/D',
        slope: 'N/D',
        ...state.liveMetrics,
        ...metrics,
      },
    })),

  isAnalyzing: false,
  setIsAnalyzing: (status) => set({ isAnalyzing: status }),

  activeAnalysis: null,
  setActiveAnalysis: (analysis) => set({ activeAnalysis: analysis }),

  activeInterpretation: null,
  setActiveInterpretation: (text) => set({ activeInterpretation: text }),

  isInterpreting: false,
  setIsInterpreting: (status) => set({ isInterpreting: status }),

  interpretationToken: 0,
  bumpInterpretationToken: () => set((state) => ({ interpretationToken: state.interpretationToken + 1 })),

  analysisHistory: [],
  setAnalysisHistory: (history) => set({ analysisHistory: history }),
  addAnalysisToHistory: (analysis) =>
    set((state) => ({
      analysisHistory: [analysis, ...state.analysisHistory.slice(0, 9)], // limit to 10 items
    })),
  updateHistoryChartData: (taskId, chartData) =>
    set((state) => ({
      analysisHistory: state.analysisHistory.map((item) =>
        item.task_id === taskId ? { ...item, chart_data: chartData } : item
      ),
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

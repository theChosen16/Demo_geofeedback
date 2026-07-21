import { useEffect } from 'react'
import { useStore } from './store/useStore'
import { Navbar } from './components/Navbar'
import { Hero } from './components/Hero'
import { LayerSelector } from './components/LayerSelector'
import { DemoSection } from './components/DemoSection'
import { Services } from './components/Services'
import { Team } from './components/Team'
import { Contact } from './components/Contact'
import { Footer } from './components/Footer'
import { Chatbot } from './components/Chatbot'
import { ResultModal } from './components/ResultModal'

function App() {
  const { setUser, setAnalysisHistory } = useStore()

  // Register landing page visit on mount
  useEffect(() => {
    const registerVisit = async () => {
      try {
        await fetch('/api/v1/visit', {
          method: 'POST'
        })
      } catch (err) {
        console.warn('Failed to log visitor metrics:', err)
      }
    }
    registerVisit()
  }, [])

  // Restore Google Sign-In session (if any) and hydrate the persisted analysis history
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const meRes = await fetch('/api/v1/auth/me')
        if (!meRes.ok) return
        const meData = await meRes.json()
        setUser(meData.user)

        const historyRes = await fetch('/api/v1/me/analyses?days=30')
        if (historyRes.ok) {
          const history = await historyRes.json()
          setAnalysisHistory(history)
        }
      } catch (err) {
        console.warn('No se pudo restaurar la sesión:', err)
      }
    }
    restoreSession()
  }, [setUser, setAnalysisHistory])

  return (
    <div className="min-h-screen bg-[#111318] text-[#9ca3af] relative flex flex-col">
      {/* Header and Navigation */}
      <Navbar />

      {/* Main Page Layout Sections */}
      <main className="flex-grow">
        {/* Hero Landing */}
        <Hero />

        {/* Layer picker — choose GEE data layers before the interactive demo */}
        <LayerSelector />

        {/* Visor Demo Map */}
        <DemoSection />

        {/* Premium services plans */}
        <Services />

        {/* LinkedIn Founders profiles */}
        <Team />

        {/* Contact form */}
        <Contact />
      </main>

      {/* Footer */}
      <Footer />

      {/* Floating chatbot assistant */}
      <Chatbot />

      {/* Dynamic results interpretation popup */}
      <ResultModal />
    </div>
  )
}

export default App

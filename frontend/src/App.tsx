import { useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { Hero } from './components/Hero'
import { Problem } from './components/Problem'
import { Solution } from './components/Solution'
import { Indices } from './components/Indices'
import { DemoSection } from './components/DemoSection'
import { Services } from './components/Services'
import { Team } from './components/Team'
import { Contact } from './components/Contact'
import { Footer } from './components/Footer'
import { Chatbot } from './components/Chatbot'
import { ResultModal } from './components/ResultModal'

function App() {
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

  return (
    <div className="min-h-screen bg-[#111318] text-[#9ca3af] relative flex flex-col">
      {/* Header and Navigation */}
      <Navbar />

      {/* Main Page Layout Sections */}
      <main className="flex-grow">
        {/* Hero Landing */}
        <Hero />

        {/* Problem and Regulatory context */}
        <Problem />

        {/* Technical Solution */}
        <Solution />

        {/* Satellite Indices Definitions */}
        <Indices />

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

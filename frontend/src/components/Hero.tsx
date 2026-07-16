import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store/useStore'
import { ArrowRight, Satellite as SatIcon } from 'lucide-react'

export const Hero: React.FC = () => {
  const { t } = useTranslation()
  const { stats, setStats } = useStore()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  // Fetch stats count on load
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('/api/v1/stats')
        if (res.ok) {
          const data = await res.json()
          setStats({ visits: data.visits, analyses: data.analyses })
        }
      } catch (err) {
        console.error('Error fetching landing stats:', err)
      }
    }
    fetchStats()
  }, [setStats])

  // Canvas animated space background
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    let width = (canvas.width = window.innerWidth)
    let height = (canvas.height = window.innerHeight)

    const handleResize = () => {
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
    }
    window.addEventListener('resize', handleResize)

    // Twinkling stars
    const stars: { x: number; y: number; size: number; speed: number; phase: number }[] = []
    for (let i = 0; i < 120; i++) {
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        size: Math.random() * 1.5,
        speed: 0.01 + Math.random() * 0.02,
        phase: Math.random() * Math.PI * 2,
      })
    }

    // Orbiting satellites
    const orbitalDots: { x: number; y: number; r: number; angle: number; speed: number; color: string }[] = [
      { x: width * 0.7, y: height * 0.5, r: 180, angle: 0, speed: 0.005, color: '#2dd4bf' },
      { x: width * 0.7, y: height * 0.5, r: 240, angle: Math.PI, speed: -0.003, color: '#c084fc' },
    ]

    const draw = () => {
      ctx.fillStyle = '#111318'
      ctx.fillRect(0, 0, width, height)

      // Stars
      for (const star of stars) {
        star.phase += star.speed
        const alpha = 0.15 + Math.abs(Math.sin(star.phase)) * 0.85
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`
        ctx.beginPath()
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2)
        ctx.fill()
      }

      // Orbital lines
      ctx.lineWidth = 1
      for (const dot of orbitalDots) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)'
        ctx.beginPath()
        ctx.arc(width * 0.75, height * 0.45, dot.r, 0, Math.PI * 2)
        ctx.stroke()

        // Satellite dots
        dot.angle += dot.speed
        const sX = width * 0.75 + Math.cos(dot.angle) * dot.r
        const sY = height * 0.45 + Math.sin(dot.angle) * dot.r

        ctx.fillStyle = dot.color
        ctx.shadowColor = dot.color
        ctx.shadowBlur = 8
        ctx.beginPath()
        ctx.arc(sX, sY, 3, 0, Math.PI * 2)
        ctx.fill()
        ctx.shadowBlur = 0 // reset
      }

      animationFrameId = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      window.removeEventListener('resize', handleResize)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  const handleScrollToDemo = () => {
    const demoSec = document.querySelector('#demo')
    if (demoSec) {
      demoSec.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <section id="inicio" className="relative min-h-[90vh] lg:min-h-screen flex items-center overflow-hidden pt-20">
      {/* Dynamic Starry Canvas background */}
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none" />

      {/* Styled Earth & Satellite 3D Visualizer wrapper */}
      <div className="absolute right-0 lg:right-[-5%] top-1/2 -translate-y-1/2 w-full lg:w-[50%] h-[50vh] lg:h-[80vh] pointer-events-none z-10 hidden sm:block">
        <div className="relative w-full h-full flex items-center justify-center">
          {/* Earth glow ring */}
          <div className="absolute w-[280px] lg:w-[450px] h-[280px] lg:h-[450px] rounded-full bg-teal-500/10 blur-[80px] animate-pulse" />
          
          {/* 3D Planet Earth */}
          <div className="earth-sphere absolute w-[240px] lg:w-[380px] h-[240px] lg:h-[380px] rounded-full shadow-[inset_-25px_-25px_60px_rgba(0,0,0,0.9),_0_0_40px_rgba(45,212,191,0.2)] border border-teal-500/20" />
          
          {/* Detailed 3D Satellite and Orbit path */}
          <div className="satellite-orbit absolute w-[360px] lg:w-[580px] h-[120px] lg:h-[180px] border border-white/5 rounded-[50%] rotate-[25deg]">
            <div className="satellite absolute top-0 left-1/2 w-8 h-8 -ml-4 -mt-4 bg-[#23242e] border border-teal-400/50 rounded-lg flex items-center justify-center shadow-xl animate-satellite-float">
              <SatIcon className="h-4 w-4 text-teal-400 animate-pulse" />
              {/* Laser scanning beam */}
              <div className="absolute bottom-[-150%] left-1/2 -translate-x-1/2 w-[2px] h-[60px] bg-gradient-to-b from-teal-400/80 to-transparent animate-laser-scan origin-top" />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-20 w-full">
        {/* Left text column */}
        <div className="lg:col-span-7 text-left flex flex-col items-start">
          {/* Stats widget */}
          <div className="flex gap-6 items-center bg-white/5 border border-white/10 backdrop-blur-xl px-5 py-2.5 rounded-2xl shadow-2xl mb-8">
            <div className="text-center">
              <span className="block text-teal-400 font-extrabold text-2xl font-outfit tracking-tight">{stats.visits.toLocaleString()}</span>
              <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Visitas</span>
            </div>
            <div className="w-[1px] h-8 bg-white/10" />
            <div className="text-center">
              <span className="block text-purple-400 font-extrabold text-2xl font-outfit tracking-tight">{stats.analyses.toLocaleString()}</span>
              <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Análisis</span>
            </div>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.1] font-outfit mb-6">
            {t('hero.title1')}{' '}
            <span className="bg-gradient-to-r from-teal-400 via-teal-300 to-emerald-500 bg-clip-text text-transparent">
              {t('hero.titleAccent')}
            </span>
          </h1>

          <p className="text-gray-400 text-lg md:text-xl font-medium max-w-2xl leading-relaxed mb-10">
            {t('hero.subtitle')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <button
              onClick={handleScrollToDemo}
              className="btn btn-primary bg-gradient-to-r from-teal-500 to-emerald-600 border-none hover:opacity-90 text-[#111318] rounded-xl h-12 font-bold px-8 flex items-center justify-center gap-2 group transition-all"
            >
              <span>{t('hero.exploreBtn')}</span>
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <a
              href="https://github.com/theChosen16/Demo_geofeedback"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline border-white/10 text-white hover:bg-white/5 rounded-xl h-12 font-bold px-8 flex items-center justify-center gap-2 transition-all"
            >
              <i className="fab fa-github text-lg"></i>
              <span>{t('hero.githubBtn')}</span>
            </a>
          </div>
        </div>
      </div>

      {/* Styled Earth Custom Keyframe CSS */}
      <style>{`
        .earth-sphere {
          background-image: url('https://upload.wikimedia.org/wikipedia/commons/c/c4/Earthmap1000x500compac.jpg');
          background-size: cover;
          background-repeat: repeat-x;
          animation: spin-earth 60s linear infinite;
        }

        .satellite-orbit {
          transform-style: preserve-3d;
        }

        @keyframes spin-earth {
          from { background-position: 0 0; }
          to { background-position: 1000px 0; }
        }

        .animate-spin-slow {
          animation: spin 20s linear infinite;
        }

        .animate-satellite-float {
          animation: orbit-satellite 25s linear infinite;
        }

        @keyframes orbit-satellite {
          from {
            transform: rotate(0deg) translateX(180px) rotate(0deg);
          }
          to {
            transform: rotate(360deg) translateX(180px) rotate(-360deg);
          }
        }

        @media (min-width: 1024px) {
          @keyframes orbit-satellite {
            from {
              transform: rotate(0deg) translateX(290px) rotate(0deg);
            }
            to {
              transform: rotate(360deg) translateX(290px) rotate(-360deg);
            }
          }
        }

        @keyframes laser-scan {
          0%, 100% {
            transform: translate(-50%) rotate(-10deg);
            opacity: 0.8;
          }
          50% {
            transform: translate(-50%) rotate(10deg);
            opacity: 0.3;
          }
        }
        .animate-laser-scan {
          animation: laser-scan 3s ease-in-out infinite;
        }
      `}</style>
    </section>
  )
}

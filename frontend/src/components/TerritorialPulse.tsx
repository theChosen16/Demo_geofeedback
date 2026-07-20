import React from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { Sprout, Droplets, CloudRain, Lock, TrendingUp, TrendingDown, Satellite } from 'lucide-react'
import { GoogleLoginButton } from './GoogleLoginButton'

export interface ChartPoint {
  date: string
  ndvi: number
  ndwi: number
  ndmi: number
  clouds?: number
}

// Paleta categórica validada con scripts/validate_palette.js de la skill dataviz contra la
// superficie oscura real de la app (#16171d): las 3 pasan lightness band, chroma floor,
// separación CVD (peor par ΔE 26.8/11.3) y contraste >= 3:1. Orden fijo, nunca ciclado.
const SERIES = [
  { key: 'ndvi' as const, label: 'NDVI', color: '#008300', Icon: Sprout },
  { key: 'ndwi' as const, label: 'NDWI', color: '#3987e5', Icon: Droplets },
  { key: 'ndmi' as const, label: 'NDMI', color: '#d95926', Icon: CloudRain },
]

// Colores de estado (fijos, nunca ciclados con la paleta categórica de arriba) para deltas y
// el score de salud — mismos roles "good"/"warning"/"critical" de la skill dataviz.
const STATUS = { good: '#0ca30c', warning: '#fab219', critical: '#d03b3b' }

// Fórmula genérica de "salud del territorio": vegetación (NDVI) y humedad (NDMI) altas suman
// puntos; NDWI se evalúa por estabilidad (valores extremos en cualquier dirección — sequía
// total o anegamiento — restan) en vez de por signo, ya que si "más agua" es bueno o malo
// depende del enfoque (riego vs. riesgo de inundación). No pretende ser tan precisa como el
// índice de riesgo específico de "fire-risk" en el worker; es un indicador general de un
// vistazo, no un reemplazo del análisis satelital detallado.
function computeHealthScore(latest: { ndvi: number; ndwi: number; ndmi: number }): number {
  const ndviScore = Math.max(0, Math.min(1, latest.ndvi / 0.8)) * 45
  const ndmiScore = Math.max(0, Math.min(1, latest.ndmi / 0.4)) * 35
  const ndwiStability = Math.max(0, 1 - Math.abs(latest.ndwi)) * 20
  return Math.round(ndviScore + ndmiScore + ndwiStability)
}

function healthLabel(score: number): { label: string; color: string } {
  if (score >= 70) return { label: 'Saludable', color: STATUS.good }
  if (score >= 40) return { label: 'Moderado', color: STATUS.warning }
  return { label: 'Atención', color: STATUS.critical }
}

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#0d0e12] border border-white/10 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-gray-300 font-semibold mb-1">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.dataKey} style={{ color: entry.color }} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: entry.color }} />
          {entry.name}: {Number(entry.value).toFixed(2)}
        </p>
      ))}
      {payload[0]?.payload?.clouds != null && (
        <p className="text-gray-500 mt-1">☁ {payload[0].payload.clouds}% nubes</p>
      )}
    </div>
  )
}

interface TerritorialPulseProps {
  isLoggedIn: boolean
  isLoading: boolean
  chartData: ChartPoint[] | null
}

export const TerritorialPulse: React.FC<TerritorialPulseProps> = ({ isLoggedIn, isLoading, chartData }) => {
  if (!isLoggedIn) {
    return (
      <div className="relative glass-panel rounded-2xl border border-white/5 mt-6 overflow-hidden">
        <div className="absolute inset-0 backdrop-blur-md bg-[#111318]/70 z-10 flex flex-col items-center justify-center gap-3 p-6 text-center">
          <Lock className="h-8 w-8 text-teal-400" />
          <p className="text-white font-bold font-outfit">Pulso Territorial</p>
          <p className="text-gray-400 text-sm max-w-sm">
            Inicia sesión con Google para desbloquear la evolución mensual de los índices satelitales de esta zona.
          </p>
          <GoogleLoginButton />
        </div>
        <div aria-hidden="true" className="h-56" />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="glass-panel rounded-2xl border border-white/5 p-6 mt-6 flex flex-col items-center justify-center gap-3 h-56 text-gray-400">
        <span className="loading loading-spinner loading-md text-teal-400" />
        <p className="text-sm">Calculando el Pulso Territorial del último mes...</p>
      </div>
    )
  }

  if (!chartData || chartData.length < 2) {
    return (
      <div className="glass-panel rounded-2xl border border-white/5 p-6 mt-6 text-center text-gray-400 text-sm">
        No hay suficientes pasadas satelitales libres de nubes este mes en esta zona para calcular una tendencia.
      </div>
    )
  }

  const first = chartData[0]
  const last = chartData[chartData.length - 1]
  const score = computeHealthScore(last)
  const health = healthLabel(score)

  return (
    <div className="glass-panel rounded-2xl border border-white/5 p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-white font-outfit flex items-center gap-2">
          <Satellite className="h-5 w-5 text-teal-400" />
          Pulso Territorial · Último mes
        </h3>
        <span className="text-xs text-gray-500">{chartData.length} pasadas satelitales</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                {SERIES.map((s) => (
                  <linearGradient key={s.key} id={`territorial-pulse-grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={s.color} stopOpacity={0.25} />
                    <stop offset="95%" stopColor={s.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2c2c2a" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: '#898781', fontSize: 11 }} tickLine={false} axisLine={{ stroke: '#383835' }} />
              <YAxis tick={{ fill: '#898781', fontSize: 11 }} tickLine={false} axisLine={false} width={36} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, color: '#c3c2b7' }} />
              {SERIES.map((s) => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label}
                  stroke={s.color}
                  strokeWidth={2}
                  fill={`url(#territorial-pulse-grad-${s.key})`}
                  dot={{ r: 3, fill: s.color, strokeWidth: 0 }}
                  activeDot={{ r: 5 }}
                  isAnimationActive={false}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="flex flex-col gap-2.5">
          <div className="rounded-xl border border-white/5 bg-white/[0.03] p-3 flex items-center justify-between">
            <span className="text-xs text-gray-400 font-semibold">Salud del territorio</span>
            <span className="text-base font-bold flex items-center gap-1.5" style={{ color: health.color }}>
              {score}<span className="text-xs text-gray-500 font-normal">/100</span>
              <span className="text-xs font-semibold">{health.label}</span>
            </span>
          </div>
          {SERIES.map((s) => {
            const delta = last[s.key] - first[s.key]
            const isUp = delta >= 0
            const deltaColor = isUp ? STATUS.good : STATUS.critical
            const { Icon } = s
            return (
              <div key={s.key} className="rounded-xl border border-white/5 bg-white/[0.03] p-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4" style={{ color: s.color }} />
                  <span className="text-xs text-gray-400 font-semibold">{s.label}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-bold text-white">{last[s.key].toFixed(2)}</span>
                  <span className="text-xs flex items-center gap-0.5 font-semibold" style={{ color: deltaColor }}>
                    {isUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {Math.abs(delta).toFixed(2)}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Vista de tabla accesible para lectores de pantalla (misma data que el gráfico) */}
      <table className="sr-only">
        <caption>Evolución mensual de índices satelitales NDVI, NDWI y NDMI</caption>
        <thead>
          <tr><th>Fecha</th><th>NDVI</th><th>NDWI</th><th>NDMI</th></tr>
        </thead>
        <tbody>
          {chartData.map((d) => (
            <tr key={d.date}>
              <td>{d.date}</td><td>{d.ndvi}</td><td>{d.ndwi}</td><td>{d.ndmi}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

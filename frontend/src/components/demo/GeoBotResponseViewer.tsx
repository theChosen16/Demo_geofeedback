import React from 'react'

interface GeoBotResponseViewerProps {
  text: string
}

export const GeoBotResponseViewer: React.FC<GeoBotResponseViewerProps> = ({ text }) => {
  if (!text) return null

  // Split text by lines
  const lines = text.split('\n')

  return (
    <div className="flex flex-col gap-4 text-left font-sans leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim()
        if (!trimmed) return null

        // Section Headers (📌, 📊, 🌱, 🎯 or capital titles)
        if (
          trimmed.startsWith('📌') ||
          trimmed.startsWith('📊') ||
          trimmed.startsWith('🌱') ||
          trimmed.startsWith('🎯')
        ) {
          let badgeColor = 'bg-teal-500/10 border-teal-500/30 text-teal-300'
          if (trimmed.startsWith('📌')) badgeColor = 'bg-sky-500/15 border-sky-500/30 text-sky-300'
          if (trimmed.startsWith('📊')) badgeColor = 'bg-indigo-500/15 border-indigo-500/30 text-indigo-300'
          if (trimmed.startsWith('🌱')) badgeColor = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
          if (trimmed.startsWith('🎯')) badgeColor = 'bg-amber-500/15 border-amber-500/30 text-amber-300'

          return (
            <div
              key={idx}
              className={`px-3 py-2 rounded-xl border text-xs font-bold font-outfit uppercase tracking-wider mt-2 mb-1 flex items-center gap-2 ${badgeColor}`}
            >
              <span>{trimmed}</span>
            </div>
          )
        }

        // Technical metric line with status indicator (🟢, 🟡, 🔴)
        if (trimmed.includes('🟢') || trimmed.includes('🟡') || trimmed.includes('🔴')) {
          const isGreen = trimmed.includes('🟢')
          const isYellow = trimmed.includes('🟡')

          const statusBg = isGreen
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : isYellow
            ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            : 'bg-red-500/10 border-red-500/30 text-red-300'

          return (
            <div
              key={idx}
              className="bg-[#111318] border border-white/5 p-3 rounded-xl flex items-center justify-between text-xs my-0.5 hover:border-white/10 transition-colors"
            >
              <span className="font-semibold text-gray-200">{trimmed.replace(/^[•\-]\s*/, '')}</span>
              <span className={`px-2 py-0.5 rounded-md border text-[10px] font-bold ${statusBg}`}>
                {isGreen ? '🟢 Saludable' : isYellow ? '🟡 Atención' : '🔴 Crítico'}
              </span>
            </div>
          )
        }

        // Bullet point item (• or -)
        if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
          const content = trimmed.replace(/^[•\-]\s*/, '')
          return (
            <div key={idx} className="flex items-start gap-2 text-xs text-gray-300 pl-2">
              <span className="text-teal-400 font-bold text-sm leading-none">•</span>
              <span className="flex-1">{content}</span>
            </div>
          )
        }

        // Numbered item (1., 2., etc)
        if (/^\d+\./.test(trimmed)) {
          return (
            <div key={idx} className="flex items-start gap-2.5 text-xs text-gray-200 bg-[#16171d] p-2.5 rounded-lg border border-white/5">
              <span className="text-teal-400 font-bold font-outfit">{trimmed.split('.')[0]}.</span>
              <span className="flex-1">{trimmed.replace(/^\d+\.\s*/, '')}</span>
            </div>
          )
        }

        // Normal text paragraph
        return (
          <p key={idx} className="text-xs text-gray-300 leading-relaxed font-normal">
            {trimmed}
          </p>
        )
      })}
    </div>
  )
}

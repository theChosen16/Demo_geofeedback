# Esquemas Cromáticos Accesibles para GeoFeedback

Este reporte propone 3 paletas cromáticas armónicas y accesibles (cumplimiento WCAG 2.1 AA contraste > 4.5:1) diseñadas para aplicaciones de inteligencia territorial y visores cartográficos.

## Paleta 1: Geo Emerald (Predeterminada - Basada en DaisyUI / Tailwind)
- **Principal (Primary):** `#10B981` (Emerald 500)
- **Secundario (Secondary):** `#065F46` (Emerald 800)
- **Fondo Oscuro (Dark Surface):** `#0F172A` (Slate 900)
- **Superficie de Tarjetas:** `#1E293B` (Slate 800)
- **Texto Principal:** `#F8FAFC` (Slate 50)

```css
:root {
  --color-primary: #10B981;
  --color-primary-focus: #059669;
  --color-surface-dark: #0F172A;
  --color-card-dark: #1E293B;
  --color-text-main: #F8FAFC;
}
```

## Paleta 2: Oceanic Cartography (Modo Alto Contraste)
- **Principal:** `#0284C7` (Sky 600)
- **Acento Geoespacial:** `#F59E0B` (Amber 500)
- **Fondo:** `#030712` (Gray 950)

```css
:root[data-theme="oceanic"] {
  --color-primary: #0284C7;
  --color-accent: #F59E0B;
  --color-background: #030712;
}
```

## Paleta 3: Urban Analytic Light Mode
- **Fondo Claro:** `#F9FAFB` (Gray 50)
- **Superficie Panel:** `#FFFFFF`
- **Borde de Tarjeta:** `#E5E7EB` (Gray 200)
- **Texto Principal:** `#111827` (Gray 900)

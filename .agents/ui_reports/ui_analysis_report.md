# Reporte de Auditoría Semántica y Heurística UI/UX

**Proyecto:** GeoFeedback Demo
**Ámbito de Evaluación:** Interfaces Web Geoespaciales y Analítica Territorial

## Resumen Ejecutivo
Se han auditado 21 componentes TSX del frontend. El análisis examina la jerarquía visual, presencia de atributos de accesibilidad, coherencia de Tailwind/DaisyUI y distribución espacial.

## Hallazgos por Componente

| Componente | Atributos ARIA | Imágenes sin `alt` | Estilos Inciertos Inline | Nivel de Riesgo UX |
|------------|----------------|---------------------|--------------------------|-------------------|
| `Chatbot.tsx` | 0 | 0 | 0 | Medio |
| `Contact.tsx` | 0 | 0 | 0 | Medio |
| `DemoSection.tsx` | 0 | 0 | 0 | Medio |
| `EarthCanvas.tsx` | 0 | 0 | 0 | Medio |
| `Footer.tsx` | 0 | 0 | 0 | Medio |
| `GoogleLoginButton.tsx` | 0 | 0 | 0 | Medio |
| `Hero.tsx` | 0 | 0 | 0 | Medio |
| `Indices.tsx` | 0 | 0 | 0 | Medio |
| `LayerSelector.tsx` | 0 | 0 | 0 | Medio |
| `Navbar.tsx` | 0 | 0 | 0 | Medio |
| `Problem.tsx` | 0 | 0 | 0 | Medio |
| `ResultModal.tsx` | 0 | 0 | 0 | Medio |
| `Services.tsx` | 0 | 0 | 0 | Medio |
| `Solution.tsx` | 0 | 0 | 0 | Medio |
| `Team.tsx` | 0 | 0 | 0 | Medio |
| `TerritorialPulse.tsx` | 1 | 0 | 0 | Bajo |
| `AlertsSection.tsx` | 0 | 0 | 0 | Medio |
| `DemoResultsCards.tsx` | 0 | 0 | 0 | Medio |
| `DemoSearchPanel.tsx` | 0 | 0 | 0 | Medio |
| `HistorySection.tsx` | 0 | 0 | 0 | Medio |
| `OnboardingModal.tsx` | 0 | 0 | 0 | Medio |

## Recomendaciones Heurísticas de Usabilidad

1. **Jerarquía Tipográfica y Contraste:** Asegurar que los encabezados `h1`, `h2` utilicen clases con suficiente contraste (`text-slate-900` / `text-white` en modo oscuro).
2. **Targets Táctiles:** Verificar que los botones e íconos interactivos tengan una superficie táctil mínima de 44x44px (`p-2.5` o superior).
3. **Soporte de Lectores de Pantalla:** Agregar etiquetas `aria-label` explícitas a botones que solo contengan íconos Lucide-react.

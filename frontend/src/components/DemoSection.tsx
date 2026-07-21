import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { APIProvider, Map, useMap, MapControl, ControlPosition, AdvancedMarker } from '@vis.gl/react-google-maps'
import { useStore, type AnalysisResult } from '../store/useStore'
import { Search, MapPin, Satellite as SatIcon, AlertTriangle, RefreshCw } from 'lucide-react'
import { TerritorialPulse } from './TerritorialPulse'

// Declare google as a global variable to satisfy TypeScript
declare const google: any

// Define the approaches configuration
const approachesConfig: Record<string, { name: string; enName: string; indices: string[] }> = {
  mining: { name: 'Minería Sostenible', enName: 'Sustainable Mining', indices: ['NDVI', 'NDWI', 'NDMI'] },
  agriculture: { name: 'Agroindustria Inteligente', enName: 'Smart Agribusiness', indices: ['NDVI', 'NDMI'] },
  energy: { name: 'Energías Renovables', enName: 'Renewable Energy', indices: ['NDVI', 'NDMI'] },
  'real-estate': { name: 'Desarrollo Inmobiliario', enName: 'Real Estate Development', indices: ['NDVI', 'NDWI'] },
  'fire-risk': { name: 'Riesgo de Incendio Forestal', enName: 'Forest Fire Risk', indices: ['NDVI', 'NDMI'] },
  'flood-risk': { name: 'Riesgo de Inundación', enName: 'Flood Risk', indices: ['NDWI'] },
  'water-management': { name: 'Gestión Hídrica', enName: 'Water Management', indices: ['NDWI', 'NDMI'] },
  environmental: { name: 'Calidad Ambiental', enName: 'Environmental Quality', indices: ['NDVI', 'NDWI', 'NDMI'] },
  'land-planning': { name: 'Planificación Territorial', enName: 'Territorial Planning', indices: ['NDVI', 'NDWI'] }
}

export const DemoSection: React.FC = () => {
  const { i18n } = useTranslation()
  const [mapsKey, setMapsKey] = useState<string | null>(null)
  const [isLoadingKey, setIsLoadingKey] = useState(true)

  // Fetch public Google Maps API key from backend
  useEffect(() => {
    const fetchKey = async () => {
      try {
        const res = await fetch('/api/v1/config/maps-key')
        if (res.ok) {
          const data = await res.json()
          setMapsKey(data.google_maps_api_key)
        }
      } catch (err) {
        console.error('Error fetching Google Maps API key:', err)
      } finally {
        setIsLoadingKey(false)
      }
    }
    fetchKey()
  }, [])

  if (isLoadingKey) {
    return (
      <section id="demo" className="py-20 lg:py-32 bg-[#111318] text-center min-h-[600px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <span className="loading loading-spinner loading-lg text-teal-400"></span>
          <p className="text-gray-400 font-medium">Iniciando visor geoespacial...</p>
        </div>
      </section>
    )
  }

  if (!mapsKey) {
    return (
      <section id="demo" className="py-20 lg:py-32 bg-[#111318] text-center min-h-[600px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-red-400 p-6 glass-panel max-w-md rounded-2xl border-red-500/25">
          <AlertTriangle className="h-10 w-10" />
          <h3 className="text-lg font-bold">Error de Configuración</h3>
          <p className="text-sm text-gray-400">No se pudo cargar el visor de mapas porque la clave de Google Maps no está configurada en el servidor backend.</p>
        </div>
      </section>
    )
  }

  return (
    <APIProvider apiKey={mapsKey} language={i18n.language} region="CL">
      <DemoSectionContent mapsKey={mapsKey} />
    </APIProvider>
  )
}

const DemoSectionContent: React.FC<{ mapsKey: string }> = ({ mapsKey }) => {
  const { t, i18n } = useTranslation()
  const map = useMap()
  const isEn = i18n.language === 'en'

  const {
    user,
    selectedLocation,
    setSelectedLocation,
    selectedApproach,
    setSelectedApproach,
    selectedRadius,
    setSelectedRadius,
    liveMetrics,
    setLiveMetrics,
    isAnalyzing,
    setIsAnalyzing,
    activeAnalysis,
    setActiveAnalysis,
    setActiveInterpretation,
    setIsInterpreting,
    bumpInterpretationToken,
    analysisHistory,
    addAnalysisToHistory,
    updateHistoryChartData,
  } = useStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [mapType, setMapType] = useState<'hybrid' | 'roadmap'>('hybrid')
  const autocompleteServiceRef = useRef<any>(null)
  const searchContainerRef = useRef<HTMLDivElement>(null)
  const [pollingStatus, setPollingStatus] = useState<string | null>(null)
  const [isPulseLoading, setIsPulseLoading] = useState(false)

  const [useCustomDates, setUseCustomDates] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const [userAlerts, setUserAlerts] = useState<any[]>([])
  const [isSettingAlert, setIsSettingAlert] = useState(false)
  const [alertTriggerType, setAlertTriggerType] = useState('ndvi_below')
  const [alertTriggerValue, setAlertTriggerValue] = useState(0.3)
  const [isSavingAlert, setIsSavingAlert] = useState(false)

  const fetchUserAlerts = async () => {
    if (!user) return
    try {
      const res = await fetch('/api/v1/alerts')
      if (res.ok) {
        const data = await res.json()
        setUserAlerts(data)
      }
    } catch (err) {
      console.error('Error fetching alerts:', err)
    }
  }

  useEffect(() => {
    fetchUserAlerts()
  }, [user])

  const handleCreateAlert = async () => {
    if (!selectedLocation || !selectedApproach) return
    setIsSavingAlert(true)
    try {
      const res = await fetch('/api/v1/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location_name: selectedLocation.name,
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          radius: selectedRadius,
          approach: selectedApproach,
          trigger_type: alertTriggerType,
          trigger_value: Number(alertTriggerValue)
        })
      })
      if (res.ok) {
        alert('¡Alerta de monitoreo activo creada con éxito!')
        setIsSettingAlert(false)
        fetchUserAlerts()
      } else {
        const err = await res.json()
        alert(err.detail || 'Error al crear la alerta.')
      }
    } catch {
      alert('Error de red al configurar la alerta.')
    } finally {
      setIsSavingAlert(false)
    }
  }

  const handleDeleteAlert = async (alertId: number) => {
    if (!confirm('¿Seguro que deseas eliminar esta alerta de monitoreo?')) return
    try {
      const res = await fetch(`/api/v1/alerts/${alertId}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        alert('Alerta eliminada.')
        fetchUserAlerts()
      } else {
        alert('Error al eliminar la alerta.')
      }
    } catch {
      alert('Error de red al eliminar la alerta.')
    }
  }

  const circleRef = useRef<any>(null)
  const geeLayerRef = useRef<any>(null)
  // task_id del análisis actualmente activo: fetchInterpretation lo compara antes de escribir
  // en el store, para que una interpretación vieja resuelta tarde no pise un análisis más nuevo.
  const latestTaskIdRef = useRef<string | null>(null)

  // Sync Google Map type selection
  useEffect(() => {
    if (map) {
      map.setMapTypeId(mapType)
    }
  }, [map, mapType])

  // Center map on Chile by default
  const centerMapOnChile = () => {
    if (map) {
      map.setCenter({ lat: -33.4489, lng: -70.6693 })
      map.setZoom(5)
    }
  }

  // Toggle map roadmap / satellite hybrid view
  const toggleMapType = () => {
    setMapType(prev => (prev === 'hybrid' ? 'roadmap' : 'hybrid'))
  }

  // Draw radius circle buffer on coordinates update (the marker renders declaratively as <AdvancedMarker>)
  useEffect(() => {
    if (!map || !selectedLocation) return

    if (circleRef.current) {
      circleRef.current.setMap(null)
    }
    circleRef.current = new google.maps.Circle({
      map: map,
      center: { lat: selectedLocation.lat, lng: selectedLocation.lng },
      radius: selectedRadius,
      fillColor: '#2dd4bf',
      fillOpacity: 0.08,
      strokeColor: '#c084fc',
      strokeOpacity: 0.5,
      strokeWeight: 2,
      clickable: false,
    })

    // Fit map bounds to circle
    map.fitBounds(circleRef.current.getBounds())

    return () => {
      if (circleRef.current) circleRef.current.setMap(null)
    }
  }, [map, selectedLocation, selectedRadius])

  // Sync Earth Engine tiles overlays
  useEffect(() => {
    if (!map) return

    if (geeLayerRef.current) {
      map.overlayMapTypes.clear()
      geeLayerRef.current = null
    }

    if (activeAnalysis?.map_layer?.url) {
      const geeMapType = new google.maps.ImageMapType({
        getTileUrl: (coord: any, zoom: number) => {
          return activeAnalysis.map_layer!.url
            .replace('{x}', String(coord.x))
            .replace('{y}', String(coord.y))
            .replace('{z}', String(zoom))
        },
        tileSize: new google.maps.Size(256, 256),
        name: 'GEE Layer',
        opacity: 0.7,
      })

      map.overlayMapTypes.insertAt(0, geeMapType)
      geeLayerRef.current = geeMapType
    }
  }, [map, activeAnalysis])

  // Fetch public Google Maps APIs metadata (Elevation, AQI, Solar)
  const fetchLocalApiMetrics = async (lat: number, lng: number) => {
    // 1. Elevation and Slope
    try {
      const elevator = new google.maps.ElevationService()
      const offset = 0.001
      const locations = [
        { lat, lng },
        { lat: lat + offset, lng },
        { lat: lat - offset, lng },
        { lat, lng: lng + offset },
        { lat, lng: lng - offset },
      ]

      elevator.getElevationForLocations({ locations }, (results: any[], status: string) => {
        if (status === 'OK' && results && results[0]) {
          const centerElev = results[0].elevation
          const maxDiff = results.slice(1).reduce((max: number, r: any) => Math.max(max, Math.abs(r.elevation - centerElev)), 0)
          const slopePercent = (maxDiff / 111) * 100
          const slopeClass = slopePercent < 5 ? 'Plano' : slopePercent < 15 ? 'Suave' : slopePercent < 30 ? 'Moderado' : 'Pronunciado'

          setLiveMetrics({
            elevation: `${Math.round(centerElev)} m`,
            slope: `${Math.round(slopePercent)}% (${slopeClass})`
          })
        } else {
          setLiveMetrics({ elevation: 'N/D', slope: 'N/D' })
        }
      })
    } catch {
      setLiveMetrics({ elevation: 'Error', slope: 'Error' })
    }

    // 2. Air Quality
    try {
      const url = `https://airquality.googleapis.com/v1/currentConditions:lookup?key=${mapsKey}`
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location: { latitude: lat, longitude: lng } }),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.indexes && data.indexes[0]) {
          const idx = data.indexes[0]
          setLiveMetrics({ aqi: `${idx.aqi} (${idx.category})` })
        } else {
          setLiveMetrics({ aqi: 'N/D' })
        }
      } else {
        setLiveMetrics({ aqi: 'N/D' })
      }
    } catch {
      setLiveMetrics({ aqi: 'N/D' })
    }

    // 3. Solar Potential
    try {
      const url = `https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude=${lat}&location.longitude=${lng}&requiredQuality=LOW&key=${mapsKey}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        if (data.solarPotential) {
          const hours = Math.round(data.solarPotential.maxSunshineHoursPerYear || 0)
          setLiveMetrics({ solar: `${hours} hrs/yr` })
        } else {
          setLiveMetrics({ solar: 'Sin edificio' })
        }
      } else {
        setLiveMetrics({ solar: 'N/D' })
      }
    } catch {
      setLiveMetrics({ solar: 'N/D' })
    }
  }

  // Initialize AutocompleteService lazily once Maps API is loaded
  const getAutocompleteService = () => {
    if (!autocompleteServiceRef.current && typeof google !== 'undefined' && google.maps?.places) {
      autocompleteServiceRef.current = new google.maps.places.AutocompleteService()
    }
    return autocompleteServiceRef.current
  }

  // Handle search input changes and fetch suggestions
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setSearchQuery(val)
    if (!val.trim() || val.length < 3) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    const svc = getAutocompleteService()
    if (!svc) return
    svc.getPlacePredictions(
      { input: val, componentRestrictions: { country: 'cl' }, types: ['geocode', 'establishment'] },
      (predictions: any[], status: string) => {
        if (status === 'OK' && predictions) {
          setSuggestions(predictions)
          setShowSuggestions(true)
        } else {
          setSuggestions([])
          setShowSuggestions(false)
        }
      }
    )
  }

  // Select a suggestion and resolve coordinates
  const handleSelectSuggestion = (prediction: any) => {
    setSearchQuery(prediction.description)
    setSuggestions([])
    setShowSuggestions(false)
    const geocoder = new google.maps.Geocoder()
    geocoder.geocode({ placeId: prediction.place_id }, (results: any[], status: string) => {
      if (status === 'OK' && results && results[0]) {
        const loc = results[0].geometry.location
        const nextLoc = { lat: loc.lat(), lng: loc.lng(), name: prediction.description }
        setSelectedLocation(nextLoc)
        setLiveMetrics({ elevation: '...', aqi: '...', solar: '...', slope: '...' })
        fetchLocalApiMetrics(nextLoc.lat, nextLoc.lng)
      }
    })
  }

  // Fallback: Geocode on form submit (for typed queries without selecting suggestion)
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setSuggestions([])
    setShowSuggestions(false)
    const geocoder = new google.maps.Geocoder()
    geocoder.geocode({ address: searchQuery }, (results: any[], status: string) => {
      if (status === 'OK' && results && results[0]) {
        const loc = results[0].geometry.location
        const placeName = results[0].formatted_address
        const nextLoc = { lat: loc.lat(), lng: loc.lng(), name: placeName }
        setSelectedLocation(nextLoc)
        setLiveMetrics({ elevation: '...', aqi: '...', solar: '...', slope: '...' })
        fetchLocalApiMetrics(nextLoc.lat, nextLoc.lng)
      }
    })
  }

  // Map Click Listener
  const handleMapClick = async (e: any) => {
    const lat = e.detail.latLng.lat
    const lng = e.detail.latLng.lng

    const geocoder = new google.maps.Geocoder()
    geocoder.geocode({ location: { lat, lng } }, (results: any[], status: string) => {
      let placeName = isEn ? 'Selected location' : 'Ubicación seleccionada'
      if (status === 'OK' && results && results[0]) {
        placeName = results[0].formatted_address
      }

      const nextLoc = { lat, lng, name: placeName }
      setSelectedLocation(nextLoc)
      setLiveMetrics({ elevation: '...', aqi: '...', solar: '...', slope: '...' })
      fetchLocalApiMetrics(lat, lng)
    })
  }

  // Replay historical analyses
  const replayHistory = (item: AnalysisResult) => {
    // Este item ya no está "en curso": cualquier fetchInterpretation/fetchTimeseries viejo que
    // siga pendiente para el análisis previamente activo no debe pisar lo que se está por
    // mostrar acá. No se vuelve a pedir el Pulso Territorial: se muestra el chart_data ya
    // persistido en el historial (o el estado "sin datos" si nunca se calculó para este item).
    latestTaskIdRef.current = item.task_id
    setIsPulseLoading(false)
    setSelectedLocation({ lat: item.lat, lng: item.lng, name: item.location_name })
    setSelectedApproach(item.approach)
    setSelectedRadius(item.radius)
    setActiveAnalysis(item)
    if (item.interpreted_result) {
      setActiveInterpretation(item.interpreted_result)
      // Reabre el modal aunque el usuario ya lo hubiera cerrado antes en esta sesión.
      bumpInterpretationToken()
    }
    if (map) {
      map.setCenter({ lat: item.lat, lng: item.lng })
      map.setZoom(12)
    }
    fetchLocalApiMetrics(item.lat, item.lng)
  }

  // Trigger Satellite Analysis
  const handleAnalyze = async () => {
    if (!selectedLocation || !selectedApproach) return

    setIsAnalyzing(true)
    setPollingStatus('Encolando análisis...')
    setActiveAnalysis(null)
    setActiveInterpretation(null)
    setIsInterpreting(false)
    setIsPulseLoading(false)

    try {
      const payload = {
        lat: selectedLocation.lat,
        lng: selectedLocation.lng,
        radius: selectedRadius,
        approach: selectedApproach,
        location: selectedLocation.name,
        ...(useCustomDates && startDate && endDate ? { start_date: startDate, end_date: endDate } : {})
      }

      const res = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        const queueData = await res.json()
        const tsTaskId = queueData.timeseries_task_id ?? null
        const tsResult = queueData.timeseries_result ?? null

        if (queueData.status === 'complete') {
          // Cache hit del backend: el resultado ya está listo, sin necesidad de sondear Celery.
          handleAnalysisResult(queueData.task_id, queueData.result, tsTaskId, tsResult)
        } else {
          pollCeleryTask(queueData.task_id, tsTaskId, tsResult)
        }
      } else {
        const errorData = await res.json().catch(() => ({}))
        setPollingStatus(null)
        setIsAnalyzing(false)
        alert(errorData.detail || 'Fallo al iniciar el análisis.')
      }
    } catch {
      setPollingStatus(null)
      setIsAnalyzing(false)
      alert('Error de red al conectar con el motor satelital.')
    }
  }

  // Poll Celery task (primer chequeo rápido a los 500ms, luego cada 2s)
  const pollCeleryTask = (taskId: string, tsTaskId: string | null, tsResult: any | null) => {
    let intervalId: number

    const checkStatus = async () => {
      try {
        const res = await fetch(`/api/v1/analyze/status/${taskId}`)
        if (res.ok) {
          const data = await res.json()

          if (data.status === 'success') {
            clearInterval(intervalId)
            handleAnalysisResult(taskId, data.result, tsTaskId, tsResult)
          } else if (data.status === 'failed') {
            clearInterval(intervalId)
            setPollingStatus(null)
            setIsAnalyzing(false)
            alert(data.error || 'Error procesando las imágenes satelitales.')
          } else if (data.status === 'running') {
            setPollingStatus('Procesando bandas en Google Earth Engine...')
          } else {
            setPollingStatus('En cola de trabajadores Celery...')
          }
        }
      } catch (err) {
        clearInterval(intervalId)
        setPollingStatus(null)
        setIsAnalyzing(false)
        console.error('Error polling Celery task:', err)
      }
    }

    setTimeout(checkStatus, 500)
    intervalId = setInterval(checkStatus, 2000)
  }

  // Se llama en cuanto Google Earth Engine termina (por polling o por cache-hit inmediato):
  // muestra de inmediato los índices y la capa satelital en el mapa, sin esperar a que Gemini
  // termine de generar la interpretación en lenguaje natural (que se dispara justo después).
  const handleAnalysisResult = (taskId: string, result: any, tsTaskId: string | null, tsResult: any | null) => {
    const newAnalysis: AnalysisResult = {
      task_id: taskId,
      location_name: selectedLocation!.name,
      lat: selectedLocation!.lat,
      lng: selectedLocation!.lng,
      radius: selectedRadius,
      approach: selectedApproach,
      timestamp: new Date().toLocaleString(),
      indices: result.data,
      chart_data: [],
      map_layer: result.map_layer,
      meta_date: result.meta?.date ?? 'Desconocida',
      status: 'success'
    }

    // Este es ahora el análisis activo: si un fetchInterpretation/fetchTimeseries de uno
    // anterior (todavía en vuelo) resuelve después, lo detecta comparando contra este valor
    // y no pisa lo de acá.
    latestTaskIdRef.current = taskId

    setActiveAnalysis(newAnalysis)
    setIsAnalyzing(false)
    setPollingStatus(null)

    // La interpretación de IA se pide en paralelo; el modal muestra un placeholder mientras llega.
    setIsInterpreting(true)
    bumpInterpretationToken()
    fetchInterpretation(newAnalysis)

    // El Pulso Territorial (usuarios logeados) también se resuelve en paralelo.
    fetchTimeseries(newAnalysis, tsTaskId, tsResult)
  }

  // Trae la evolución mensual de índices para el Pulso Territorial (solo usuarios logeados;
  // tsTaskId/tsResult vienen null para anónimos y esta función no hace nada). Igual que
  // fetchInterpretation, corre en paralelo y respeta latestTaskIdRef para no pisar un
  // análisis más nuevo con datos de uno viejo si el usuario ya siguió adelante.
  const fetchTimeseries = (analysis: AnalysisResult, tsTaskId: string | null, tsResultInline: any | null) => {
    const applyChartData = async (chartData: AnalysisResult['chart_data']) => {
      const current = useStore.getState().activeAnalysis
      if (latestTaskIdRef.current === analysis.task_id && current?.task_id === analysis.task_id) {
        setActiveAnalysis({ ...current, chart_data: chartData })
      }
      if (latestTaskIdRef.current === analysis.task_id) {
        setIsPulseLoading(false)
      }
      updateHistoryChartData(analysis.task_id, chartData)

      // Persistir en el historial del usuario (best-effort; si falla, el dato sigue
      // visible en esta sesión, solo no sobrevive a un refresh de página).
      try {
        await fetch(`/api/v1/me/analyses/${analysis.task_id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chart_data: chartData }),
        })
      } catch (err) {
        console.warn('No se pudo persistir el Pulso Territorial en el historial:', err)
      }
    }

    if (tsResultInline) {
      setIsPulseLoading(false)
      applyChartData(tsResultInline.chart_data || [])
      return
    }

    if (!tsTaskId) {
      setIsPulseLoading(false)
      return
    }

    setIsPulseLoading(true)
    let intervalId: number

    const checkStatus = async () => {
      try {
        const res = await fetch(`/api/v1/analyze/status/${tsTaskId}`)
        if (res.ok) {
          const data = await res.json()
          if (data.status === 'success') {
            clearInterval(intervalId)
            applyChartData(data.result?.chart_data || [])
          } else if (data.status === 'failed') {
            clearInterval(intervalId)
            if (latestTaskIdRef.current === analysis.task_id) setIsPulseLoading(false)
          }
        }
      } catch (err) {
        clearInterval(intervalId)
        if (latestTaskIdRef.current === analysis.task_id) setIsPulseLoading(false)
        console.error('Error consultando el Pulso Territorial:', err)
      }
    }

    setTimeout(checkStatus, 800)
    intervalId = setInterval(checkStatus, 3000)
  }

  // Fetch AI Gemini interpretation (corre en segundo plano; no bloquea la vista de resultados).
  // Guarda internamente contra que dos análisis se solapen: si el usuario ya inició uno nuevo
  // (o reprodujo un ítem del historial) antes de que esta llamada resuelva, esta ya no es la
  // "última" (latestTaskIdRef cambió) y sus resultados se agregan solo al historial, sin pisar
  // lo que se está mostrando actualmente en pantalla.
  const fetchInterpretation = async (analysis: AnalysisResult) => {
    try {
      const metaDate = analysis.meta_date && analysis.meta_date !== 'Desconocida'
        ? analysis.meta_date
        : (analysis.map_layer?.url ? 'Imagen Sentinel-2 Reciente' : 'Desconocida')
      const payload = {
        results: analysis.indices,
        approach: analysis.approach,
        location: analysis.location_name,
        meta_date: metaDate,
      }

      const res = await fetch('/api/v1/interpret', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const isStillActive = latestTaskIdRef.current === analysis.task_id

      if (res.ok) {
        const interpretData = await res.json()
        const updatedAnalysis = { ...analysis, interpreted_result: interpretData.interpretation }
        if (isStillActive) {
          setActiveAnalysis(updatedAnalysis)
          setActiveInterpretation(updatedAnalysis.interpreted_result!)
        }
        addAnalysisToHistory(updatedAnalysis)
      } else {
        addAnalysisToHistory(analysis)
      }

      if (isStillActive) {
        setIsInterpreting(false)
      }
    } catch {
      addAnalysisToHistory(analysis)
      if (latestTaskIdRef.current === analysis.task_id) {
        setIsInterpreting(false)
      }
    }
  }

  return (
    <section id="demo" className="py-20 lg:py-32 bg-[#111318]">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white font-outfit mb-4 tracking-tight">
            {t('demo.title')}
          </h2>
          <p className="text-lg lg:text-xl text-[#94a3b8] font-medium">
            {t('demo.subtitle')}
          </p>
        </div>

        {/* Info GEE research note */}
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-300/80 p-5 rounded-2xl mb-12 max-w-4xl mx-auto flex gap-4 text-left items-start text-xs lg:text-sm">
          <i className="fas fa-info-circle text-lg mt-0.5 text-amber-400 flex-shrink-0" />
          <div>
            <strong className="block text-white mb-1 font-semibold">{t('demo.noteTitle')}</strong>
            <p className="leading-relaxed whitespace-pre-line">{t('demo.noteDesc')}</p>
            <p className="mt-3 border-t border-amber-500/10 pt-3 opacity-75">{t('demo.methodology')}</p>
          </div>
        </div>

        {/* Demo Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Map Column */}
          <div className="lg:col-span-8 flex flex-col gap-4">
            <div className="relative w-full h-[350px] sm:h-[480px] lg:h-[580px] rounded-2xl overflow-hidden border border-white/5 shadow-2xl bg-[#0b0c10]">
              <Map
                mapId="DEMO_MAP_ID"
                defaultCenter={{ lat: -33.4489, lng: -70.6693 }}
                defaultZoom={5}
                gestureHandling="cooperative"
                disableDefaultUI={true}
                onClick={handleMapClick}
                className="w-full h-full"
              >
                {selectedLocation && (
                  <AdvancedMarker
                    position={{ lat: selectedLocation.lat, lng: selectedLocation.lng }}
                    title={selectedLocation.name}
                  />
                )}
                {/* Custom Map Controls */}
                <MapControl position={ControlPosition.TOP_RIGHT}>
                  <div className="flex gap-2 m-4">
                    <button
                      onClick={centerMapOnChile}
                      className="btn btn-circle btn-sm bg-[#16171d] hover:bg-[#1e2028] border-white/10 text-teal-400 shadow-xl flex items-center justify-center"
                      title={t('demo.centerChile')}
                    >
                      <i className="fas fa-home text-xs"></i>
                    </button>
                    <button
                      onClick={toggleMapType}
                      className="btn btn-circle btn-sm bg-[#16171d] hover:bg-[#1e2028] border-white/10 text-teal-400 shadow-xl flex items-center justify-center"
                      title={t('demo.toggleLayer')}
                    >
                      <i className="fas fa-layer-group text-xs"></i>
                    </button>
                  </div>
                </MapControl>
              </Map>
              
              {/* Tap to select overlay */}
              {!selectedLocation && (
                <div className="absolute inset-0 z-10 bg-black/40 flex items-center justify-center pointer-events-none">
                  <div className="bg-[#16171d]/90 backdrop-blur border border-white/10 px-5 py-2.5 rounded-full text-xs text-white font-medium shadow-xl flex items-center gap-2 animate-bounce">
                    <i className="fas fa-hand-pointer text-teal-400"></i>
                    <span>{t('demo.mapHint')}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Results Grid Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="glass-panel p-5 rounded-xl flex gap-4 items-start">
                <MapPin className="h-6 w-6 text-teal-400 flex-shrink-0" />
                <div>
                  <h4 className="font-bold text-white text-sm">{t('demo.resultLocationTitle')}</h4>
                  <p className="text-gray-400 text-xs mt-1 leading-relaxed truncate max-w-[180px]" title={selectedLocation?.name}>
                    {selectedLocation ? selectedLocation.name : t('demo.resultLocationDesc')}
                  </p>
                </div>
              </div>
              <div className="glass-panel p-5 rounded-xl flex gap-4 items-start">
                <i className="fas fa-crosshairs text-teal-400 text-lg flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-white text-sm">{t('demo.resultApproachTitle')}</h4>
                  <p className="text-gray-400 text-xs mt-1">
                    {selectedApproach ? (isEn ? approachesConfig[selectedApproach]?.enName : approachesConfig[selectedApproach]?.name) : t('demo.resultApproachDesc')}
                  </p>
                </div>
              </div>
              <div className="glass-panel p-5 rounded-xl flex gap-4 items-start">
                <i className="fas fa-satellite text-teal-400 text-lg flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-white text-sm">{t('demo.resultApisTitle')}</h4>
                  <p className="text-gray-400 text-xs mt-1">{t('demo.resultApisDesc')}</p>
                </div>
              </div>
            </div>

            {/* Pulso Territorial: contenido premium para usuarios logeados, aparece tras un análisis */}
            {selectedApproach && activeAnalysis && activeAnalysis.approach === selectedApproach && (
              <TerritorialPulse
                isLoggedIn={!!user}
                isLoading={isPulseLoading}
                chartData={activeAnalysis.chart_data && activeAnalysis.chart_data.length > 0 ? activeAnalysis.chart_data : null}
              />
            )}
          </div>

          {/* Sidebar Controls Column */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            {/* Status bar */}
            <div className="glass-panel p-5 rounded-xl flex items-center justify-around text-xs">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${selectedLocation ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]' : 'bg-red-400'}`} />
                <span className="text-gray-400 font-semibold">{t('demo.statusLocation')}</span>
              </div>
              <div className="w-[1px] h-4 bg-white/10" />
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${selectedApproach ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]' : 'bg-red-400'}`} />
                <span className="text-gray-400 font-semibold">{t('demo.statusApproach')}</span>
              </div>
            </div>

            {/* Buscar Ubicación */}
            <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
              <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
                <Search className="h-4 w-4 text-teal-400" />
                {t('demo.searchLabel')}
              </h4>
              <div ref={searchContainerRef} className="relative">
                <form onSubmit={handleSearchSubmit} className="flex gap-2">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={handleSearchChange}
                    onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                    placeholder={t('demo.searchPlaceholder')}
                    className="input input-sm flex-1 bg-[#111318] border-white/10 focus:border-teal-500 rounded-lg text-xs text-white"
                    autoComplete="off"
                  />
                  <button type="submit" className="btn btn-sm btn-ghost hover:bg-[#1e2028] border border-white/10 text-teal-400 rounded-lg">
                    <Search className="h-3.5 w-3.5" />
                  </button>
                </form>
                {showSuggestions && suggestions.length > 0 && (
                  <ul className="absolute z-50 top-full mt-1 w-full bg-[#16171d] border border-white/10 rounded-xl shadow-2xl overflow-hidden">
                    {suggestions.map((s) => (
                      <li
                        key={s.place_id}
                        onMouseDown={() => handleSelectSuggestion(s)}
                        className="px-4 py-2.5 text-xs text-gray-200 hover:bg-teal-500/10 hover:text-teal-300 cursor-pointer flex items-start gap-2 border-b border-white/5 last:border-0 transition-colors"
                      >
                        <i className="fas fa-map-marker-alt text-teal-400 mt-0.5 flex-shrink-0" />
                        <span className="leading-tight">{s.description}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {selectedLocation && (
                <div className="bg-[#111318] border border-white/5 p-4 rounded-xl text-left flex flex-col gap-1">
                  <div className="font-bold text-white text-xs leading-normal line-clamp-1">{selectedLocation.name}</div>
                  <div className="text-[10px] text-gray-500 font-semibold font-mono">
                    {selectedLocation.lat.toFixed(5)}, {selectedLocation.lng.toFixed(5)}
                  </div>
                </div>
              )}

              {/* Live metrics (Skeletons / Loaded) */}
              {liveMetrics && (
                <div className="bg-[#111318]/50 border border-white/5 p-4 rounded-xl flex flex-col gap-3 text-left">
                  <h5 className="text-[10px] uppercase font-bold text-gray-400 tracking-wider flex items-center gap-1.5">
                    <i className="fas fa-broadcast-tower text-teal-400"></i>
                    {t('demo.livePanelTitle')}
                  </h5>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="flex flex-col gap-1">
                      <span className="text-gray-500 font-semibold text-[10px]">{t('demo.elevation')}</span>
                      <span className="text-white font-bold">{liveMetrics.elevation}</span>
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-gray-500 font-semibold text-[10px]">{t('demo.aqi')}</span>
                      <span className="text-white font-bold">{liveMetrics.aqi}</span>
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-gray-500 font-semibold text-[10px]">{t('demo.solar')}</span>
                      <span className="text-white font-bold">{liveMetrics.solar}</span>
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-gray-500 font-semibold text-[10px]">{t('demo.slope')}</span>
                      <span className="text-white font-bold">{liveMetrics.slope}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Seleccionar Enfoque */}
            <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
              <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
                <i className="fas fa-crosshairs text-teal-400 text-sm"></i>
                {t('demo.selectApproachLabel')}
              </h4>
              <select
                value={selectedApproach}
                onChange={(e) => setSelectedApproach(e.target.value)}
                className="select select-sm bg-[#111318] border-white/10 focus:border-teal-500 rounded-lg text-xs text-white w-full"
              >
                <option value="">{t('demo.chooseApproachOpt')}</option>
                <optgroup label="Sectores Industriales">
                  <option value="mining">Minería Sostenible</option>
                  <option value="agriculture">Agroindustria Inteligente</option>
                  <option value="energy">Energías Renovables</option>
                  <option value="real-estate">Desarrollo Inmobiliario</option>
                </optgroup>
                <optgroup label="Análisis General">
                  <option value="fire-risk">Riesgo de Incendio Forestal</option>
                  <option value="flood-risk">Riesgo de Inundación</option>
                  <option value="water-management">Gestión Hídrica</option>
                  <option value="environmental">Calidad Ambiental</option>
                  <option value="land-planning">Planificación Territorial</option>
                </optgroup>
              </select>

              {selectedApproach && activeAnalysis && activeAnalysis.approach === selectedApproach && (
                <div className="mt-2 text-left flex flex-col gap-3">
                  <div className="text-gray-400 text-xs font-semibold">{t('demo.indicesAndData')}</div>
                  <div className="flex flex-col gap-2">
                    {Object.entries(activeAnalysis.indices || {}).map(([key, val]) => (
                      <div key={key} className="flex justify-between items-center text-xs py-1.5 border-b border-white/5">
                        <span className="text-gray-400 font-semibold">{key}</span>
                        <span className="text-white font-bold font-mono">{typeof val === 'number' ? val.toFixed(4) : val}</span>
                      </div>
                    ))}
                  </div>

                  {/* Exportar Reporte PDF (Premium) */}
                  <button
                    type="button"
                    onClick={() => window.open(`/api/v1/analyze/export/${activeAnalysis.task_id}`, '_blank')}
                    className="btn btn-xs bg-[#16171d] hover:bg-[#1e2028] border border-white/10 text-teal-400 rounded-lg flex items-center justify-center gap-1.5 w-full mt-1 font-semibold"
                  >
                    <i className="fas fa-file-pdf text-[11px]"></i>
                    <span>Exportar Reporte Ejecutivo PDF</span>
                  </button>
                </div>
              )}
            </div>

            {/* Radio de Análisis */}
            <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
              <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
                <i className="fas fa-ruler-combined text-teal-400 text-sm"></i>
                {t('demo.radiusLabel')}
              </h4>
              <select
                value={selectedRadius}
                onChange={(e) => setSelectedRadius(Number(e.target.value))}
                className="select select-sm bg-[#111318] border-white/10 focus:border-teal-500 rounded-lg text-xs text-white w-full"
              >
                <option value={2000}>2 kilómetros (~12.57 km²)</option>
                <option value={5000}>5 kilómetros (~78.54 km²)</option>
                <option value={10000}>10 kilómetros (~314.16 km²)</option>
              </select>
              <div className="text-[10px] text-gray-500 leading-normal text-left">
                <i className="fas fa-info-circle"></i> {t('demo.radiusDesc')}
              </div>

              {/* Rango de Fechas Histórico (Premium) */}
              <div className="border-t border-white/5 pt-3 mt-1 flex flex-col gap-2 text-left">
                <label className="flex items-center gap-2 text-xs font-semibold text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useCustomDates && !!user}
                    disabled={!user}
                    onChange={(e) => setUseCustomDates(e.target.checked)}
                    className="checkbox checkbox-xs checkbox-primary"
                  />
                  {user ? (
                    <span>📅 Rango Histórico (Premium)</span>
                  ) : (
                    <span className="text-gray-500 flex items-center gap-1">
                      <i className="fas fa-lock text-[10px]"></i>
                      📅 Rango Histórico (Premium)
                    </span>
                  )}
                </label>
                
                {!user && (
                  <p className="text-[9px] text-gray-500 leading-snug">
                    Inicia sesión para comparar imágenes históricas de los últimos 3 años.
                  </p>
                )}

                {useCustomDates && user && (
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] text-gray-400">Fecha Inicio</span>
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="input input-xs bg-[#111318] border-white/10 text-white rounded text-[10px]"
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] text-gray-400">Fecha Fin</span>
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="input input-xs bg-[#111318] border-white/10 text-white rounded text-[10px]"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Iniciar Análisis */}
            <div className="glass-panel p-6 rounded-xl flex flex-col gap-4 text-center">
              <button
                onClick={handleAnalyze}
                disabled={!selectedLocation || !selectedApproach || isAnalyzing}
                className="btn btn-primary bg-gradient-to-r from-teal-500 to-emerald-600 border-none hover:opacity-90 text-[#111318] rounded-xl h-11 font-bold flex items-center justify-center gap-2 w-full disabled:opacity-50"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>{t('demo.btnAnalyzing')}</span>
                  </>
                ) : (
                  <>
                    <SatIcon className="h-4 w-4" />
                    <span>{t('demo.btnAnalyze')}</span>
                  </>
                )}
              </button>
              
              <p className={`text-xs font-semibold ${selectedLocation && selectedApproach ? 'text-teal-400' : 'text-gray-500'}`}>
                {selectedLocation && selectedApproach ? '✓ Listo para analizar' : t('demo.btnRequireSelection')}
              </p>

              {pollingStatus && (
                <div className="text-gray-400 text-xs mt-1 animate-pulse italic flex items-center justify-center gap-1.5">
                  <LoaderIcon className="h-3.5 w-3.5 animate-spin text-teal-400" />
                  <span>{pollingStatus}</span>
                </div>
              )}
            </div>

            {/* Monitoreo Satelital Activo (Alertas) */}
            <div className="glass-panel p-6 rounded-xl flex flex-col gap-4 text-left">
              <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
                <i className="fas fa-bell text-teal-400 text-sm"></i>
                Monitoreo Satelital y Alertas
              </h4>
              
              {user ? (
                <div className="flex flex-col gap-3">
                  {userAlerts.length > 0 ? (
                    userAlerts.map((alertItem: any) => (
                      <div key={alertItem.id} className="bg-[#111318]/60 border border-white/5 p-3.5 rounded-xl flex flex-col gap-2">
                        <div className="flex justify-between items-start gap-2">
                          <span className="font-bold text-white text-xs truncate max-w-[170px]" title={alertItem.location_name}>
                            📍 {alertItem.location_name}
                          </span>
                          <button
                            onClick={() => handleDeleteAlert(alertItem.id)}
                            className="text-red-400 hover:text-red-300 font-semibold text-[10px] uppercase tracking-wider"
                          >
                            Eliminar
                          </button>
                        </div>
                        <div className="text-[10px] text-gray-400 leading-normal flex flex-col gap-1 font-semibold">
                          <div>
                            Enfoque: <span className="text-gray-300 font-bold">{(isEn ? approachesConfig[alertItem.approach]?.enName : approachesConfig[alertItem.approach]?.name) || alertItem.approach}</span>
                          </div>
                          <div>
                            Disparador: <span className="text-teal-400 font-bold">{alertItem.trigger_type.toUpperCase().replace('_', ' ')} = {alertItem.trigger_value}</span>
                          </div>
                          {alertItem.last_index_value !== null && (
                            <div>
                              Último Valor: <span className="text-gray-300 font-mono">{alertItem.last_index_value.toFixed(4)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-2">
                      <p className="text-xs text-gray-500 mb-3 font-semibold">No tienes alertas configuradas.</p>
                      {selectedLocation && selectedApproach && !isSettingAlert && (
                        <button
                          onClick={() => setIsSettingAlert(true)}
                          className="btn btn-xs btn-outline btn-primary text-teal-400 hover:bg-teal-500/10 hover:text-teal-300 rounded-lg w-full font-bold"
                        >
                          🔔 Activar Monitoreo en esta Zona
                        </button>
                      )}
                    </div>
                  )}

                  {isSettingAlert && selectedLocation && selectedApproach && (
                    <div className="bg-[#111318] border border-teal-500/20 p-4 rounded-xl flex flex-col gap-3">
                      <div className="text-xs font-bold text-white">Configurar Alerta</div>
                      
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] text-gray-400 font-semibold">Condición Disparadora</span>
                        <select
                          value={alertTriggerType}
                          onChange={(e) => setAlertTriggerType(e.target.value)}
                          className="select select-xs bg-[#16171d] border-white/10 text-white rounded text-[10px] w-full"
                        >
                          <option value="ndvi_below">NDVI (Vegetación) menor que</option>
                          <option value="ndwi_above">NDWI (Inundación/Agua) mayor que</option>
                          <option value="ndmi_below">NDMI (Humedad Suelo) menor que</option>
                          <option value="ndvi_drop_pct">Caída de NDVI (%) mayor o igual a</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] text-gray-400 font-semibold">Valor de Umbral</span>
                        <input
                          type="number"
                          step="0.01"
                          value={alertTriggerValue}
                          onChange={(e) => setAlertTriggerValue(Number(e.target.value))}
                          className="input input-xs bg-[#16171d] border-white/10 text-white rounded text-[10px]"
                        />
                      </div>

                      <div className="flex gap-2 mt-1">
                        <button
                          onClick={handleCreateAlert}
                          disabled={isSavingAlert}
                          className="btn btn-xs btn-primary flex-1 rounded-lg font-bold"
                        >
                          {isSavingAlert ? 'Guardando...' : 'Crear Alerta'}
                        </button>
                        <button
                          onClick={() => setIsSettingAlert(false)}
                          className="btn btn-xs btn-ghost text-gray-400 flex-1 rounded-lg font-bold"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col gap-2 bg-[#111318]/40 border border-white/5 p-4 rounded-xl text-xs">
                  <div className="text-gray-400 font-semibold leading-relaxed">
                    💡 <span className="text-white font-bold">Monitoreo Semanal Satelital (Premium):</span> Guarda un punto de interés para vigilar variaciones críticas de sequía o vegetación y recibir alertas automáticas por email.
                  </div>
                  <div className="text-gray-500 font-semibold text-[10px] mt-1">
                    Inicia sesión con Google para acceder a esta prueba gratuita del plan premium.
                  </div>
                </div>
              )}
            </div>

            {/* Análisis Recientes */}
            {analysisHistory.length > 0 && (
              <div className="glass-panel p-6 rounded-xl flex flex-col gap-4 text-left">
                <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
                  <i className="fas fa-history text-teal-400 text-sm"></i>
                  {t('demo.historyTitle')}
                </h4>
                <div className="flex flex-col gap-2 max-h-[160px] overflow-y-auto custom-scroll">
                  {analysisHistory.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => replayHistory(item)}
                      className="p-2.5 border border-white/5 hover:border-teal-500/20 hover:bg-[#1e2028]/40 rounded-lg text-xs cursor-pointer flex justify-between items-center transition-colors"
                      title={item.location_name}
                    >
                      <div className="flex items-center gap-2">
                        <MapPin className="h-3.5 w-3.5 text-teal-400 flex-shrink-0" />
                        <span className="text-gray-300 font-bold truncate max-w-[150px]">
                          {(isEn ? approachesConfig[item.approach]?.enName : approachesConfig[item.approach]?.name) || item.approach}
                        </span>
                      </div>
                      <span className="text-[10px] text-gray-500 font-semibold">{item.timestamp}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

const LoaderIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
)

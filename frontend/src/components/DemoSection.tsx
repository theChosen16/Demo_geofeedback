import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { APIProvider, Map, useMap, MapControl, ControlPosition, AdvancedMarker } from '@vis.gl/react-google-maps'
import { useStore, type AnalysisResult } from '../store/useStore'
import { AlertTriangle } from 'lucide-react'
import { TerritorialPulse } from './TerritorialPulse'
import { OnboardingModal } from './demo/OnboardingModal'
import { AlertsSection } from './demo/AlertsSection'
import { HistorySection } from './demo/HistorySection'
import { DemoSearchPanel } from './demo/DemoSearchPanel'
import { DemoResultsCards } from './demo/DemoResultsCards'

// Declare google as a global variable to satisfy TypeScript
declare const google: any

// Define the approaches configuration
const approachesConfig: Record<string, { name: string; enName: string; indices: string[] }> = {
  agriculture: { name: 'Agroindustria Inteligente', enName: 'Smart Agribusiness', indices: ['NDVI', 'NDMI', 'SAVI', 'NDRE', 'BSI'] },
  mining: { name: 'Minería Sostenible', enName: 'Sustainable Mining', indices: ['NDVI', 'NDWI', 'BSI', 'NDBI', 'Pendiente'] },
  energy: { name: 'Energías Renovables', enName: 'Renewable Energy', indices: ['Potencial Solar', 'Elevación', 'Aspect', 'NDBI'] },
  'real-estate': { name: 'Desarrollo Inmobiliario', enName: 'Real Estate Development', indices: ['NDBI', 'Pendiente', 'Elevación', 'MNDWI'] },
  'fire-risk': { name: 'Riesgo de Incendio Forestal', enName: 'Forest Fire Risk', indices: ['NBR', 'NDMI', 'NDVI', 'Pendiente'] },
  'flood-risk': { name: 'Riesgo de Inundación', enName: 'Flood Risk', indices: ['MNDWI', 'NDWI', 'NDBI', 'Elevación'] },
  'water-management': { name: 'Gestión Hídrica', enName: 'Water Management', indices: ['NDWI', 'MNDWI', 'NDMI', 'NDVI'] },
  environmental: { name: 'Calidad Ambiental', enName: 'Environmental Quality', indices: ['EVI', 'NDVI', 'NDMI', 'AQI', 'BSI'] },
  'land-planning': { name: 'Planificación Territorial', enName: 'Territorial Planning', indices: ['Pendiente', 'NDBI', 'BSI', 'NDVI', 'Elevación'] }
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
    setUser,
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
  const [alertFrequency, setAlertFrequency] = useState('daily')
  const [isSavingAlert, setIsSavingAlert] = useState(false)

  // Onboarding modal states
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [onboardingStep, setOnboardingStep] = useState(1)
  const [onboardingSector, setOnboardingSector] = useState('')
  const [onboardingRole, setOnboardingRole] = useState('')
  const [onboardingLocation, setOnboardingLocation] = useState('')
  const [onboardingLayers, setOnboardingLayers] = useState({
    ndvi: true,
    ndwi: true,
    ndmi: true,
    elevation: true,
    slope: true,
    lst: false,
    aqi: false,
    solar: false
  })
  const [isSavingOnboarding, setIsSavingOnboarding] = useState(false)

  useEffect(() => {
    if (user && user.onboarding_completed === false) {
      setShowOnboarding(true)
      setOnboardingStep(1)
    } else {
      setShowOnboarding(false)
    }
  }, [user])

  const handleSaveOnboarding = async (skip = false) => {
    setIsSavingOnboarding(true)
    const preferences = skip ? {
      sector: '',
      role: '',
      location: '',
      layers: {
        ndvi: true,
        ndwi: true,
        ndmi: true,
        elevation: true,
        slope: true,
        lst: false,
        aqi: false,
        solar: false
      }
    } : {
      sector: onboardingSector,
      role: onboardingRole,
      location: onboardingLocation,
      layers: onboardingLayers
    }

    try {
      const res = await fetch('/api/v1/auth/me/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferences,
          onboarding_completed: true
        })
      })
      if (res.ok) {
        const data = await res.json()
        setUser(data.user)
        setShowOnboarding(false)
      } else {
        alert('Error al guardar preferencias de personalización.')
      }
    } catch (err) {
      console.error('Error saving onboarding preferences:', err)
      alert('Error de red al guardar la configuración.')
    } finally {
      setIsSavingOnboarding(false)
    }
  }

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
          trigger_value: Number(alertTriggerValue),
          frequency: alertFrequency
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
  const latestTaskIdRef = useRef<string | null>(null)

  // Sync Google Map type selection
  useEffect(() => {
    if (map) {
      map.setMapTypeId(mapType)
    }
  }, [map, mapType])

  const centerMapOnChile = () => {
    if (map) {
      map.setCenter({ lat: -33.4489, lng: -70.6693 })
      map.setZoom(5)
    }
  }

  const toggleMapType = () => {
    setMapType(prev => (prev === 'hybrid' ? 'roadmap' : 'hybrid'))
  }

  // Draw radius circle buffer on coordinates update
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

  // Fetch public Google Maps APIs metadata (Elevation, AQI, Solar) in parallel
  const fetchLocalApiMetrics = async (lat: number, lng: number) => {
    const elevationPromise = new Promise<{ elevation: string; slope: string }>((resolve) => {
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
            resolve({
              elevation: `${Math.round(centerElev)} m`,
              slope: `${Math.round(slopePercent)}% (${slopeClass})`
            })
          } else {
            resolve({ elevation: 'N/D', slope: 'N/D' })
          }
        })
      } catch {
        resolve({ elevation: 'Error', slope: 'Error' })
      }
    })

    const aqiPromise = (async () => {
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
            return { aqi: `${idx.aqi} (${idx.category})` }
          }
        }
        return { aqi: 'N/D' }
      } catch {
        return { aqi: 'N/D' }
      }
    })()

    const solarPromise = (async () => {
      try {
        const url = `https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude=${lat}&location.longitude=${lng}&requiredQuality=LOW&key=${mapsKey}`
        const res = await fetch(url)
        if (res.ok) {
          const data = await res.json()
          if (data.solarPotential) {
            const hours = Math.round(data.solarPotential.maxSunshineHoursPerYear || 0)
            return { solar: `${hours} hrs/yr` }
          }
          return { solar: 'Sin edificio' }
        }
        return { solar: 'N/D' }
      } catch {
        return { solar: 'N/D' }
      }
    })()

    const [elevRes, aqiRes, solarRes] = await Promise.allSettled([elevationPromise, aqiPromise, solarPromise])

    const mergedMetrics = {
      elevation: elevRes.status === 'fulfilled' ? elevRes.value.elevation : 'N/D',
      slope: elevRes.status === 'fulfilled' ? elevRes.value.slope : 'N/D',
      aqi: aqiRes.status === 'fulfilled' ? aqiRes.value.aqi : 'N/D',
      solar: solarRes.status === 'fulfilled' ? solarRes.value.solar : 'N/D',
    }

    setLiveMetrics(mergedMetrics)
  }

  const getAutocompleteService = () => {
    if (!autocompleteServiceRef.current && typeof google !== 'undefined' && google.maps?.places) {
      autocompleteServiceRef.current = new google.maps.places.AutocompleteService()
    }
    return autocompleteServiceRef.current
  }

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

  const replayHistory = (item: AnalysisResult) => {
    latestTaskIdRef.current = item.task_id
    setIsPulseLoading(false)
    setSelectedLocation({ lat: item.lat, lng: item.lng, name: item.location_name })
    setSelectedApproach(item.approach)
    setSelectedRadius(item.radius)
    setActiveAnalysis(item)
    if (item.interpreted_result) {
      setActiveInterpretation(item.interpreted_result)
      bumpInterpretationToken()
    }
    if (map) {
      map.setCenter({ lat: item.lat, lng: item.lng })
      map.setZoom(12)
    }
    fetchLocalApiMetrics(item.lat, item.lng)
  }

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

    latestTaskIdRef.current = taskId
    setActiveAnalysis(newAnalysis)
    setIsAnalyzing(false)
    setPollingStatus(null)

    setIsInterpreting(true)
    bumpInterpretationToken()
    fetchInterpretation(newAnalysis)
    fetchTimeseries(newAnalysis, tsTaskId, tsResult)
  }

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
              
              {!selectedLocation && (
                <div className="absolute inset-0 z-10 bg-black/40 flex items-center justify-center pointer-events-none">
                  <div className="bg-[#16171d]/90 backdrop-blur border border-white/10 px-5 py-2.5 rounded-full text-xs text-white font-medium shadow-xl flex items-center gap-2 animate-bounce">
                    <i className="fas fa-hand-pointer text-teal-400"></i>
                    <span>{t('demo.mapHint')}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Results summary cards */}
            <DemoResultsCards
              selectedLocation={selectedLocation}
              selectedApproach={selectedApproach}
              t={t}
              isEn={isEn}
              approachesConfig={approachesConfig}
            />

            {/* Pulso Territorial */}
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

            {/* Search, Approach & Radius Controls */}
            <DemoSearchPanel
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              handleSearchChange={handleSearchChange}
              handleSearchSubmit={handleSearchSubmit}
              suggestions={suggestions}
              showSuggestions={showSuggestions}
              setShowSuggestions={setShowSuggestions}
              handleSelectSuggestion={handleSelectSuggestion}
              searchContainerRef={searchContainerRef}
              selectedLocation={selectedLocation}
              liveMetrics={liveMetrics}
              selectedApproach={selectedApproach}
              setSelectedApproach={setSelectedApproach}
              activeAnalysis={activeAnalysis}
              selectedRadius={selectedRadius}
              setSelectedRadius={setSelectedRadius}
              useCustomDates={useCustomDates}
              setUseCustomDates={setUseCustomDates}
              startDate={startDate}
              setStartDate={setStartDate}
              endDate={endDate}
              setEndDate={setEndDate}
              user={user}
              t={t}
              triggerAnalysis={handleAnalyze}
              isAnalyzing={isAnalyzing}
              pollingStatus={pollingStatus}
            />

            {/* Monitoring & Alerts Section */}
            <AlertsSection
              user={user}
              userAlerts={userAlerts}
              selectedLocation={selectedLocation}
              selectedApproach={selectedApproach}
              isSettingAlert={isSettingAlert}
              setIsSettingAlert={setIsSettingAlert}
              alertTriggerType={alertTriggerType}
              setAlertTriggerType={setAlertTriggerType}
              alertTriggerValue={alertTriggerValue}
              setAlertTriggerValue={setAlertTriggerValue}
              alertFrequency={alertFrequency}
              setAlertFrequency={setAlertFrequency}
              isSavingAlert={isSavingAlert}
              handleCreateAlert={handleCreateAlert}
              handleDeleteAlert={handleDeleteAlert}
            />

            {/* User Analysis History */}
            <HistorySection
              analysisHistory={analysisHistory}
              replayHistory={replayHistory}
              t={t}
              isEn={isEn}
              approachesConfig={approachesConfig}
            />
          </div>
        </div>
      </div>

      {/* Onboarding Modal Overlay */}
      <OnboardingModal
        showOnboarding={showOnboarding}
        onboardingStep={onboardingStep}
        setOnboardingStep={setOnboardingStep}
        onboardingSector={onboardingSector}
        setOnboardingSector={setOnboardingSector}
        onboardingRole={onboardingRole}
        setOnboardingRole={setOnboardingRole}
        onboardingLocation={onboardingLocation}
        setOnboardingLocation={setOnboardingLocation}
        onboardingLayers={onboardingLayers}
        setOnboardingLayers={setOnboardingLayers}
        handleSaveOnboarding={handleSaveOnboarding}
        isSavingOnboarding={isSavingOnboarding}
      />
    </section>
  )
}

export default DemoSection

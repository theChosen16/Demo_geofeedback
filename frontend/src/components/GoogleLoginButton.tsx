import { useEffect, useRef, useState } from 'react'
import { useStore } from '../store/useStore'

// Google Identity Services se carga vía <script> dinámico; no tiene tipos oficiales de npm.
declare const google: any

const GOOGLE_IDENTITY_SCRIPT_ID = 'google-identity-services-script'
const GOOGLE_IDENTITY_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'

// google.accounts.id es un singleton a nivel de página: el Navbar monta un
// <GoogleLoginButton /> para el header móvil y otro para el desktop (uno queda oculto por
// CSS, no desmontado), así que sin esta guarda initialize() se llamaría dos veces con el
// mismo client_id/callback — funciona igual (Google solo avisa en consola), pero es
// redundante. Solo renderButton() debe correr por instancia (cada una pinta su propio botón).
let googleIdentityInitialized = false

export const GoogleLoginButton: React.FC = () => {
  const { setUser } = useStore()
  const buttonRef = useRef<HTMLDivElement>(null)
  const [clientId, setClientId] = useState<string | null>(null)

  // 1. Obtener el Client ID público desde el backend (no es un secreto, ver main.py).
  useEffect(() => {
    const fetchClientId = async () => {
      try {
        const res = await fetch('/api/v1/config/google-client-id')
        if (res.ok) {
          const data = await res.json()
          setClientId(data.google_oauth_client_id || null)
        }
      } catch (err) {
        console.error('Error fetching Google OAuth client ID:', err)
      }
    }
    fetchClientId()
  }, [])

  // 2. Cargar el script de Google Identity Services e inicializar el botón.
  useEffect(() => {
    if (!clientId) return

    const handleCredentialResponse = async (response: any) => {
      try {
        const res = await fetch('/api/v1/auth/google', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ credential: response.credential }),
        })
        if (res.ok) {
          const data = await res.json()
          setUser(data.user)
        } else {
          console.error('Falló el login con Google:', await res.text())
        }
      } catch (err) {
        console.error('Error de red iniciando sesión con Google:', err)
      }
    }

    const renderButton = () => {
      if (typeof google === 'undefined' || !google.accounts?.id || !buttonRef.current) return
      if (!googleIdentityInitialized) {
        google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
        })
        googleIdentityInitialized = true
      }
      google.accounts.id.renderButton(buttonRef.current, {
        theme: 'filled_black',
        size: 'medium',
        shape: 'pill',
        text: 'signin_with',
      })
    }

    const existingScript = document.getElementById(GOOGLE_IDENTITY_SCRIPT_ID) as HTMLScriptElement | null
    if (existingScript) {
      // El script ya está (o está por) cargado por otra instancia de este componente.
      if (typeof google !== 'undefined' && google.accounts?.id) {
        renderButton()
      } else {
        existingScript.addEventListener('load', renderButton)
      }
      return () => existingScript.removeEventListener('load', renderButton)
    }

    const script = document.createElement('script')
    script.id = GOOGLE_IDENTITY_SCRIPT_ID
    script.src = GOOGLE_IDENTITY_SCRIPT_SRC
    script.async = true
    script.defer = true
    script.onload = renderButton
    document.head.appendChild(script)
  }, [clientId, setUser])

  if (!clientId) return null

  return <div ref={buttonRef} className="flex items-center" />
}

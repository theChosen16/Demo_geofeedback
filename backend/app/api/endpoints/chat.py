import os
import json
import logging
import hashlib
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import verify_rate_limit, analysis_limiter, redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Intentar inicializar cliente de Gemini
gemini_client = None
gemini_available = False
gemini_model_name = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-2.5-flash')

try:
    from google import genai
    if settings.GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        gemini_available = True
        logger.info(f"Gemini AI ({gemini_model_name}) inicializado correctamente en FastAPI.")
    else:
        logger.warning("GEMINI_API_KEY no configurada en FastAPI.")
except ImportError:
    logger.warning("google-genai no está instalado en FastAPI.")


router = APIRouter()

class InterpretRequest(BaseModel):
    results: Dict[str, Any] = Field(..., description="Resultados del análisis satelital a interpretar")
    approach: str = Field(..., description="Enfoque de análisis satelital")
    location: str = Field("ubicación seleccionada", description="Nombre del lugar")
    meta_date: str = Field("Desconocida", description="Fecha de la imagen satelital analizada")


class ChatMessage(BaseModel):
    role: str = Field(..., description="Rol (user/assistant)")
    text: str = Field(..., description="Contenido del mensaje")


class ChatRequest(BaseModel):
    message: str = Field(..., description="Pregunta del usuario", max_length=500)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Contexto del análisis activo")
    history: List[ChatMessage] = Field(default=[], description="Historial de mensajes previos")


def run_gemini_call(prompt: str) -> Optional[str]:
    """Llamada síncrona a Gemini SDK."""
    if not gemini_available or not gemini_client:
        return None
    try:
        response = gemini_client.models.generate_content(
            model=gemini_model_name,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Error llamando a Gemini SDK: {e}")
        return None


@router.post("/interpret", dependencies=[Depends(verify_rate_limit(analysis_limiter))])
async def interpret_analysis(data: InterpretRequest):
    """
    Genera interpretación estructurada con IA (Gemini) sobre los resultados de análisis satelital.
    Utiliza cache en Redis para responder instantáneamente si el mismo análisis fue interpretado recientemente.
    """
    if not gemini_available:
        raise HTTPException(status_code=503, detail="Gemini AI no disponible")

    if len(data.results) > 20:
        raise HTTPException(status_code=400, detail="Datos de resultados inválidos (excede límite)")

    approach_trimmed = data.approach[:50]
    location_trimmed = data.location[:200]
    meta_date_trimmed = data.meta_date[:30]

    # Comprobar cache en Redis
    results_json = json.dumps(data.results, sort_keys=True)
    raw_key = f"interpretation:{approach_trimmed}:{location_trimmed}:{meta_date_trimmed}:{results_json}"
    cache_key = f"interpret:{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()}"

    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                cached_text = cached.decode('utf-8') if isinstance(cached, bytes) else cached
                return {
                    "status": "success",
                    "interpretation": cached_text,
                    "model": f"{gemini_model_name} (cached)"
                }
        except Exception as e:
            logger.warning(f"Error leyendo cache de interpretación ({cache_key}): {e}")

    # Map raw layer keys → human-readable names for context injection
    layer_names = {
        'ndvi':      'Índice de Vegetación (NDVI)',
        'ndwi':      'Agua Superficial (NDWI)',
        'ndmi':      'Humedad / Riesgo de Incendio (NDMI)',
        'elevation': 'Elevación y Pendiente topográfica',
        'aqi':       'Calidad del Aire (AQI)',
        'solar':     'Potencial Solar fotovoltaico',
        'lst':       'Temperatura Superficial (LST)',
        # legacy approach keys kept for backward-compat
        'mining':          'Minería Sostenible',
        'agriculture':     'Agroindustria Inteligente',
        'energy':          'Energías Renovables',
        'real-estate':     'Desarrollo Inmobiliario',
        'flood-risk':      'Riesgo de Inundación',
        'water-management':'Gestión Hídrica',
        'environmental':   'Calidad Ambiental',
        'land-planning':   'Planificación Territorial',
    }

    system_prompt = f"""PERSONALIDAD Y ROL:
Eres GeoBot, el asistente experto de GeoFeedback Chile. Eres un especialista en análisis geoespacial, teledetección satelital e índices ambientales. Tu rol es explicar datos técnicos de forma clara y accesible para cualquier usuario, sin perder rigor científico.

ESTILO DE COMUNICACIÓN:
- Usa un tono profesional pero cercano y amigable
- Evita tecnicismos innecesarios, pero cuando los uses explícalos brevemente
- Sé conciso y ve directo al punto
- Usa emojis moderadamente para hacer el contenido más visual (🌱 🌊 ⛰️ 📊 ⚠️ ✅)
- NO uses formato markdown como ### o ** porque no se renderiza bien en el chat
- Usa saltos de línea para separar secciones

INFORMACIÓN METODOLÓGICA (OBLIGATORIO MENCIONAR):
- Muestra explícitamente el nombre del satélite (Sentinel-2) y la fecha de la imagen analizada.
- OBLIGATORIO: Usa única y exclusivamente la fecha real de la imagen satelital proporcionada en el contexto de los datos ({meta_date_trimmed}), NO inventes, simules ni alucines ninguna otra fecha bajo ninguna circunstancia. Si la fecha es "Desconocida" o nula, indícalo tal cual, pero jamás inventes fechas falsas.
- Explica que los índices se calculan procesando bandas espectrales de luz no visible.
- Indica que los resultados presentados son el promedio de la respuesta satelital en toda la zona (promedio de índices según el área de análisis en km²).
- IMPORTANTE: Explica que la licencia no comercial de GEE tiene acceso completo e inmediato al catálogo. Sentinel-2 tiene una frecuencia física de paso de 5 días (2-3 días en Chile). Para garantizar imágenes sin nubes en la demo, el sistema selecciona la mejor toma dentro de un rango de hasta 6 meses.

ESTRUCTURA DE RESPUESTA:
Organiza tu respuesta en estas secciones claramente separadas:
1. RESUMEN (2-3 líneas con el hallazgo principal, incluye Satélite y Fecha)
2. QUÉ SIGNIFICAN LOS DATOS (explica métricas, procesamiento espectral y promedio por área)
3. IMPLICACIONES PRÁCTICAS (qué significa esto para el usuario)
4. RECOMENDACIONES (3-5 acciones concretas)
"""
    
    prompt = f"""{system_prompt}

DATOS A INTERPRETAR:
Capas activas seleccionadas: {layer_names.get(approach_trimmed, approach_trimmed)}
Ubicación: {location_trimmed}
Fecha de la imagen satelital analizada: {meta_date_trimmed}

Resultados del análisis satelital:
{json.dumps(data.results, indent=2, ensure_ascii=False)}

Genera una interpretación profesional de estos datos siguiendo la estructura indicada. Máximo 250 palabras."""

    # Ejecutar la llamada bloqueante en un hilo asíncrono seguro
    try:
        response_text = await asyncio.to_thread(run_gemini_call, prompt)
        
        if not response_text:
            raise HTTPException(status_code=503, detail="No se pudo obtener la interpretación de Gemini")

        # Guardar en Redis cache por 24 horas
        if redis_client and response_text:
            try:
                redis_client.setex(cache_key, 24 * 60 * 60, response_text)
            except Exception as e:
                logger.warning(f"Error escribiendo cache de interpretación: {e}")
            
        return {
            "status": "success",
            "interpretation": response_text,
            "model": gemini_model_name
        }
    except Exception as e:
        logger.error(f"Error interpret_analysis: {e}")
        raise HTTPException(status_code=503, detail="Falla interna llamando a Gemini")


@router.post("/chat", dependencies=[Depends(verify_rate_limit(analysis_limiter))])
async def chat_with_assistant(data: ChatRequest):
    """
    Chatbot asistente interactivo para responder preguntas ambientales y metodológicas.
    """
    if not gemini_available:
        raise HTTPException(status_code=503, detail="Gemini AI no disponible")

    message_trimmed = data.message[:500]
    meta_date = "Desconocida"
    if data.context:
        meta_date = str(data.context.get("meta_date", "Desconocida"))[:30]

    # Construir historial (limitar a 20 últimos mensajes)
    chat_history_str = ""
    for msg in data.history[:20]:
        role = msg.role[:10]
        text = msg.text[:500]
        chat_history_str += f"{role}: {text}\n"

    system_prompt = f"""Eres GeoBot, el asistente experto de GeoFeedback Chile. 
Eres un especialista en análisis geoespacial, teledetección satelital e índices ambientales.
Tu rol es responder preguntas de forma clara, útil y accesible.

REGLAS:
- Responde siempre en español
- Sé conciso (máximo 100 palabras para respuestas simples)
- Usa emojis moderadamente para hacer el contenido más visual
- NO uses formato markdown como ### o ** porque no se renderiza
- Si no tienes datos de análisis, indica que el usuario debe primero seleccionar capas y realizar un análisis

CONTEXTO CLAVE SOBRE LA PLATAFORMA:
- La UI ahora permite al usuario elegir CAPAS DE DATOS directamente antes del análisis:
  * NDVI (vegetación), NDWI (agua superficial), NDMI (humedad/incendio): calculados por GEE sobre imágenes Sentinel-2
  * Elevación y Pendiente: Google Elevation API
  * AQI: Google Air Quality API en tiempo real
  * Potencial Solar: Google Solar API
  * LST: temperatura superficial de la tierra (Landsat)
- Esta es una DEMO. Usa imágenes Sentinel-2 del catálogo histórico (frecuencia física orbital de paso de 5 días).
- OBLIGATORIO: Si hablas de la fecha de la imagen del análisis, debes usar obligatoriamente la fecha real provista en el contexto: {meta_date}. NO inventes, simules ni alucines ninguna otra fecha bajo ninguna circunstancia.
- Para asegurar resultados libres de nubes, el sistema analiza la mejor imagen dentro de un rango de hasta 6 meses.
- El monitoreo en TIEMPO REAL en vivo está limitado por el tiempo físico de paso orbital del satélite.
- Metodología: Los datos son promedios calculados mediante procesamiento de bandas espectrales sobre el área circular seleccionada (km²).
- Debes mencionar el satélite Sentinel-2 y la fecha cuando hables de análisis.
"""

    prompt = f"""{system_prompt}

CONTEXTO DEL ANÁLISIS ACTUAL:
{json.dumps(data.context, indent=2, ensure_ascii=False) if data.context else "No hay análisis activo aún."}

HISTORIAL DE CONVERSACIÓN:
{chat_history_str if chat_history_str else "Inicio de conversación."}

PREGUNTA DEL USUARIO: {message_trimmed}

Responde de forma útil y amigable:"""

    try:
        response_text = await asyncio.to_thread(run_gemini_call, prompt)
        
        if not response_text:
            raise HTTPException(status_code=503, detail="No se pudo obtener respuesta del chatbot")
            
        return {
            "status": "success",
            "response": response_text,
            "model": gemini_model_name
        }
    except Exception as e:
        logger.error(f"Error chatbot: {e}")
        raise HTTPException(status_code=503, detail="Falla interna en chatbot de Gemini")

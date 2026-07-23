# GeoFeedback Backend (FastAPI + Celery + Earth Engine)

Modulo backend del sistema **GeoFeedback Chile**. Construido con **FastAPI**, **Celery**, **Google Earth Engine Enterprise API**, **Redis** y **PostGIS 3.7**.

> 📚 **Documentación Técnica Completa:** Para acceder a la arquitectura completa, modelos de datos PostGIS, fórmulas de los 15 índices espectrales e integración con GeoBot AI, consulte el documento principal [DOCS.md](../docs/DOCS.md).

---

## 🚀 Inicio Rápido Local

### 1. Requisitos
- Python 3.11+
- Redis (para colas de Celery y caché)
- PostgreSQL + PostGIS (opcional para persistencia local)

### 2. Instalación y Ejecución
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # En Windows (.venv/bin/activate en Linux/macOS)
pip install -r requirements.txt

# Iniciar servidor FastAPI
uvicorn app.main:app --reload --port 8000
```

### 3. Iniciar Worker de Celery
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

---

## 🧪 Pruebas Automatizadas
```bash
# Ejecutar suite de pruebas unitarias e integración desde la raíz
pytest tests/
```

---

## 🛰️ Endpoints Principales
- `POST /api/v1/analyze` : Inicia análisis satelital asíncrono en GEE.
- `GET /api/v1/analyze/status/{task_id}` : Consulta el estado y resultado del análisis.
- `POST /api/v1/interpret` : Genera diagnóstico con GeoBot (Gemini 2.5 Flash).
- `POST /api/v1/chat` : Asistente conversacional de GeoBot.
- `GET /api/v1/stats` : Métricas públicas de observabilidad.

---

_Última actualización: Julio de 2026_

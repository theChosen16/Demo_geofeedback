"""Regresiones de endurecimiento de seguridad para el backend FastAPI.

Cubre la auditoría del 18 de Julio, 2026:
  * Rate limiting en GET /api/v1/analyze/status/{task_id}
  * CORS: el origen comodín ("*") nunca habilita credenciales cross-origin
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
import app.core.security as security_module


class AnalyzeStatusRateLimitTests(unittest.TestCase):
    """GET /analyze/status/{task_id} debe estar acotado como el resto de endpoints públicos.

    Sin límite, un cliente anónimo puede sondear/enumerar el backend de resultados
    de Celery/Redis de forma ilimitada (agotamiento de recursos).
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_status_polling_is_rate_limited(self):
        fake_result = MagicMock()
        fake_result.state = "PENDING"

        original_max = security_module.status_limiter.max_requests
        security_module.status_limiter.max_requests = 3
        security_module.status_limiter._requests.clear()

        try:
            with patch("app.api.endpoints.analyze.AsyncResult", return_value=fake_result):
                responses = [
                    self.client.get("/api/v1/analyze/status/task-abc") for _ in range(6)
                ]
            statuses = [r.status_code for r in responses]

            self.assertEqual(statuses[:3], [200, 200, 200])
            self.assertTrue(all(code == 429 for code in statuses[3:]))
            self.assertEqual(
                responses[3].json(),
                {"detail": "Demasiadas solicitudes. Intenta de nuevo en un minuto."},
            )
        finally:
            security_module.status_limiter.max_requests = original_max


class CorsCredentialedWildcardTests(unittest.TestCase):
    """El comodín '*' no debe combinarse con Access-Control-Allow-Credentials: true.

    Con esa combinación Starlette refleja cualquier Origin y permite peticiones
    autenticadas cross-origin desde cualquier sitio. En despliegues no productivos
    (dev / docker-compose sin ALLOWED_ORIGINS) el backend usa '*', por lo que las
    credenciales deben quedar deshabilitadas.
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_wildcard_origin_does_not_allow_credentials(self):
        response = self.client.get(
            "/api/v1/health",
            headers={"Origin": "https://attacker.example"},
        )
        self.assertEqual(response.status_code, 200)

        acao = response.headers.get("access-control-allow-origin")
        acac = response.headers.get("access-control-allow-credentials")

        # Con comodín se responde '*' (no se refleja el Origin del atacante)
        self.assertEqual(acao, "*")
        # y jamás se conceden credenciales cross-origin
        self.assertIsNone(acac)


if __name__ == "__main__":
    unittest.main()

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
import app.db.session as session_module
from app.core.config import settings


class StatsEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_session = MagicMock()
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_stats_contract_returns_expected_keys_and_types(self):
        # Configurar mock para devolver visitas y análisis
        self.mock_session.exec.return_value.one.side_effect = [15, 8]

        response = self.client.get("/api/v1/stats")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("visits", payload)
        self.assertIn("analyses", payload)
        self.assertEqual(payload["visits"], 15)
        self.assertEqual(payload["analyses"], 8)

    def test_stats_fallback_when_database_fails(self):
        self.mock_session.exec.side_effect = Exception("boom")
        
        response = self.client.get("/api/v1/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"visits": 0, "analyses": 0})


class StatsRateLimitTests(unittest.TestCase):
    """GET /api/v1/stats must cap DB COUNT reads so a flood cannot load Postgres."""

    def setUp(self):
        self.client = TestClient(app)
        self.mock_session = MagicMock()
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_stats_reads_are_rate_limited(self):
        self.mock_session.exec.return_value.one.return_value = 5

        original_max = security_module.stats_limiter.max_requests
        security_module.stats_limiter.max_requests = 3
        security_module.stats_limiter._requests.clear()
        
        try:
            responses = [self.client.get("/api/v1/stats") for _ in range(6)]
            statuses = [r.status_code for r in responses]

            # Primeras 3 retornan 200; las demás fallan con 429
            self.assertEqual(statuses[:3], [200, 200, 200])
            self.assertTrue(all(code == 429 for code in statuses[3:]))
            
            # Throttled response contains the standard detail error from the FastAPI security handler
            self.assertEqual(responses[3].json(), {"detail": "Demasiadas solicitudes. Intenta de nuevo en un minuto."})
        finally:
            security_module.stats_limiter.max_requests = original_max


class ObservabilityRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_session = MagicMock()
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session
        self.original_token = settings.OBSERVABILITY_TOKEN
        self.original_maps_key = settings.GOOGLE_MAPS_API_KEY

    def tearDown(self):
        app.dependency_overrides.clear()
        settings.OBSERVABILITY_TOKEN = self.original_token
        settings.GOOGLE_MAPS_API_KEY = self.original_maps_key

    @patch("ee.Initialize")
    @patch("app.api.endpoints.observability.gemini_available", True)
    @patch("app.api.endpoints.observability.redis_client", object())
    @patch("app.api.endpoints.observability.inspect")
    def test_observability_returns_healthy_contract(self, mock_inspect, mock_ee):
        settings.OBSERVABILITY_TOKEN = "secret-token"
        settings.GOOGLE_MAPS_API_KEY = "test-maps-key"
        
        # Configurar existencia de tablas
        mock_inspect.return_value.has_table.return_value = True
        
        # Mock de consultas de conteo
        self.mock_session.exec.return_value.one.side_effect = [12, 4]

        response = self.client.get(
            "/api/v1/observability",
            headers={"X-Observability-Token": "secret-token"},
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["public_stats"], {"visits": 12, "analyses": 4})
        self.assertTrue(payload["critical_checks"]["database"])
        self.assertTrue(payload["critical_checks"]["analytics"])
        self.assertTrue(payload["critical_checks"]["google_earth_engine"])
        self.assertTrue(payload["critical_checks"]["google_maps_key"])
        self.assertTrue(payload["optional_checks"]["gemini"])
        self.assertTrue(payload["optional_checks"]["redis"])
        self.assertIn("checked_at", payload)

    @patch("ee.Initialize", side_effect=Exception("boom"))
    @patch("app.api.endpoints.observability.gemini_available", False)
    @patch("app.api.endpoints.observability.redis_client", None)
    @patch("app.api.endpoints.observability.inspect")
    def test_observability_returns_503_when_critical_check_is_degraded(self, mock_inspect, _mock_ee):
        settings.OBSERVABILITY_TOKEN = "secret-token"
        settings.GOOGLE_MAPS_API_KEY = ""
        mock_inspect.return_value.has_table.return_value = False

        response = self.client.get(
            "/api/v1/observability",
            headers={"X-Observability-Token": "secret-token"},
        )
        self.assertEqual(response.status_code, 503)

        payload = response.json()
        self.assertEqual(payload["status"], "degraded")
        self.assertFalse(payload["critical_checks"]["analytics"])
        self.assertFalse(payload["critical_checks"]["google_maps_key"])
        self.assertFalse(payload["optional_checks"]["gemini"])
        self.assertFalse(payload["optional_checks"]["redis"])

    @patch("ee.Initialize")
    @patch("app.api.endpoints.observability.gemini_available", True)
    @patch("app.api.endpoints.observability.redis_client", object())
    @patch("app.api.endpoints.observability.inspect")
    def test_observability_external_hides_component_details(self, mock_inspect, _mock_ee):
        """External callers (no observability token) must not receive component details."""
        settings.OBSERVABILITY_TOKEN = ""
        settings.GOOGLE_MAPS_API_KEY = "test-key"
        
        mock_inspect.return_value.has_table.return_value = True
        self.mock_session.exec.return_value.one.side_effect = [5, 2]
        
        response = self.client.get("/api/v1/observability")
        self.assertIn(response.status_code, [200, 503])

        payload = response.json()
        self.assertIn("status", payload)
        self.assertIn("public_stats", payload)
        self.assertNotIn("critical_checks", payload)
        self.assertNotIn("optional_checks", payload)
        self.assertNotIn("analytics", payload)


class VisitLoggingRateLimitTests(unittest.TestCase):
    """POST /api/v1/visit must cap page visits writes to avoid DB flood."""

    def setUp(self):
        self.client = TestClient(app)
        self.mock_session = MagicMock()
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_visit_logging_is_rate_limited(self):
        # Modificar in-place para que afecte la dependencia ya compilada
        original_max = security_module.visit_limiter.max_requests
        security_module.visit_limiter.max_requests = 3
        security_module.visit_limiter._requests.clear()
        
        try:
            responses = [self.client.post("/api/v1/visit") for _ in range(6)]
            statuses = [r.status_code for r in responses]

            # Las primeras 3 retornan 200, las demás 429
            self.assertEqual(statuses[:3], [200, 200, 200])
            self.assertTrue(all(code == 429 for code in statuses[3:]))
            
            # Las inserciones en base de datos están limitadas a 3
            self.assertEqual(self.mock_session.add.call_count, 3)
        finally:
            security_module.visit_limiter.max_requests = original_max


class RedirectRoutesTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_api_root_redirects_to_docs(self):
        response = self.client.get("/api/", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers.get("Location", "").endswith("/api/docs"))

    def test_contact_redirects_to_contact_anchor(self):
        response = self.client.get("/contact", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers.get("Location", "").endswith("/#contacto"))

    def test_csp_allows_google_maps_runtime_resources(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)

        csp = response.headers.get("Content-Security-Policy", "")
        self.assertIn("connect-src 'self' data:", csp)
        self.assertIn("https://*.gstatic.com", csp)
        self.assertIn("worker-src 'self' blob:", csp)


class FrontendAndBootstrapRegressionTests(unittest.TestCase):
    def test_stats_zero_state_is_rendered_explicitly(self):
        js_path = os.path.join(ROOT_DIR, "legacy", "app.js")
        if os.path.exists(js_path):
            with open(js_path, "r", encoding="utf-8") as file_obj:
                js_content = file_obj.read()
            self.assertIn("if (safeStart === safeEnd)", js_content)
            self.assertIn("obj.innerHTML = safeEnd.toLocaleString();", js_content)
            self.assertIn("function syncDemoMapLayout()", js_content)
            self.assertIn("--demo-map-height", js_content)

    def test_railway_init_includes_analytics_sql(self):
        init_script = os.path.join(ROOT_DIR, "scripts", "init_railway_db.py")
        with open(init_script, "r", encoding="utf-8") as file_obj:
            content = file_obj.read()

        self.assertIn("06_create_analytics_tables.sql", content)


if __name__ == "__main__":
    unittest.main()

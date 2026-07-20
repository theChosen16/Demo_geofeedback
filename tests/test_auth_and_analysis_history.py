"""Regresiones para el login con Google, la cache de análisis y el historial por usuario.

Cubre la Etapa B/A del plan de Julio 2026: /auth/google, /auth/me, /auth/logout,
la persistencia condicionada a usuario logeado en el cache-hit de /analyze, y el
aislamiento por usuario de /me/analyses.
"""
import os
import sys
import json
import datetime
import unittest
from unittest.mock import patch, MagicMock

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
import app.db.session as session_module
import app.core.auth as auth_module
import app.core.security as security_module
import app.api.endpoints.analyze as analyze_module
from app.core.config import settings
from app.db.models import User


class GoogleLoginTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_session = MagicMock()
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session
        self.original_secret = settings.SECRET_KEY
        self.original_client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        settings.SECRET_KEY = "test-secret-key-1234567890-abcdef-ghijkl"
        settings.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"

    def tearDown(self):
        app.dependency_overrides.clear()
        settings.SECRET_KEY = self.original_secret
        settings.GOOGLE_OAUTH_CLIENT_ID = self.original_client_id

    @patch("app.api.endpoints.auth.verify_google_id_token")
    def test_invalid_google_token_returns_401(self, mock_verify):
        mock_verify.side_effect = ValueError("invalid token")

        response = self.client.post("/api/v1/auth/google", json={"credential": "bad-token"})
        self.assertEqual(response.status_code, 401)

    @patch("app.api.endpoints.auth.verify_google_id_token")
    def test_valid_google_token_creates_user_and_sets_cookie(self, mock_verify):
        mock_verify.return_value = {
            "sub": "google-sub-123",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/pic.png",
        }
        self.mock_session.exec.return_value.first.return_value = None  # no existía el usuario

        response = self.client.post("/api/v1/auth/google", json={"credential": "good-token"})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["user"]["email"], "user@example.com")
        self.assertEqual(payload["user"]["name"], "Test User")
        self.assertIn("session", response.cookies)

    def test_me_without_cookie_is_401(self):
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_me_with_valid_session_returns_user(self):
        fake_user = User(
            id=7, google_sub="sub-7", email="seven@example.com", name="Seven", picture_url=None,
        )
        token = auth_module.create_session_token(fake_user)
        self.mock_session.get.return_value = fake_user

        self.client.cookies.set("session", token)
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], "seven@example.com")

    def test_me_with_tampered_cookie_is_401(self):
        self.client.cookies.set("session", "not-a-real-jwt")
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_logout_clears_cookie(self):
        self.client.cookies.set("session", "whatever")
        response = self.client.post("/api/v1/auth/logout")
        self.assertEqual(response.status_code, 200)
        set_cookie_header = response.headers.get("set-cookie", "")
        self.assertIn("session=", set_cookie_header)


class AuthRateLimitTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_session = MagicMock()
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.api.endpoints.auth.verify_google_id_token", side_effect=ValueError("invalid"))
    def test_google_login_is_rate_limited(self, _mock_verify):
        original_max = security_module.auth_limiter.max_requests
        security_module.auth_limiter.max_requests = 3
        security_module.auth_limiter._requests.clear()

        try:
            with patch.object(security_module, "redis_client", None):
                responses = [
                    self.client.post("/api/v1/auth/google", json={"credential": "x"})
                    for _ in range(6)
                ]
            statuses = [r.status_code for r in responses]
            self.assertEqual(statuses[:3], [401, 401, 401])
            self.assertTrue(all(code == 429 for code in statuses[3:]))
        finally:
            security_module.auth_limiter.max_requests = original_max


class AnalyzeCacheHitPersistenceTests(unittest.TestCase):
    """El cache-hit de /analyze debe guardar el análisis en el historial SOLO si hay
    un usuario logeado, ya que en ese camino nunca corre process_gee_analysis (worker.py),
    que es lo único que persiste el historial en el flujo normal (no-cacheado)."""

    def setUp(self):
        self.client = TestClient(app)
        self.cached_result = {
            "status": "success",
            "approach": "environmental",
            "data": {"Cobertura Vegetal (NDVI)": "0.45"},
            "area_m2": 100,
            "map_layer": {"url": "https://example.com/tile/{z}/{x}/{y}", "attribution": "GEE"},
            "meta": {
                "satellite": "Sentinel-2", "terrain": "GLO-30",
                "date": "2026-07-01", "buffer_radius_m": 2000,
            },
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def _payload(self):
        return {"lat": -33.45, "lng": -70.66, "radius": 2000, "approach": "environmental", "location": "Test"}

    @patch("app.api.endpoints.analyze.persist_user_analysis")
    def test_cache_hit_persists_for_logged_in_user(self, mock_persist):
        fake_user = MagicMock()
        fake_user.id = 42
        app.dependency_overrides[auth_module.get_optional_user] = lambda: fake_user

        with patch.object(analyze_module, "redis_client") as mock_redis:
            mock_redis.get.return_value = json.dumps(self.cached_result)
            response = self.client.post("/api/v1/analyze", json=self._payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "complete")
        mock_persist.assert_called_once()
        self.assertEqual(mock_persist.call_args[0][0], 42)

    @patch("app.api.endpoints.analyze.persist_user_analysis")
    def test_cache_hit_does_not_persist_for_anonymous_user(self, mock_persist):
        app.dependency_overrides[auth_module.get_optional_user] = lambda: None

        with patch.object(analyze_module, "redis_client") as mock_redis:
            mock_redis.get.return_value = json.dumps(self.cached_result)
            response = self.client.post("/api/v1/analyze", json=self._payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "complete")
        mock_persist.assert_not_called()

    @patch("app.tasks.worker.process_timeseries.delay")
    @patch("app.tasks.worker.process_gee_analysis.delay")
    def test_non_cached_analysis_passes_user_id_to_celery_task(self, mock_delay, mock_ts_delay):
        fake_user = MagicMock()
        fake_user.id = 99
        app.dependency_overrides[auth_module.get_optional_user] = lambda: fake_user
        mock_delay.return_value = MagicMock(id="task-xyz")
        mock_ts_delay.return_value = MagicMock(id="ts-task-xyz")

        with patch.object(analyze_module, "redis_client") as mock_redis:
            mock_redis.get.return_value = None  # cache miss (tanto análisis principal como timeseries)
            response = self.client.post("/api/v1/analyze", json=self._payload())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "queued")
        self.assertEqual(body["timeseries_task_id"], "ts-task-xyz")
        _, kwargs = mock_delay.call_args
        self.assertEqual(kwargs.get("user_id"), 99)

    @patch("app.tasks.worker.process_gee_analysis.delay")
    def test_non_cached_analysis_passes_none_user_id_when_anonymous(self, mock_delay):
        app.dependency_overrides[auth_module.get_optional_user] = lambda: None
        mock_delay.return_value = MagicMock(id="task-xyz")

        with patch.object(analyze_module, "redis_client") as mock_redis:
            mock_redis.get.return_value = None
            response = self.client.post("/api/v1/analyze", json=self._payload())

        self.assertEqual(response.status_code, 200)
        _, kwargs = mock_delay.call_args
        self.assertIsNone(kwargs.get("user_id"))


class TimeseriesResolutionTests(unittest.TestCase):
    """resolve_timeseries() (Pulso Territorial): solo corre para usuarios logeados, cachea
    independientemente del análisis principal, y nunca golpea Celery en un cache-hit."""

    def setUp(self):
        self.client = TestClient(app)
        self.main_result = {"status": "success", "approach": "environmental", "data": {}, "area_m2": 1, "map_layer": {"url": "x"}, "meta": {"date": "2026-07-01"}}
        self.ts_result = {"status": "success", "chart_data": [{"date": "2026-07-01", "ndvi": 0.5, "ndwi": 0.1, "ndmi": 0.3, "clouds": 5.0}]}

    def tearDown(self):
        app.dependency_overrides.clear()

    def _payload(self):
        return {"lat": -33.45, "lng": -70.66, "radius": 2000, "approach": "environmental", "location": "Test"}

    def _redis_get_side_effect(self, key):
        if key.startswith("timeseries:"):
            return json.dumps(self.ts_result)
        return None  # cache miss para el análisis principal

    @patch("app.tasks.worker.process_gee_analysis.delay")
    @patch("app.api.endpoints.analyze.persist_user_analysis")
    def test_timeseries_cache_hit_returned_inline_without_celery(self, _mock_persist, mock_main_delay):
        fake_user = MagicMock()
        fake_user.id = 7
        app.dependency_overrides[auth_module.get_optional_user] = lambda: fake_user
        mock_main_delay.return_value = MagicMock(id="task-main")

        with patch.object(analyze_module, "redis_client") as mock_redis:
            mock_redis.get.side_effect = self._redis_get_side_effect
            response = self.client.post("/api/v1/analyze", json=self._payload())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "queued")  # el análisis principal sí tuvo cache miss
        self.assertIsNone(body["timeseries_task_id"])  # cache-hit: sin task id, sin encolar
        self.assertEqual(body["timeseries_result"], self.ts_result)

    def test_timeseries_not_computed_for_anonymous_user(self):
        app.dependency_overrides[auth_module.get_optional_user] = lambda: None

        with patch.object(analyze_module, "redis_client") as mock_redis:
            mock_redis.get.side_effect = self._redis_get_side_effect
            with patch("app.tasks.worker.process_gee_analysis.delay") as mock_main_delay:
                mock_main_delay.return_value = MagicMock(id="task-main")
                response = self.client.post("/api/v1/analyze", json=self._payload())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body.get("timeseries_task_id"))
        self.assertIsNone(body.get("timeseries_result"))


class MyAnalysesEndpointTests(unittest.TestCase):
    """GET/PATCH /me/analyses deben exigir sesión y aislar los datos por usuario."""

    def setUp(self):
        self.client = TestClient(app)
        self.mock_session = MagicMock()
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_list_analyses_requires_auth(self):
        response = self.client.get("/api/v1/me/analyses")
        self.assertEqual(response.status_code, 401)

    def test_list_analyses_returns_only_current_user_rows(self):
        fake_user = MagicMock()
        fake_user.id = 5
        app.dependency_overrides[auth_module.get_current_user] = lambda: fake_user

        fake_row = MagicMock()
        fake_row.task_id = "task-1"
        fake_row.location_name = "Papudo"
        fake_row.lat = -32.5
        fake_row.lng = -71.4
        fake_row.radius = 2000
        fake_row.approach = "environmental"
        fake_row.created_at = datetime.datetime(2026, 7, 1, 10, 30)
        fake_row.indices = {"NDVI": 0.5}
        fake_row.chart_data = None
        fake_row.map_layer_url = "https://example.com/tile"
        fake_row.image_date = "2026-07-01"
        fake_row.interpretation = None

        self.mock_session.exec.return_value.all.return_value = [fake_row]

        response = self.client.get("/api/v1/me/analyses")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["task_id"], "task-1")
        self.assertEqual(body[0]["map_layer"], {"url": "https://example.com/tile"})

    def test_patch_interpretation_requires_auth(self):
        response = self.client.patch("/api/v1/me/analyses/task-1", json={"interpretation": "texto"})
        self.assertEqual(response.status_code, 401)

    def test_patch_interpretation_404_when_not_owned(self):
        fake_user = MagicMock()
        fake_user.id = 5
        app.dependency_overrides[auth_module.get_current_user] = lambda: fake_user
        self.mock_session.exec.return_value.first.return_value = None

        response = self.client.patch("/api/v1/me/analyses/task-1", json={"interpretation": "texto"})
        self.assertEqual(response.status_code, 404)

    def test_patch_interpretation_updates_row(self):
        fake_user = MagicMock()
        fake_user.id = 5
        app.dependency_overrides[auth_module.get_current_user] = lambda: fake_user

        fake_row = MagicMock()
        self.mock_session.exec.return_value.first.return_value = fake_row

        response = self.client.patch("/api/v1/me/analyses/task-1", json={"interpretation": "texto nuevo"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake_row.interpretation, "texto nuevo")
        self.mock_session.commit.assert_called()


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT_DIR, "api")

if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

import app as app_module  # noqa: E402


class StatsEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    @patch.object(app_module.database, "get_public_stats", return_value={"visits": 0, "analyses": 0})
    def test_stats_contract_returns_expected_keys_and_types(self, _mock_stats):
        response = self.client.get("/api/v1/stats")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertIn("visits", payload)
        self.assertIn("analyses", payload)
        self.assertIsInstance(payload["visits"], int)
        self.assertIsInstance(payload["analyses"], int)

    @patch.object(app_module.database, "get_public_stats", side_effect=Exception("boom"))
    def test_stats_fallback_when_database_fails(self, _mock_stats):
        response = self.client.get("/api/v1/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"visits": 0, "analyses": 0})


class ObservabilityRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-maps-key", "OBSERVABILITY_TOKEN": "secret-token"}, clear=False)
    @patch.object(app_module, "gee_initialized", True)
    @patch.object(app_module, "gemini_available", True)
    @patch.object(app_module, "redis_client", object())
    @patch.object(
        app_module.database,
        "get_observability_snapshot",
        return_value={
            "database": {"connected": True},
            "analytics": {
                "page_visits_table": True,
                "api_usage_logs_table": True,
                "role_configured": True,
                "ready": True,
            },
            "public_stats": {"visits": 12, "analyses": 4},
        },
    )
    def test_observability_returns_healthy_contract(self, _mock_snapshot):
        response = self.client.get(
            "/api/v1/observability",
            headers={"X-Observability-Token": "secret-token"},
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["public_stats"], {"visits": 12, "analyses": 4})
        self.assertTrue(payload["critical_checks"]["database"])
        self.assertTrue(payload["critical_checks"]["analytics"])
        self.assertTrue(payload["critical_checks"]["google_earth_engine"])
        self.assertTrue(payload["critical_checks"]["google_maps_key"])
        self.assertTrue(payload["optional_checks"]["gemini"])
        self.assertTrue(payload["optional_checks"]["redis"])
        self.assertIn("checked_at", payload)

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "", "OBSERVABILITY_TOKEN": "secret-token"}, clear=False)
    @patch.object(app_module, "gee_initialized", True)
    @patch.object(app_module, "gemini_available", False)
    @patch.object(app_module, "redis_client", None)
    @patch.object(
        app_module.database,
        "get_observability_snapshot",
        return_value={
            "database": {"connected": True},
            "analytics": {
                "page_visits_table": False,
                "api_usage_logs_table": False,
                "role_configured": True,
                "ready": False,
            },
            "public_stats": {"visits": 0, "analyses": 0},
        },
    )
    def test_observability_returns_503_when_critical_check_is_degraded(self, _mock_snapshot):
        response = self.client.get(
            "/api/v1/observability",
            headers={"X-Observability-Token": "secret-token"},
        )
        self.assertEqual(response.status_code, 503)

        payload = response.get_json()
        self.assertEqual(payload["status"], "degraded")
        self.assertFalse(payload["critical_checks"]["analytics"])
        self.assertFalse(payload["critical_checks"]["google_maps_key"])
        self.assertFalse(payload["optional_checks"]["gemini"])
        self.assertFalse(payload["optional_checks"]["redis"])

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"}, clear=False)
    @patch.object(app_module, "gee_initialized", True)
    @patch.object(app_module, "gemini_available", True)
    @patch.object(app_module, "redis_client", object())
    @patch.object(
        app_module.database,
        "get_observability_snapshot",
        return_value={
            "database": {"connected": True},
            "analytics": {"page_visits_table": True, "api_usage_logs_table": True, "role_configured": True, "ready": True},
            "public_stats": {"visits": 5, "analyses": 2},
        },
    )
    def test_observability_external_hides_component_details(self, _mock_snapshot):
        """External callers (no observability token) must not receive component details."""
        # No X-Observability-Token header -> external path, even if a token is configured.
        env_without_token = {k: v for k, v in os.environ.items() if k != "OBSERVABILITY_TOKEN"}
        with patch.dict(os.environ, env_without_token, clear=True):
            response = self.client.get("/api/v1/observability")
        self.assertIn(response.status_code, (200, 503))

        payload = response.get_json()
        self.assertIn("status", payload)
        self.assertIn("public_stats", payload)
        self.assertNotIn("critical_checks", payload)
        self.assertNotIn("optional_checks", payload)
        self.assertNotIn("analytics", payload)

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key", "OBSERVABILITY_TOKEN": "secret-token"}, clear=False)
    @patch.object(app_module, "gee_initialized", True)
    @patch.object(app_module, "gemini_available", True)
    @patch.object(app_module, "redis_client", object())
    @patch.object(
        app_module.database,
        "get_observability_snapshot",
        return_value={
            "database": {"connected": True},
            "analytics": {"page_visits_table": True, "api_usage_logs_table": True, "role_configured": True, "ready": True},
            "public_stats": {"visits": 5, "analyses": 2},
        },
    )
    def test_observability_wrong_token_hides_component_details(self, _mock_snapshot):
        """A caller presenting an incorrect token is treated as external."""
        response = self.client.get(
            "/api/v1/observability",
            headers={"X-Observability-Token": "wrong-token"},
        )
        self.assertIn(response.status_code, (200, 503))

        payload = response.get_json()
        self.assertNotIn("critical_checks", payload)
        self.assertNotIn("optional_checks", payload)
        self.assertNotIn("analytics", payload)


class AnalyticsBootstrapMiddlewareTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    @patch.object(app_module.database, "ensure_analytics_ready", return_value=True)
    def test_bootstrap_runs_before_request_when_enabled(self, _mock_bootstrap):
        previous_ready = app_module._analytics_bootstrap_state["ready"]
        previous_last_attempt = app_module._analytics_bootstrap_state["last_attempt"]
        previous_enabled = app_module._ANALYTICS_BOOTSTRAP_ENABLED

        try:
            app_module._analytics_bootstrap_state["ready"] = False
            app_module._analytics_bootstrap_state["last_attempt"] = 0.0
            app_module._ANALYTICS_BOOTSTRAP_ENABLED = True

            response = self.client.get("/api/v1/health")
            self.assertEqual(response.status_code, 200)

            _mock_bootstrap.assert_called_once()
            self.assertTrue(app_module._analytics_bootstrap_state["ready"])
        finally:
            app_module._analytics_bootstrap_state["ready"] = previous_ready
            app_module._analytics_bootstrap_state["last_attempt"] = previous_last_attempt
            app_module._ANALYTICS_BOOTSTRAP_ENABLED = previous_enabled


class VisitLoggingRateLimitTests(unittest.TestCase):
    """GET / must cap analytics writes so a flood cannot fill the DB / inflate stats."""

    def setUp(self):
        self.client = app_module.app.test_client()

    @patch.object(app_module.database, "log_visit")
    def test_visit_logging_is_rate_limited_but_page_still_serves(self, mock_log_visit):
        # Fresh limiter so this test is independent of module-level state:
        # allow at most 3 visit writes per window.
        fresh_limiter = app_module.RateLimiter(
            key_prefix="visit-test", max_requests=3, window_seconds=60
        )
        with patch.object(app_module, "visit_limiter", fresh_limiter):
            statuses = [self.client.get("/").status_code for _ in range(6)]

        # The landing page is always served, even once logging is throttled.
        self.assertTrue(all(code == 200 for code in statuses))
        # ...but the DB write is capped at the limiter's max_requests.
        self.assertEqual(mock_log_visit.call_count, 3)


class GeminiTimeoutTests(unittest.TestCase):
    """A slow Gemini call must not block the request thread past the timeout."""

    def test_call_returns_promptly_on_timeout(self):
        import time as _time

        class _SlowModels:
            def generate_content(self, *args, **kwargs):
                _time.sleep(5)  # simulate a hung upstream response
                return type("R", (), {"text": "late"})()

        class _SlowClient:
            models = _SlowModels()

        with patch.object(app_module, "gemini_available", True), \
                patch.object(app_module, "gemini_model_name", "test-model", create=True), \
                patch.object(app_module, "gemini_client", _SlowClient(), create=True):
            started = _time.time()
            result = app_module.call_gemini_with_retry(
                "prompt", max_retries=1, timeout=0.2
            )
            elapsed = _time.time() - started

        self.assertIsNone(result)
        # Old `with ThreadPoolExecutor()` code blocked ~5s on shutdown(wait=True);
        # the shared executor returns as soon as the 0.2s timeout elapses.
        self.assertLess(elapsed, 2.0)


class RedirectRoutesTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

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

    def test_favicon_route_does_not_404(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 204)

    def test_robots_route_does_not_404(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertIn("User-agent: *", response.get_data(as_text=True))


class FrontendAndBootstrapRegressionTests(unittest.TestCase):
    def test_stats_zero_state_is_rendered_explicitly(self):
        js_path = os.path.join(API_DIR, "static", "js", "app.js")
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

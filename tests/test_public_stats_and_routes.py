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


class FrontendAndBootstrapRegressionTests(unittest.TestCase):
    def test_stats_zero_state_is_rendered_explicitly(self):
        template_path = os.path.join(API_DIR, "templates", "index.html")
        with open(template_path, "r", encoding="utf-8") as file_obj:
            template = file_obj.read()

        self.assertIn("if (safeStart === safeEnd)", template)
        self.assertIn("obj.innerHTML = safeEnd.toLocaleString();", template)
        self.assertIn("function syncDemoMapLayout()", template)
        self.assertIn("--demo-map-height", template)

    def test_railway_init_includes_analytics_sql(self):
        init_script = os.path.join(ROOT_DIR, "scripts", "init_railway_db.py")
        with open(init_script, "r", encoding="utf-8") as file_obj:
            content = file_obj.read()

        self.assertIn("06_create_analytics_tables.sql", content)


if __name__ == "__main__":
    unittest.main()

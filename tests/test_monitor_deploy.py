import os
import sys
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import monitor_deploy  # noqa: E402


class MonitorDeployContractTests(unittest.TestCase):
    def test_observability_healthy_contract(self):
        payload = {
            "status": "healthy",
            "critical_checks": {
                "database": True,
                "analytics": True,
                "google_earth_engine": True,
                "google_maps_key": True,
            },
            "analytics": {"ready": True},
        }

        healthy, reason = monitor_deploy.evaluate_response("/api/v1/observability", 200, payload)

        self.assertTrue(healthy)
        self.assertEqual(reason, "ok")

    def test_observability_degraded_when_analytics_not_ready(self):
        payload = {
            "status": "degraded",
            "critical_checks": {
                "database": True,
                "analytics": False,
                "google_earth_engine": True,
                "google_maps_key": True,
            },
            "analytics": {"ready": False},
        }

        healthy, reason = monitor_deploy.evaluate_response("/api/v1/observability", 503, payload)

        self.assertFalse(healthy)
        self.assertEqual(reason, "observability reports degraded state")

    def test_stats_requires_integer_counters(self):
        payload = {"visits": "0", "analyses": 1}

        healthy, reason = monitor_deploy.evaluate_response("/api/v1/stats", 200, payload)

        self.assertFalse(healthy)
        self.assertEqual(reason, "stats payload missing integer counters")

    def test_health_requires_healthy_status(self):
        payload = {"status": "degraded"}

        healthy, reason = monitor_deploy.evaluate_response("/api/v1/health", 200, payload)

        self.assertFalse(healthy)
        self.assertEqual(reason, "health payload invalid")


class MonitorDeployRetryTests(unittest.TestCase):
    @patch.object(monitor_deploy.time, "sleep")
    @patch.object(monitor_deploy, "run_checks", side_effect=[False, True])
    def test_run_with_retries_stops_after_success(self, mock_run_checks, mock_sleep):
        healthy = monitor_deploy.run_with_retries(
            "https://geofeedback.cl",
            monitor_deploy.DEFAULT_ENDPOINTS,
            retries=3,
            retry_delay=1,
        )

        self.assertTrue(healthy)
        self.assertEqual(mock_run_checks.call_count, 2)
        mock_sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()

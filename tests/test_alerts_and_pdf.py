import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
import app.db.session as session_module
import app.core.auth as auth_module
from app.db.models import User, UserAlert, UserAnalysis
from app.tasks.tasks_periodic import check_active_alerts

class AlertsAndPdfTests(unittest.TestCase):
    def setUp(self):
        from app.core.config import settings
        self.original_secret = settings.SECRET_KEY
        settings.SECRET_KEY = "test-secret-key-1234567890-abcdef-ghijkl"

        self.client = TestClient(app)
        self.mock_session = MagicMock()
        self.mock_session.__enter__.return_value = self.mock_session
        app.dependency_overrides[session_module.get_session] = lambda: self.mock_session
        
        # Crear usuario de prueba
        self.fake_user = User(
            id=12,
            google_sub="sub-12",
            email="testuser@geofeedback.cl",
            name="Test User Alert"
        )
        self.token = auth_module.create_session_token(self.fake_user)
        self.client.cookies.set("session", self.token)
        
        # Por defecto, mock_session.get devuelve el usuario de prueba o None según el modelo
        def mock_get(model, id_val):
            if model == User:
                return self.fake_user
            return None
        self.mock_session.get.side_effect = mock_get

        # Cuando se llama a session.add, le asignamos un ID ficticio para cumplir con el esquema
        def mock_add(obj):
            if hasattr(obj, "id") and obj.id is None:
                obj.id = 1
        self.mock_session.add.side_effect = mock_add

    def tearDown(self):
        from app.core.config import settings
        settings.SECRET_KEY = self.original_secret
        app.dependency_overrides.clear()

    def test_create_alert_requires_auth(self):
        # Limpiar cookie de sesión para simular anónimo
        client_anon = TestClient(app)
        response = client_anon.post("/api/v1/alerts", json={
            "location_name": "Santiago",
            "lat": -33.44,
            "lng": -70.66,
            "radius": 1000,
            "approach": "agriculture"
        })
        self.assertEqual(response.status_code, 401)

    def test_create_alert_success_and_free_limit(self):
        # Simular que el usuario no tiene alertas creadas actualmente
        self.mock_session.exec.return_value.all.return_value = []
        
        # Mocking el retorno del save/refresh en DB
        saved_alert = UserAlert(
            id=1,
            user_id=self.fake_user.id,
            location_name="Santiago, Chile",
            lat=-33.4489,
            lng=-70.6693,
            radius=1000,
            approach="agriculture",
            trigger_type="ndvi_below",
            trigger_value=0.3
        )
        
        # Configurar mock para guardar
        def mock_commit():
            pass
        self.mock_session.commit = mock_commit
        
        # Cuando se llama a session.add y session.refresh
        self.mock_session.refresh = lambda x: None
        
        response = self.client.post("/api/v1/alerts", json={
            "location_name": "Santiago, Chile",
            "lat": -33.4489,
            "lng": -70.6693,
            "radius": 1000,
            "approach": "agriculture",
            "trigger_type": "ndvi_below",
            "trigger_value": 0.3
        })
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["location_name"], "Santiago, Chile")
        self.assertEqual(response.json()["trigger_type"], "ndvi_below")

        # Probar el límite: ahora simular que el usuario ya tiene 1 alerta activa
        self.mock_session.exec.return_value.all.return_value = [saved_alert]
        
        response_limit = self.client.post("/api/v1/alerts", json={
            "location_name": "Valparaíso",
            "lat": -33.04,
            "lng": -71.61,
            "radius": 2000,
            "approach": "water-management"
        })
        
        self.assertEqual(response_limit.status_code, 400)
        self.assertIn("límite de 1 alerta activa", response_limit.json()["detail"])

    def test_list_alerts(self):
        alert1 = UserAlert(id=1, user_id=self.fake_user.id, location_name="Santiago", lat=-33.4, lng=-70.6, radius=1000, approach="agriculture")
        self.mock_session.exec.return_value.all.return_value = [alert1]

        response = self.client.get("/api/v1/alerts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["location_name"], "Santiago")

    def test_delete_alert_not_found_or_not_owned(self):
        # Alerta pertenece a otro usuario (user_id = 99)
        other_alert = UserAlert(id=5, user_id=99, location_name="Not Mine", lat=-33.4, lng=-70.6, radius=1000, approach="agriculture")
        self.mock_session.get.side_effect = lambda model, id_val: other_alert if model == UserAlert else self.fake_user

        response = self.client.delete("/api/v1/alerts/5")
        self.assertEqual(response.status_code, 404)

    def test_delete_alert_success(self):
        my_alert = UserAlert(id=5, user_id=self.fake_user.id, location_name="Mine", lat=-33.4, lng=-70.6, radius=1000, approach="agriculture")
        # Primero deuelve el alert en get, luego el user de la session si se requiere
        self.mock_session.get.side_effect = lambda model, id_val: my_alert if model == UserAlert else self.fake_user

        response = self.client.delete("/api/v1/alerts/5")
        self.assertEqual(response.status_code, 204) # 204 No Content

    def test_pdf_export_success_from_db(self):
        fake_analysis = UserAnalysis(
            id=1,
            user_id=self.fake_user.id,
            task_id="task-12345",
            location_name="Valparaíso",
            lat=-33.02,
            lng=-71.62,
            radius=2000,
            approach="water-management",
            indices={"NDVI": 0.45, "NDWI": -0.12},
            interpretation="El suelo está estable.",
            image_date="2026-07-15"
        )
        self.mock_session.exec.return_value.first.return_value = fake_analysis

        response = self.client.get("/api/v1/analyze/export/task-12345")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Valparaíso", response.text)
        self.assertIn("NDVI", response.text)
        self.assertIn("El suelo está estable.", response.text)

    @patch("app.tasks.tasks_periodic.init_gee")
    @patch("app.tasks.tasks_periodic.get_sentinel2_image")
    @patch("app.tasks.tasks_periodic.calculate_indices")
    @patch("app.tasks.tasks_periodic.get_info_with_timeout")
    @patch("app.tasks.tasks_periodic.send_alert_email")
    def test_periodic_alerts_task_execution(self, mock_send_email, mock_get_info, mock_calc_indices, mock_get_s2, mock_init_gee):
        # Configurar datos de simulación
        my_alert = UserAlert(
            id=3,
            user_id=self.fake_user.id,
            location_name="Monitoreo Agrícola",
            lat=-33.5,
            lng=-70.5,
            radius=1000,
            approach="agriculture",
            trigger_type="ndvi_below",
            trigger_value=0.4,
            is_active=True
        )
        
        # Mocks de base de datos
        self.mock_session.exec.return_value.all.return_value = [my_alert]
        self.mock_session.get.return_value = self.fake_user
        
        # Mock de Earth Engine
        mock_get_s2.return_value = MagicMock()
        mock_calc_indices.return_value.select.return_value.reduceRegion.return_value = MagicMock()
        
        # Simular que el NDVI promedio obtenido es 0.35 (menor que el trigger de 0.4)
        mock_get_info.return_value = {"NDVI": 0.35}
        
        # Ejecutar la tarea periódica
        with patch("app.tasks.tasks_periodic.Session", return_value=self.mock_session):
            check_active_alerts()
            
        # Verificar que se disparó la alerta y se envió el correo
        mock_send_email.assert_called_once_with(
            to_email=self.fake_user.email,
            location_name=my_alert.location_name,
            trigger_desc="NDVI menor a 0.4",
            index_name="NDVI",
            current_value=0.35
        )
        
        # Verificar que se actualizó el último valor en el registro de alerta
        self.assertEqual(my_alert.last_index_value, 0.35)
        self.assertIsNotNone(my_alert.last_checked_at)

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from employe.models import Employe
from pointage.models import Attendance


class AttendanceApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employe = Employe.objects.create_user(
            username="pointeur", first_name="Pointe", last_name="Test",
            telephone="620000000", email="pointe@test.local", password="x",
        )

    def setUp(self):
        self.check_in_url = reverse("attendance-check-in")
        self.check_out_url = reverse("attendance-check-out")
        self.status_url = reverse("attendance-current-status")

    def _payload(self):
        return {"employee": str(self.employe.id)}

    def test_check_in_cree_une_session_ouverte(self):
        resp = self.client.post(self.check_in_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data["is_open"])
        self.assertIsNone(resp.data["check_out_time"])
        self.assertEqual(
            Attendance.objects.filter(
                employee=self.employe, check_out_time__isnull=True
            ).count(),
            1,
        )

    def test_double_check_in_refuse(self):
        """Contrainte : pas de 2e arrivée tant que le départ n'est pas pointé."""
        self.client.post(self.check_in_url, self._payload(), format="json")
        resp = self.client.post(self.check_in_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        # Toujours une seule session, aucune créée en doublon.
        self.assertEqual(Attendance.objects.filter(employee=self.employe).count(), 1)

    def test_check_out_cloture_la_session(self):
        self.client.post(self.check_in_url, self._payload(), format="json")
        resp = self.client.post(self.check_out_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["is_open"])
        self.assertIsNotNone(resp.data["check_out_time"])

    def test_check_out_sans_arrivee_refuse(self):
        """Contrainte inverse : pas de départ sans arrivée en cours."""
        resp = self.client.post(self.check_out_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_double_check_out_refuse(self):
        self.client.post(self.check_in_url, self._payload(), format="json")
        self.client.post(self.check_out_url, self._payload(), format="json")
        resp = self.client.post(self.check_out_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_cycle_arrivee_depart_arrivee(self):
        """Après un départ, une nouvelle arrivée est autorisée (2 sessions)."""
        self.client.post(self.check_in_url, self._payload(), format="json")
        self.client.post(self.check_out_url, self._payload(), format="json")
        resp = self.client.post(self.check_in_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Attendance.objects.filter(employee=self.employe).count(), 2)
        self.assertEqual(
            Attendance.objects.filter(
                employee=self.employe, check_out_time__isnull=True
            ).count(),
            1,
        )

    def test_status_reflete_la_presence(self):
        # Absent au départ.
        resp = self.client.get(self.status_url, {"employee": str(self.employe.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["on_site"])
        # Présent après arrivée.
        self.client.post(self.check_in_url, self._payload(), format="json")
        resp = self.client.get(self.status_url, {"employee": str(self.employe.id)})
        self.assertTrue(resp.data["on_site"])
        self.assertIsNotNone(resp.data["open_attendance"])

    def test_status_sans_parametre_employee(self):
        resp = self.client.get(self.status_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

from django.db.models import ProtectedError
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
        # Ce que l'app mobile envoie après scan du QR du badge.
        return {"badge_token": self.employe.badge_token}

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

    def test_status_par_badge_token(self):
        self.client.post(self.check_in_url, self._payload(), format="json")
        resp = self.client.get(self.status_url,
                               {"badge_token": self.employe.badge_token})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["on_site"])

    def test_status_sans_parametre(self):
        resp = self.client.get(self.status_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_badge_inconnu_refuse(self):
        resp = self.client.post(self.check_in_url,
                                {"badge_token": "jeton-bidon-inexistant"},
                                format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_employe_desactive_refuse(self):
        self.employe.is_active = False
        self.employe.save(update_fields=["is_active"])
        resp = self.client.post(self.check_in_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rotation_invalide_ancien_badge(self):
        """Badge perdu/volé : après rotation, l'ancien token ne pointe plus."""
        ancien_token = self.employe.badge_token
        self.employe.rotate_badge_token()
        nouveau_token = self.employe.badge_token
        self.assertNotEqual(ancien_token, nouveau_token)

        # L'ancien badge est refusé.
        resp = self.client.post(self.check_in_url,
                                {"badge_token": ancien_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Le nouveau badge fonctionne.
        resp = self.client.post(self.check_in_url,
                                {"badge_token": nouveau_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_created_by_rempli_si_authentifie(self):
        """L'agent de sécurité connecté est tracé comme auteur de l'arrivée."""
        garde = Employe.objects.create_user(
            username="garde", first_name="Agent", last_name="Securite",
            telephone="620000009", email="garde@test.local", password="x",
        )
        self.client.force_authenticate(user=garde)
        resp = self.client.post(self.check_in_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        att = Attendance.objects.get(employee=self.employe)
        self.assertEqual(att.created_by, garde)

    def test_created_by_null_si_anonyme(self):
        resp = self.client.post(self.check_in_url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        att = Attendance.objects.get(employee=self.employe)
        self.assertIsNone(att.created_by)

    def test_updated_by_et_updated_at_remplis_au_depart(self):
        """Le départ (check-out) trace l'agent et l'horodatage de mise à jour."""
        garde = Employe.objects.create_user(
            username="garde_depart", first_name="Agent", last_name="Depart",
            telephone="620000010", email="garde_depart@test.local", password="x",
        )
        self.client.force_authenticate(user=garde)
        self.client.post(self.check_in_url, self._payload(), format="json")
        self.client.post(self.check_out_url, self._payload(), format="json")
        att = Attendance.objects.get(employee=self.employe)
        self.assertEqual(att.updated_by, garde)
        self.assertIsNotNone(att.updated_at)

    def test_suppression_employe_avec_pointage_protegee(self):
        """PROTECT : un employé ayant des pointages ne peut pas être supprimé."""
        self.client.post(self.check_in_url, self._payload(), format="json")
        with self.assertRaises(ProtectedError):
            self.employe.delete()

    def test_badge_token_genere_automatiquement_et_unique(self):
        autre = Employe.objects.create_user(
            username="pointeur2", first_name="Autre", last_name="Agent",
            telephone="620000001", email="autre@test.local", password="x",
        )
        self.assertTrue(self.employe.badge_token)
        self.assertTrue(autre.badge_token)
        self.assertNotEqual(self.employe.badge_token, autre.badge_token)

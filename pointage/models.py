from django.db import models
from django.db.models import Q, UniqueConstraint

from employe.models import Employe


class Attendance(models.Model):
    # PROTECT : on n'anonymise pas l'historique de pointage — un employé référencé
    # par un pointage ne peut pas être supprimé (préserve la présence/paie).
    employee = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name="attendances")
    check_in_time = models.DateTimeField(auto_now_add=True, db_index=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    # Coordonnées GPS du lieu de pointage (traçabilité : où l'arrivée/le départ a
    # été scanné). Nullable : le check-out reste nul tant que le départ n'est pas
    # pointé, et l'historique antérieur n'a pas de coordonnées. Le caractère
    # obligatoire est imposé à l'entrée API (serializer), pas en base.
    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Agent de sécurité ayant scanné le badge (traçabilité anti-fraude).
    # Nullable : rempli depuis request.user si la requête est authentifiée.
    # created_by = l'arrivée (check-in) ; updated_by = le dernier départ (check-out).
    created_by = models.ForeignKey(
        Employe, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pointages_crees",
    )
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        Employe, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pointages_modifies",
    )

    @property
    def is_open(self):
        """L'employé est sur site : arrivée pointée, départ pas encore pointé."""
        return self.check_out_time is None

    def __str__(self):
        return f"{self.employee.get_full_name()} - IN: {self.check_in_time} - OUT: {self.check_out_time}"

    class Meta:
        ordering = ["-check_in_time"]
        constraints = [
            UniqueConstraint(
                fields=["employee"],
                condition=Q(check_out_time__isnull=True),
                name="unique_open_attendance_per_employee"
            )
        ]
        indexes = [
            models.Index(fields=["employee", "check_out_time"]),
            models.Index(fields=["employee", "check_in_time"]),
        ]
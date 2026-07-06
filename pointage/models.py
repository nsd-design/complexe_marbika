from django.db import models
from django.db.models import Q, UniqueConstraint

from employe.models import Employe


class Attendance(models.Model):
    # PROTECT : on n'anonymise pas l'historique de pointage — un employé référencé
    # par un pointage ne peut pas être supprimé (préserve la présence/paie).
    employee = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name="attendances")
    check_in_time = models.DateTimeField(auto_now_add=True, db_index=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
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
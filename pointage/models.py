from django.db import models
from django.db.models import Q, UniqueConstraint

from employe.models import Employe


class Attendance(models.Model):
    employee = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, related_name="attendances")
    check_in_time = models.DateTimeField(auto_now_add=True, db_index=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    @property
    def is_open(self):
        """L'employé est sur site : arrivée pointée, départ pas encore pointé."""
        return self.check_out_time is None

    def __str__(self):
        nom = self.employee.get_full_name() if self.employee else "Employé supprimé"
        return f"{nom} - IN: {self.check_in_time} - OUT: {self.check_out_time}"

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
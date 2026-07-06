from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from pointage.models import Attendance
from pointage.serializers import AttendanceSerializer, CheckActionSerializer

DEJA_ARRIVE = ("Cet employé a déjà pointé son arrivée. "
               "Il doit d'abord pointer son départ.")
PAS_ARRIVE = ("Aucun pointage d'arrivée en cours. "
              "L'employé doit d'abord pointer son arrivée.")


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Pointage des employés.

    Lecture (historique) :
      - GET  attendance/                 liste (filtres: ?employee=<id>&open=true)
      - GET  attendance/{id}/            détail

    Actions :
      - POST attendance/check-in/        pointer une arrivée  {"employee": <id>}
      - POST attendance/check-out/       pointer un départ    {"employee": <id>}
      - GET  attendance/status/?employee=<id>   état courant d'un employé

    Contrainte : jamais de doublon arrivée/départ. Un employé ne peut pointer
    une arrivée tant qu'un départ n'est pas enregistré, et inversement.
    """
    queryset = Attendance.objects.select_related("employee").all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        employee = self.request.query_params.get("employee")
        if employee:
            qs = qs.filter(employee_id=employee)
        if self.request.query_params.get("open") in ("1", "true", "True"):
            qs = qs.filter(check_out_time__isnull=True)
        return qs

    @action(detail=False, methods=["post"], url_path="check-in",
            serializer_class=CheckActionSerializer)
    def check_in(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.validated_data["employee"]

        # Garde applicative (message clair) + garde DB (UniqueConstraint sur
        # les sessions ouvertes) qui verrouille le cas de concurrence.
        try:
            with transaction.atomic():
                if Attendance.objects.filter(
                    employee=employee, check_out_time__isnull=True
                ).exists():
                    return Response({"detail": DEJA_ARRIVE},
                                    status=status.HTTP_409_CONFLICT)
                attendance = Attendance.objects.create(employee=employee)
        except IntegrityError:
            # Course entre deux requêtes concurrentes : la contrainte a tranché.
            return Response({"detail": DEJA_ARRIVE},
                            status=status.HTTP_409_CONFLICT)

        return Response(AttendanceSerializer(attendance).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="check-out",
            serializer_class=CheckActionSerializer)
    def check_out(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.validated_data["employee"]

        with transaction.atomic():
            # select_for_update verrouille la session ouverte : deux départs
            # concurrents ne peuvent pas la clôturer en double.
            attendance = (
                Attendance.objects.select_for_update()
                .filter(employee=employee, check_out_time__isnull=True)
                .first()
            )
            if attendance is None:
                return Response({"detail": PAS_ARRIVE},
                                status=status.HTTP_409_CONFLICT)
            attendance.check_out_time = timezone.now()
            attendance.save(update_fields=["check_out_time"])

        return Response(AttendanceSerializer(attendance).data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="status")
    def current_status(self, request):
        employee_id = request.query_params.get("employee")
        if not employee_id:
            return Response({"detail": "Le paramètre 'employee' est requis."},
                            status=status.HTTP_400_BAD_REQUEST)
        open_attendance = (
            Attendance.objects.select_related("employee")
            .filter(employee_id=employee_id, check_out_time__isnull=True)
            .first()
        )
        return Response({
            "employee": employee_id,
            "on_site": open_attendance is not None,
            "open_attendance": (AttendanceSerializer(open_attendance).data
                                if open_attendance else None),
        })

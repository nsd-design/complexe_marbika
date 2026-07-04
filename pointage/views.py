from django.shortcuts import render
from rest_framework import viewsets

from pointage.models import Attendance
from pointage.serializers import AttendanceSerializer


class AttendanceView(viewsets.ModelViewSet):
    """
    API endpoint that allows Attendances to be viewed or edited.
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
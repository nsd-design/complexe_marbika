from rest_framework import serializers

from employe.models import Employe
from pointage.models import Attendance


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employe
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'
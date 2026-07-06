from rest_framework import serializers

from employe.models import Employe
from pointage.models import Attendance


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employe
        # Champs explicites : Employe hérite de AbstractUser, un '__all__'
        # exposerait password, is_superuser, permissions, etc.
        fields = ["id", "first_name", "last_name", "full_name", "telephone", "email"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class AttendanceSerializer(serializers.ModelSerializer):
    """Sérialiseur de lecture (list / retrieve / réponses check-in/out)."""
    employee = EmployeeSerializer(read_only=True)
    created_by = EmployeeSerializer(read_only=True)
    updated_by = EmployeeSerializer(read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ["id", "employee", "check_in_time", "check_out_time",
                  "created_by", "updated_at", "updated_by",
                  "is_open", "duration_seconds"]
        read_only_fields = fields

    def get_duration_seconds(self, obj):
        if obj.check_out_time:
            return int((obj.check_out_time - obj.check_in_time).total_seconds())
        return None


class CheckActionSerializer(serializers.Serializer):
    """
    Entrée des actions check-in / check-out : le badge scanné.

    Le QR contient le badge_token opaque ; on résout l'employé côté serveur.
    L'employé résolu est déposé dans validated_data["employee"] pour la vue.
    """
    badge_token = serializers.CharField(write_only=True, trim_whitespace=True)

    def validate_badge_token(self, value):
        try:
            employe = Employe.objects.get(badge_token=value)
        except Employe.DoesNotExist:
            raise serializers.ValidationError("Badge inconnu.")
        if not employe.is_active:
            raise serializers.ValidationError("Employé désactivé.")
        self._employe = employe
        return value

    def validate(self, attrs):
        attrs["employee"] = self._employe
        return attrs

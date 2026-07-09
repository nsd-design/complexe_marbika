from django.contrib import admin

from pointage.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "check_in_time", "check_out_time", "is_open")
    list_filter = ("check_in_time", "check_out_time")
    search_fields = ("employee__first_name", "employee__last_name", "employee__telephone")
    date_hierarchy = "check_in_time"
    autocomplete_fields = ("employee",)
    # Coordonnées GPS du pointage : consultables mais non modifiables (renseignées
    # à la volée par l'app mobile lors du scan).
    readonly_fields = ("check_in_latitude", "check_in_longitude",
                       "check_out_latitude", "check_out_longitude")

    @admin.display(boolean=True, description="Sur site")
    def is_open(self, obj):
        return obj.is_open

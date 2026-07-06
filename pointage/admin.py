from django.contrib import admin

from pointage.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "check_in_time", "check_out_time", "is_open")
    list_filter = ("check_in_time", "check_out_time")
    search_fields = ("employee__first_name", "employee__last_name", "employee__telephone")
    date_hierarchy = "check_in_time"
    autocomplete_fields = ("employee",)

    @admin.display(boolean=True, description="Sur site")
    def is_open(self, obj):
        return obj.is_open

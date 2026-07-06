from django.contrib import admin
from django.apps import apps
from django.contrib.auth.admin import UserAdmin

from employe.forms import EmployeCreationForm, EmployeChangeForm
from employe.models import Employe


@admin.register(Employe)
class EmployeAdmin(UserAdmin):
    add_form = EmployeCreationForm
    form = EmployeChangeForm
    model = Employe

    list_display = ("username", "first_name", "last_name", "telephone", "is_staff")
    list_filter = ("is_staff", "is_active")
    actions = ("regenerer_badge",)
    readonly_fields = ("badge_token",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "email", "telephone")}),
        ("Badge de pointage", {"fields": ("badge_token",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    @admin.action(description="Régénérer le badge (révoquer l'ancien)")
    def regenerer_badge(self, request, queryset):
        for employe in queryset:
            employe.rotate_badge_token()
        self.message_user(request, f"{queryset.count()} badge(s) régénéré(s).")

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "first_name", "last_name", "email", "telephone", "password1", "password2"),
        }),
    )

    search_fields = ("username", "telephone", "email")
    ordering = ("username",)

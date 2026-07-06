from django.urls import include, path
from rest_framework import routers

from pointage import views

router = routers.DefaultRouter()
router.register(r"attendance", views.AttendanceViewSet, basename="attendance")

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from pointage import views

router = routers.DefaultRouter()
router.register(r"attendance", views.AttendanceViewSet, basename="attendance")

urlpatterns = [
    path('', include(router.urls)),
    # POST {username, password} -> {"token": "..."} ; endpoint public (l'app
    # mobile s'y authentifie pour obtenir son jeton).
    path('token/', obtain_auth_token, name='api_token_auth'),
]
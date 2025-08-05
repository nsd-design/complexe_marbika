from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.create_client, name="create_client"),
    path("location_reservation/", views.location_reservation, name="location_reservation"),
    path("location_reservation/louer", views.location_reservation, name="louer"),
]
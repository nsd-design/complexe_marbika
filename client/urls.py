from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.create_client, name="create_client"),
    path("location_reservation/", views.location_reservation, name="location_reservation"),
    path("location_reservation/louer/", views.create_location, name="louer"),
    path("location_reservation/create_zone/", views.create_zone, name="create_zone"),
    path("location_reservation/reserver/", views.create_reservation, name="create_reservation"),
]
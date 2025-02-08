from django.urls import path

from salon.views import services, add_category, add_service

urlpatterns = [
    path("services/", services, name="services"),
    path("services/add/", add_service, name="add_service"),
    path("categorie/add/", add_category, name="add_categorie"),
]
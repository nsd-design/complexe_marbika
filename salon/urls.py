from django.urls import path

from salon.views import *

urlpatterns = [
    path("services/", services, name="services"),
    path("services/add/", add_service, name="add_service"),
    path("categorie/add/", add_category, name="add_categorie"),
    path("prix/", prix_services, name="prix_services"),
    path("prix/add/", add_prix_service, name="add_prix_services"),
]
from django.urls import path

from restaurant.views import *

urlpatterns = [
    path("", plats_boissons, name="plats_boissons"),
    path("plat", create_plat, name="create_plat"),
    path("boisson", create_boisson, name="create_boisson"),
    path("commandes/", commande, name="commandes")
]
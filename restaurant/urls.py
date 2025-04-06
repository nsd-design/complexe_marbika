from django.urls import path

from restaurant.views import *

urlpatterns = [
    path("", plats_boissons, name="plats_boissons"),
    path("plat", create_plat, name="create_plat"),
    path("boisson", create_boisson, name="create_boisson"),
    path("boisson/approvisionner", approvisionner_boisson, name="appro_boisson"),
    path("commandes/", commande, name="commandes"),
    path("commandes/get_commandes/", get_commandes, name="get_commandes"),
    path("commandes/details/<str:id_commande>/", details_commande, name="details_commande"),
    path("commandes/passer_commande", passer_commande, name="passer_commande"),
    path("boisson/controle/", controle_boissons, name="controle_boissons"),
    path("boisson/nouveau_controle/", create_controle_boissons, name="nouveau_controle"),
    path("boisson/cloture_controle/", cloture_controle, name="cloture_controle"),
]
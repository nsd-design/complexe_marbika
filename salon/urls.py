from django.urls import path

from salon.views import *

urlpatterns = [
    path("services/", services, name="services"),
    path("services/add/", add_service, name="add_service"),
    path("services/get_services/", get_services, name="get_services"),
    path("services/get/", get_service, name="get_service"),
    path("services/update/", update_service, name="update_service"),
    path("categorie/add/", add_category, name="add_categorie"),
    path("categorie/get_categories/", get_categories, name="get_categories"),
    path("prix/", prix_services, name="prix_services"),
    path("prix/add/", add_prix_service, name="add_prix_services"),
    path("prestations/", prestations, name="prestations"),
    path("prestations/add/", add_prestation, name="add_prestations"),
    path("prestations/<str:service_id>/", get_prix_service, name="get_prix_service"),
    path("produits/", produits, name="produits"),
    path("produits/add/", add_produit, name="add_produit"),
    path("produits/list/", get_produits, name="get_produits"),
    path("produits/appro/", approvisionner_produit, name="approvisionner"),
    path("produits/shop/", shop_produits, name="shop"),
    path("produits/vente/", vente_produits, name="vente_produits"),
    path("produits/list_clients/", get_clients, name="list_clients"),
    path("produits/liste_ventes/", get_ventes, name="liste_ventes"),
]
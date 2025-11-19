from django.urls import path

from employe import views

urlpatterns = [
    path("", views.employe, name="employe"),
    path("list/", views.get_employes, name="get_employes"),
    path("add/", views.add_employe, name="add_employe"),
    path("dashmin/filtre/", views.filtre_dashmin_data, name="filtre_dashmin_data"),
    path("dashmin/situation_salon/", views.entrees_sorties_salon, name="entrees_sorties_salon"),
    path("dashmin/situation_resto/", views.entrees_sorties_restaurant, name="entrees_sorties_resto"),
    path("performances/", views.performances, name="performances"),
    path("performances/performances_par_date/", views.performances_par_date, name="performances_par_date"),
    path("performances/details_prestation_par_id/<str:id_init_prest>/", views.details_prestation_par_id, name="details_prestation_par_id"),
]
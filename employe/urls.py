from django.urls import path

from employe import views

urlpatterns = [
    path("", views.employe, name="employe"),
    path("list/", views.get_employes, name="get_employes"),
    path("add/", views.add_employe, name="add_employe"),
]
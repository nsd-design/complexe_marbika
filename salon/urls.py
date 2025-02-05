from django.urls import path

from salon.views import services, add_category

urlpatterns = [
    path("services/", services, name="services"),
    path("categorie/add/", add_category, name="add_categorie"),
]
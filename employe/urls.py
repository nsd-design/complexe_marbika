from django.urls import path

from employe.views import add_employe, employe

urlpatterns = [
    path("", employe, name="employe"),
    path("add/", add_employe, name="add_employe"),
]
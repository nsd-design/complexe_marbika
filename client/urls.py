from django.urls import path

from client.views import create_client

urlpatterns = [
    path("create/", create_client, name="create_client")
]
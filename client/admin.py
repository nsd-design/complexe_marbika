from django.contrib import admin
from django.apps import apps


my_app = apps.get_app_config('client')
for model_name, model in my_app.models.items():
    admin.site.register(model)

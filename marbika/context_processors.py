from django.urls import resolve


# Recuperer l'url de la page en cours
def current_url_name(request):
    return {"current_url_name": resolve(request.path_info).url_name}

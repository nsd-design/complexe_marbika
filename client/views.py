import json
from django.utils.html import escape

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from client.models import Client


def telephone_exists(telephone):
    # Check if Telephone already Exists
    phone = telephone.replace(" ", "")  # Supprimer les espaces dans le numéro
    try:
        client_found = Client.objects.get(telephone=phone)  # Recherche dans la DB
        return True
    except Client.DoesNotExist:
        return False


@require_http_methods(["POST"])
def create_client(request):
    try:
        data = json.loads(request.body)
        client = data.get('client')

        required_fields = ['sexe']
        for field in required_fields:
            if not escape(client.get(field)):
                return JsonResponse({"error": True, "msg": f"Le champ '{field}' est obligatoire."}, status=400)

        fullname = escape(client.get('fullname'))
        telephone = escape(client.get('telephone'))
        sexe = escape(client.get('sexe'))
        if telephone_exists(telephone):
            return JsonResponse({"error": True, "msg": "Ce Numéro existe déjà dans la Base de Données."}, status=400)

        Client.objects.create(
            nom_complet=fullname, telephone=telephone, sexe=int(sexe)
        )

        return JsonResponse({"success": True, "msg": "Nouveau Client créé avec succès !"}, status=200)

    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Une erreur est survenue lors de la création du Client, réessayer"}, status=400)

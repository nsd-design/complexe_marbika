import http
import json
from django.utils.html import escape

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from client.models import Client, ZoneAReserver, Location
from . import forms
from .forms import ZoneForm, LocationForm

tmp_base = "client/"

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


@require_http_methods(["GET"])
def location_reservation(request):
    context = {
        "page_title": "Location & Réservation",
        "form": forms.LocationForm(),
        "zone_form": ZoneForm()
    }
    return render(request, tmp_base + "location_reservation.html", context)


@require_http_methods(["POST"])
def create_zone(request):
    zone_form = ZoneForm(request.POST)
    if zone_form.is_valid():
        nom = zone_form.cleaned_data["nom"]
        statut = zone_form.cleaned_data["statut"]
        try:
            ZoneAReserver.objects.create(nom=nom, statut=statut)
            return JsonResponse({"success": True, "msg": "Zone crée avec succès !"})
        except Exception as e:
            print("Erreur :", e)
            return JsonResponse({"error": True, "msg": str(e)}, status=400)
    else:
        return JsonResponse({"error": True, "msg": "Données invalides"}, status=400)


@require_http_methods(["POST"])
def create_location(request):
    try:
        data = json.loads(request.body)

        id_client = escape(data.get("id_client"))
        id_zone = escape(data.get("id_zone"))
        montant_a_payer = escape(data.get("montant_a_payer"))
        remise = escape(data.get("remise"))
        date_debut = escape(data.get("date_debut"))
        date_fin = escape(data.get("date_fin"))
        statut = escape(data.get("statut"))
        type_location = escape(data.get("type_location"))
        description = escape(data.get("description"))

        current_client = Client.objects.get(id=id_client)
        current_zone = ZoneAReserver.objects.get(id=id_zone)

        Location.objects.create(
            locateur=current_client, zone=current_zone, description=description, montant_a_payer=montant_a_payer,
            montant_reduit=int(remise), date_debut=date_debut, date_fin=date_fin, statut=statut, type_location=type_location,
        )

        return JsonResponse({"success": True, "msg": f"Location enregistrée avec succès."})
    except Client.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Le Client n'a été trouvé dans la Base de données"})
    except ZoneAReserver.DoesNotExist:
        return JsonResponse({"error": True, "msg": "La Zone à louer n'a été trouvé dans la Base de données"})
    except Exception as e:
        print("Erreur :", e)
        return JsonResponse({"error": True, "msg": str(e)})
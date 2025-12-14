import http
import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils.html import escape

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from client.models import Client, ZoneAReserver, Location, Reservation, Piscine
from . import forms
from .forms import ZoneForm, LocationForm, ReservationForm, PiscineForm
from salon.views import currency

tmp_base = "client/"

def telephone_exists(telephone):
    # Check if Telephone already Exists
    phone = telephone.replace(" ", "")  # Supprimer les espaces dans le numéro
    try:
        client_found = Client.objects.get(telephone=phone)  # Recherche dans la DB
        return True
    except Client.DoesNotExist:
        return False


@login_required(login_url="login")
@require_http_methods(["POST"])
def create_client(request):
    try:
        data = json.loads(request.body)
        client = data.get('client')

        required_fields = ['sexe', 'fullname']
        for field in required_fields:
            if not escape(client.get(field)):
                return JsonResponse({"error": True, "msg": f"Le champ '{field}' est obligatoire."}, status=400)

        fullname = escape(client.get('fullname'))
        telephone = escape(client.get('telephone'))
        sexe = escape(client.get('sexe'))
        if telephone and telephone_exists(telephone):
            return JsonResponse({"error": True, "msg": "Ce Numéro existe déjà dans la Base de Données."}, status=400)

        Client.objects.create(
            nom_complet=fullname, telephone=telephone, sexe=int(sexe)
        )

        return JsonResponse({"success": True, "msg": "Nouveau Client créé avec succès !"}, status=200)

    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Une erreur est survenue lors de la création du Client, réessayer"}, status=400)


@login_required(login_url="login")
@require_http_methods(["GET"])
def location_reservation(request):
    context = {
        "page_title": "Location & Réservation",
        "form": forms.LocationForm(),
        "zone_form": ZoneForm(),
        "reservation_form": ReservationForm(),
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


@login_required(login_url="login")
@require_http_methods(["POST"])
def create_location(request):
    try:
        data = json.loads(request.body)

        id_client = escape(data.get("id_client"))
        id_zone = escape(data.get("id_zone"))

        if not check_zone_libre(id_zone):
            return JsonResponse({"error": True, "msg": "Cette Zone est déjà réservée."}, status=404)

        with transaction.atomic():

            current_client = Client.objects.get(id=id_client)
            current_zone = ZoneAReserver.objects.get(id=id_zone)

            Location.objects.create(
                locateur=current_client, zone=current_zone, description=escape(data.get("description")), montant_a_payer=escape(data.get("montant_a_payer")),
                montant_reduit=escape(data.get("remise")), date_debut=escape(data.get("date_debut")),
                date_fin=escape(data.get("date_fin")), statut=escape(data.get("statut")), type_location=escape(data.get("type_location")),
            )

            current_zone.statut = 'reserve'
            current_zone.save()

        return JsonResponse({"success": True, "msg": f"Location enregistrée avec succès."})
    except Client.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Le Client n'a été trouvé dans la Base de données"})
    except ZoneAReserver.DoesNotExist:
        return JsonResponse({"error": True, "msg": "La Zone à louer n'a été trouvé dans la Base de données"})
    except Exception as e:
        print("Erreur :", e)
        return JsonResponse({"error": True, "msg": str(e)})


# Verifier si la zone à reserver est 'libre' et renvoyer 'True'
def check_zone_libre(id_zone):
    try:
        ZoneAReserver.objects.get(id=id_zone, statut='libre')
        return True
    except ZoneAReserver.DoesNotExist:
        return False


@login_required(login_url="login")
@require_http_methods(["POST"])
def create_reservation(request):
    try:
        data = json.loads(request.body)

        id_client = escape(data.get("id_client"))
        id_zone = escape(data.get("id_zone"))

        if not check_zone_libre(id_zone):
            return JsonResponse({"error": True, "msg": "Cette Zone est déjà réservée."}, status=404)

        with transaction.atomic():

            reservation_reussie = False

            current_client = Client.objects.get(id=id_client)
            current_zone = ZoneAReserver.objects.get(id=id_zone)

            # Créer la Réservation
            new_reservation = Reservation.objects.create(
                type=escape(data.get("type")), client=current_client, zone=current_zone, etat_reservation=escape(data.get("statut")),
                date_debut=escape(data.get("date_debut")), date_fin=escape(data.get("date_fin")), commentaire=escape(data.get("commentaire"))
            )

            # Mettre à jour la Zone réservée, mettre son statut sur "reserve"
            if new_reservation:
                current_zone.statut = 'reserve'
                current_zone.save()

                reservation_reussie = True

            if not reservation_reussie:
                raise Exception("Erreur inattendue")
        return JsonResponse({"success": True, "msg": "Réservation effectuée avec succès."})

    except Client.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Le Client est introuvable."}, status=404)

    except ZoneAReserver.DoesNotExist:
        return JsonResponse({"error": True, "msg": "La zone à reserver est introuvable."}, status=404)

    except Exception as e:
        print("Erreur :", e)
        return JsonResponse({"error": True, "msg": str(e)})


@require_http_methods(["GET"])
def get_locations(request):
    try:
        list_locations: list = []

        locations = Location.objects.all()

        for location in locations:
            net_paye = location.montant_a_payer - location.montant_reduit
            list_locations.append({
                "id": location.id,
                "locateur": location.locateur.nom_complet,
                "telephone": location.locateur.telephone,
                "objet": location.objet,
                "zone": location.zone.nom,
                "description": location.description,
                "montant_a_payer": currency(location.montant_a_payer),
                "remise": currency(location.montant_reduit),
                "date_debut": location.date_debut.strftime("%d/%m/%Y"),
                "date_fin": location.date_fin.strftime("%d/%m/%Y"),
                "statut": location.get_statut_display(),
                "type_location": location.get_type_location_display(),
                "net_paye": f'<span class="text-success">{currency(net_paye)}</span>',
            })
        return JsonResponse({"success": True, "data": list_locations})
    except Location.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Aucune Location enregistrée."}, status=404)


@require_http_methods(["GET"])
def get_reservations(request):
    try:
        reservations = Reservation.objects.all()

        list_reservations: list = []

        for reservation in reservations:
            list_reservations.append({
                "id": reservation.id,
                "type": reservation.get_type_display(),
                "client": reservation.client.nom_complet,
                "telephone": reservation.client.telephone,
                "zone": reservation.zone.nom,
                "etat_reservation": reservation.get_etat_reservation_display(),
                "date_debut": reservation.date_debut.strftime("%d/%m/%Y"),
                "date_fin": reservation.date_fin.strftime("%d/%m/%Y"),
                "commentaire": reservation.commentaire,
            })
        return JsonResponse({"success": True, "data": list_reservations}, status=200)
    except Reservation.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Aucune reservation trouvée."}, status=404)

def gestion_piscine(request):
    context = {
        "page_title": "Gestion de la Piscine",
        "form": PiscineForm(),
    }
    return render(request, tmp_base + "gestion_piscine.html", context=context)

@require_http_methods(["POST"])
def pool_entry(request):
    try:
        data = json.loads(request.body)
        nb_client = data.get('nb_client')
        prix_unitaire = data.get('prix_unitaire')
        reduction = data.get('reduction')
        note = data.get('note')
        Piscine.objects.create(nb_client=nb_client, prix_unitaire=prix_unitaire, reduction=reduction, note=note)
        return JsonResponse({"success": True, "msg": "Enregistrement effectué avec succès."}, status=201)
    except json.decoder.JSONDecodeError:
        print("Erreur, format de données invalide")
        return JsonResponse({"success": False, "msg": "Erreur, format de données invalide"}, 400)
    except Exception as e:
        print("Erreur ", str(e))
        return JsonResponse({"success": False, "msg": str(e)})


@require_http_methods(["POST"])
def pool_records_per_date(request):
    try:
        data = json.loads(request.body)
        date_debut_str = data.get("dateDebut")
        date_fin_str = data.get("dateFin")

        # Convertir en datetime naive
        date_debut_naive = datetime.strptime(date_debut_str, "%Y-%m-%d")
        date_fin_naive = datetime.strptime(date_fin_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

        # Rendre aware selon TIME_ZONE défini dans settings.py
        date_debut = timezone.make_aware(date_debut_naive)
        date_fin = timezone.make_aware(date_fin_naive)

        records = Piscine.objects.filter(
            created_at__gte=date_debut, created_at__lte=date_fin
        ).order_by("-created_at")

        records_list: list = []

        for record in records:
            records_list.append({
                "id": record.id,
                "nb_client": record.nb_client,
                "prix_unitaire": currency(record.prix_unitaire),
                "total": currency(record.nb_client * record.prix_unitaire),
                "reduction": record.reduction,
                "created_at": record.created_at.strftime("%d/%m/%Y"),
                "note": record.note,
            })
        return JsonResponse({"success": True, "data": records_list}, status=200)
    except Piscine.DoesNotExist:
        return JsonResponse({"success": False, "msg": "Aucun enregistrement trouvé."}, status=404)

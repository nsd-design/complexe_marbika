import http
import json
from collections import defaultdict
from datetime import date, timedelta

import django.db.utils
from django.db import IntegrityError
from django.db.models import Sum, Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from employe.forms import EmployeForm
from employe.models import Employe
from salon.models import Vente, Depense, InitPrestation, Prestation
from salon.views import currency

tmp_base = "employe/"


def semaines():
    today = date.today()
    current_year = today.year

    # Commencer a partir du 1er Jan
    start_date = date(current_year, 1, 1)

    # Trouver le Lundi de la 1ere semaine
    start_date -= timedelta(days=start_date.weekday())

    list_semaines: list = []

    while start_date <= today:
        numero_semaine =  start_date.isocalendar().week
        annee_semaine = start_date.isocalendar().year
        mois_semaine = start_date.strftime("%B")
        num_mois_semaine = start_date.month

        list_semaines.append({
            "numero_semaine": numero_semaine,
            "annee_semaine": annee_semaine,
            "mois_semaine": mois_semaine,
            "num_mois_semaine": num_mois_semaine,
        })

        start_date += timedelta(weeks=1)

    list_semaines = sorted(list_semaines, key=lambda k: k['numero_semaine'], reverse=True)
    return list_semaines


def groupe_prestations_par_reference(year: int):
    init_prestations = InitPrestation.objects.prefetch_related(
        'prestation_set__fait_par',
        'prestation_set__service',
    ).order_by('-created_at')

    prestation_par_prestataire: list = []

    for init_pres in init_prestations:
        employe_data = defaultdict(lambda : {
            "initiales": "",
            "nom": "",
            "prenom": "",
            "email": "",
            "nb_services": 0,
            "services": list(),
        })

        for prestation in init_pres.prestation_set.all():
            prestataire = prestation.fait_par
            service = prestation.service

            if prestataire and service:
                key = prestataire.id
                employe_data[key]["nom"] = prestataire.last_name
                employe_data[key]["prenom"] = prestataire.first_name
                employe_data[key]["email"] = prestataire.email
                employe_data[key]["nb_services"] += 1
                employe_data[key]["services"].append(service.designation)

        prestation_par_prestataire.append({
            "reference": init_pres.reference,
            "montant_total": currency(init_pres.montant_total),
            "remise": currency(init_pres.remise),
            "net_paye": currency(init_pres.montant_total - init_pres.remise),
            "date": init_pres.created_at.strftime("%d/%m/%Y"),
            "prestataire": [
                {
                    "initiales": data["prenom"][0] + "" + data["nom"][0],
                    "nom_complet": data["prenom"] + " " + data["nom"],
                    "email": data["email"],
                    "nb_services": data["nb_services"],
                    "services": ", ".join(data["services"]),
                } for data in employe_data.values()
            ]
        })

    return prestation_par_prestataire


def dashmin(request):
    current_year = date.today().year

    prestations_par_reference = groupe_prestations_par_reference(year=current_year)
    context = {
        "semaines": semaines(),
        "page_title": "Analytics",
        "prestations_par_reference": prestations_par_reference,
    }
    return render(request, "dashboard.html", context)


def employe(request):
    form = EmployeForm()

    context = {
        "form": form,
        "page_title": "Employés",
    }
    return render(request, tmp_base + "add_employe.html", context)


@require_http_methods(["GET"])
def get_employes(request):
    employes = Employe.objects.all()
    list_employes: list = []
    for employe in employes:
        list_employes.append({
            "id": employe.id,
            "full_name": employe.first_name + " " + employe.last_name,
            "telephone": employe.telephone,
            "email": employe.email,
            "action": f'<a class="btn btn-danger btn-sm" href="#"><i class="bi bi-pencil"></i></a>'
        })

    return JsonResponse({"success": True, "data": list_employes})

def add_employe(request):
    if request.method == "POST":

        try:
            data = json.loads(request.body)
            #  Verification des champs cote serveur
            required_fields = ['first_name', 'last_name', 'telephone', 'email']
            for field in required_fields:
                if not escape(data.get(field)):
                    return JsonResponse({"error": f"{field} est obligatoire"}, status=400)

            # Enregistrement de l'employe
            employee = Employe.objects.create_user(
                first_name=data['first_name'], last_name=data['last_name'],
                email=data['email'], telephone=data['telephone']
            )


            return JsonResponse({ "msg": "Employé enregistré avec succès.",
                                  "first_name": employee.first_name,
                                  "last_name": employee.last_name,
                                  "telephone": employee.telephone,
                                  "email": employee.email})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Données invalides."}, status=400)
        except IntegrityError as e:
            if 'employe_employe_email_key' in str(e):
                return JsonResponse({"error": "Ce email existe déjà."}, status=409)
            return JsonResponse({"error": "Echec de l'enregistrement pour des raison de doublon"}, status=409)


def get_stats_vente_produits(annee: int, week_num: int, month_num: int):
    try:
        filtres = {"created_at__date__year": annee}

        if month_num > 0:
            # Filtre pour récupérer les data du mois
            filtres["created_at__date__month"] = month_num
        if week_num > 0:
            # Filtre pour récupérer les data de la semaine
            filtres["created_at__date__week"] = week_num

        ventes = Vente.objects.filter(**filtres)

        # Nombre de Ventes réalisé
        nb_ventes = ventes.count()
        sum_montant_ventes = ventes.aggregate(Sum("montant_total"))['montant_total__sum'] or 0
        sum_remise_ventes = ventes.aggregate(Sum("reduction"))['reduction__sum'] or 0

        total_net_ventes = sum_montant_ventes - sum_remise_ventes

        # Nombre de Ventes en Cash
        nb_ventes_cash = ventes.filter(type_vente=1).count()

        # Montant total de Ventes en Cash
        resultats_ventes_cash = ventes.aggregate(
            sum_vente_cash=Sum("montant_total", filter=Q(type_vente=1)),
            sum_remise_vente_cash=Sum("reduction", filter=Q(type_vente=1)),
        )
        sum_ventes_cash = resultats_ventes_cash['sum_vente_cash'] or 0
        sum_remise_ventes_cash = resultats_ventes_cash['sum_remise_vente_cash'] or 0

        total_ventes_cash = sum_ventes_cash - sum_remise_ventes_cash


        # Nombre de Ventes à Crédit
        nb_ventes_credits = ventes.filter(type_vente=2).count()

        # Montant total de Ventes à Crédit
        resultats_ventes_credits = ventes.aggregate(
            total_montant_credit=Sum("montant_total", filter=Q(type_vente=2)),
            total_remise_credit=Sum("reduction", filter=Q(type_vente=2))
        )
        sum_ventes_credit = resultats_ventes_credits["total_montant_credit"] or 0
        sum_remise_ventes_credit = resultats_ventes_credits["total_remise_credit"] or 0

        total_ventes_credits = sum_ventes_credit - sum_remise_ventes_credit

        response = {
            "nb_ventes": nb_ventes,
            "sum_montant_ventes": sum_montant_ventes,
            "sum_remise_ventes": sum_remise_ventes,
            "total_net_ventes": total_net_ventes,
            "nb_ventes_cash": nb_ventes_cash,
            "sum_ventes_cash": sum_ventes_cash,
            "sum_remise_ventes_cash": sum_remise_ventes_cash,
            "total_ventes_cash": total_ventes_cash,
            "nb_ventes_credits": nb_ventes_credits,
            "sum_ventes_credit": sum_ventes_credit,
            "sum_remise_ventes_credit": sum_remise_ventes_credit,
            "total_ventes_credits": total_ventes_credits,
        }
        return response
    except Vente.DoesNotExist:
        return None


def get_service_le_plus_demande(filtre):
    # le parametre 'filtre' est de type dictionnaire au format:
    # {"created_at__date__week": week_num}
    return (
        Prestation.objects.filter(**filtre)
        .values("service__id", "service__designation")
        .annotate(nb_services=Count("id"))
        .order_by("-nb_services")
        .first()
    )

def get_montant_total_par_service(id_service, filtres):
    return (
        Prestation.objects.filter(service__id=id_service, **filtres)
        .aggregate(total_montant=Sum("prix_service"))["total_montant"] or 0
    )


def get_stats_prestaions(year: int, week_num: int, month_num: int):
    try:
        filtres = {"created_at__date__year": year}

        service_de_la_semaine = {}
        service_de_du_mois = {}
        service_de_lannee = {}

        if week_num:
            filtres["created_at__date__week"] = week_num
            # Rechercher le Service le plus demandé de la Semaine
            service_semaine = get_service_le_plus_demande({"created_at__date__week": week_num})
            if service_semaine:
                # Récupérer le service le plus demandé de la semaine
                montant_total_service_semaine = get_montant_total_par_service(
                    service_semaine["service__id"],{"created_at__date__week": week_num}
                )
                service_de_la_semaine["designation"] = service_semaine["service__designation"]
                service_de_la_semaine["nb_demande"] = service_semaine["nb_services"] or 0
                service_de_la_semaine["montant_total_service_semaine"] = currency(montant_total_service_semaine)

        if month_num:
            filtres["created_at__date__month"] = month_num
            service_month = get_service_le_plus_demande({"created_at__date__month": month_num})
            if service_month:
                print("service_month :", service_month)
                montant_total_service_month = get_montant_total_par_service(service_month["service__id"], {"created_at__date__month": month_num})

                service_de_du_mois["designation"] = service_month["service__designation"]
                service_de_du_mois["nb_demande"] = service_month["nb_services"] or 0
                service_de_du_mois["montant_total_service_month"] = currency(montant_total_service_month) if montant_total_service_month else currency(0)

        # Récupérer le service le plus demandé de l'année
        service_year = get_service_le_plus_demande({"created_at__date__year": year})

        if service_year:
            # Récupérer le montant total du service le plus demandé de l'année
            montant_total_service_year = get_montant_total_par_service(
                service_year["service__id"],{"created_at__date__year": year}
            )
            service_de_lannee["designation"] = service_year["service__designation"]
            service_de_lannee["nb_demande"] = service_year["nb_services"] or 0
            service_de_lannee["montant_total_service_year"] = currency(montant_total_service_year) if montant_total_service_year else currency(0)


        prestations = InitPrestation.objects.filter(**filtres)

        # Montant total des Prestations
        resultats_montant_prestations = prestations.aggregate(
            sum_montant_prestations=Sum("montant_total"),
            sum_remises=Sum("remise"),
        )
        sum_montant_prestations = resultats_montant_prestations['sum_montant_prestations'] or 0
        sum_remises = resultats_montant_prestations['sum_remises'] or 0

        montant_net_prestations = sum_montant_prestations - sum_remises

        # Nombre de Prestations
        nb_prestations = prestations.count()

        data = {
            "montant_net_prestations": currency(montant_net_prestations) if montant_net_prestations else currency(0),
            "nb_prestations": nb_prestations if nb_prestations else 0,
            "service_semaine": service_de_la_semaine,
            "service_month": service_de_du_mois,
            "service_year": service_de_lannee,
        }

        return data

    except InitPrestation.DoesNotExist:
        return None

    except Exception as e:
        print("erreur inattendue in get_stats_prestaions :", str(e))
        return None



@require_http_methods(["POST"])
def filtre_dashmin_data(request):
    try:
        data = json.loads(request.body)

        year = int(data['year'])
        week_num = int(data['week_num'])
        month_num = int(data['month_num'])

        data = {
            "stats_vente_produits": get_stats_vente_produits(year, week_num, month_num),
            "get_stats_prestaions": get_stats_prestaions(year, week_num, month_num),
        }

        return JsonResponse({"success": True, "data": data}, status=http.HTTPStatus.OK)
    except json.JSONDecodeError:
        return JsonResponse({"error": True, "msg": "Format de données invalides"}, status=400)

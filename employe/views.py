import http
import json
from datetime import date, timedelta

import django.db.utils
from django.db import IntegrityError
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from employe.forms import EmployeForm
from employe.models import Employe
from salon.models import Vente, Depense

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


def dashmin(request):

    context = {
        "semaines": semaines(),
        "page_title": "Analytics"
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


def get_stats_vente_produits(annee: int, num_week: int):
    try:
        ventes = Vente.objects.filter(
            created_at__date__year=annee,
            created_at__date__week=num_week,
        )
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
        sum_remise_ventes_cash = resultats_ventes_cash['sum_remise_vente_cash']

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

@require_http_methods(["POST"])
def filtre_dashmin_data(request):
    try:
        data = json.loads(request.body)

        stats_vente_produits = get_stats_vente_produits(int(data['year']), int(data['week_num']))
        data = {
            "stats_vente_produits": stats_vente_produits,
        }
        return JsonResponse({"success": True, "data": data}, status=http.HTTPStatus.FOUND)
    except json.JSONDecodeError:
        return JsonResponse({"error": True, "msg": "Format de données invalides"}, status=400)

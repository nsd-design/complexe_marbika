import json
from datetime import date, timedelta

import django.db.utils
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from employe.forms import EmployeForm
from employe.models import Employe

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

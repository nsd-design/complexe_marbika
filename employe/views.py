import json

import django.db.utils
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape

from employe.forms import EmployeForm
from employe.models import Employe

tmp_base = "employe/"
def dashmin(request):

    context = {
        "page_title": "Analytics"
    }
    return render(request, "dashboard.html", context)


def employe(request):
    employes = Employe.objects.all()
    form = EmployeForm()
    context = {
        "employes": employes,
        "form": form,
        "page_title": "Employés",
    }
    return render(request, tmp_base + "add_employe.html", context)


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

import json

from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.html import escape

from salon.forms import ServiceForm, CategorieForm, PrixServiceForm
from salon.models import CategorieService, Service, PrixService

tmp = "salon/"

def services(request):
    categories = CategorieService.objects.all()
    services_list = Service.objects.all()
    context = {
        "service_form": ServiceForm(),
        "categorie_form": CategorieForm(),
        "categories": categories,
        "services": services_list,
        "page_title": "Services",
    }
    return render(request, tmp + "services.html", context)


def add_category(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            required_fields = ['category']
            for field in required_fields:
                if not escape(data.get(field)):
                    return JsonResponse({"error": f"{field} est obligatoire"}, status=400)

            category = CategorieService.objects.create(
                nom_categorie=data['category'],
            )
            category.save()

            return JsonResponse({"msg": "Categorie créée avec succès",
                                 "id_categorie": category.id,
                                 "nom_categorie": category.nom_categorie,
                                 })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Données invalides."}, status=400)


def add_service(request):
    if request.method == "POST":
        try:
            form = ServiceForm(request.POST)
            if form.is_valid():
                designation = form.cleaned_data['designation']
                categorie = form.cleaned_data['categorie']
                new_service = Service.objects.create(
                    designation=designation,
                    categorie=categorie
                )
                return JsonResponse({"msg": "Service créé avec succès",
                                     "uuid": new_service.id,
                                     "designation": new_service.designation,
                                     "categorie": new_service.categorie.nom_categorie
                                     }, status=201)
            else:
                return JsonResponse({"error": form.errors}, status=400)

        except IntegrityError:
            return JsonResponse({"error": "Erreur: Ce Service existe déjà"})

        except Exception as e:
            print(e)
            return JsonResponse({"error": "Une erreur inattendue s'est produite."}, status=500)

    return redirect("services")


def prix_services(request):
    prix_services_list = PrixService.objects.all()
    context = {
        "form": PrixServiceForm(),
        "page_title": "Prestations",
        "prix_services": prix_services_list,
    }

    return render(request, tmp + "prix_services.html", context)


def add_prix_service(request):
    if request.method == "POST":
        try:
            form = PrixServiceForm(request.POST)
            if form.is_valid():
                service = form.cleaned_data['service']
                prix = form.cleaned_data['prix_service']

                PrixService.objects.create(
                    prix_service=prix,
                    service=service
                )

                return JsonResponse({"msg": f"Prix {service} créé avec succès",
                                     "service": service.designation,
                                     "prix": prix
                                     }, status=200)
            else:
                return JsonResponse({"error": form.errors}, status=400)

        except Exception as e:
            return JsonResponse({"error": "Echec de la création du Prix, veillez réessayer"})

    else:
        return redirect("prix_services")


def prestations(request):

    context= {
        "form": "",
        "page_title": "Prestations",
    }

    return render(request, tmp + "prestations.html", context)

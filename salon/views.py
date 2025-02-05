import json

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.html import escape

from salon.forms import ServiceForm, CategorieForm
from salon.models import CategorieService

tmp = "salon/"

def services(request):
    categories = CategorieService.objects.all()
    context = {
        "service_form": ServiceForm(),
        "categorie_form": CategorieForm(),
        "categories": categories
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

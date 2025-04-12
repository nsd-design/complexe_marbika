import json

from django.db import IntegrityError
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from employe.models import Employe
from salon.forms import ServiceForm, CategorieForm, PrixServiceForm, PrestationForm, ProduitForm
from salon.models import CategorieService, Service, PrixService, Prestation, Produit

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
        "page_title": "Prix des Services",
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
    total_paye = 0

    prestations_list = Prestation.objects.annotate(
        montant_paye=F("montant_a_payer") - F("montant_reduit")
    ).order_by("-created_at")

    if prestations_list:
        total_paye = prestations_list.aggregate(total=Sum("montant_paye"))['total']
        total_paye = "{:,.0f} GNF".format(total_paye).replace(",", " ")

    context= {
        "form": PrestationForm(),
        "page_title": "Prestations",
        "prestation_list": prestations_list if prestations_list.exists else None,
        "total_paye": total_paye
    }
    return render(request, tmp + "prestations.html", context)

def get_prix_service(request, service_id):
    if request.method == 'GET':
        try:
            service = PrixService.objects.get(service_id=service_id)
            return JsonResponse({"prix_service": service.prix_service})
        except PrixService.DoesNotExist:
            return JsonResponse({"error": "Aucun prix actif pour ce service."}, status=404)

        except Exception as e:
            print("get_prix_service:", e)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


def add_prestation(request):
    if request.method == "POST":
        try:
            form = PrestationForm(request.POST)
            if form.is_valid():
                service = form.cleaned_data['service']
                fait_par = form.cleaned_data['fait_par']
                montant_a_payer = form.cleaned_data['montant_a_payer']
                montant_reduit = form.cleaned_data['montant_reduit']

                new_prestation = Prestation.objects.create(
                    service=service,
                    montant_a_payer=montant_a_payer,
                    montant_reduit=montant_reduit,
                    fait_par=fait_par
                )
                pres = {
                    "service": new_prestation.service.designation,
                    "prestateur": new_prestation.fait_par.email,
                    "montant": new_prestation.montant_a_payer,
                    "reduction": new_prestation.montant_reduit,
                    "net_paye": new_prestation.montant_a_payer - new_prestation.montant_reduit
                }

                return JsonResponse({"msg": "Prestation enregistrée", "prestation": pres})

        except Exception as e:
            print("add prestation", e)
    else:
        JsonResponse({"error": "Methode non autorisée"}, status=405)

def produits(request):
    form = ProduitForm()
    context = {
        "form": form,
        "page_title": "Produits",
    }
    return render(request, tmp + "produits.html", context)


@require_http_methods(["POST"])
def add_produit(request):
    try:
        form_submitted = ProduitForm(request.POST)
        if form_submitted.is_valid():
            designation = form_submitted.cleaned_data['designation']
            prix_achat = form_submitted.cleaned_data['prix_achat']
            prix_vente = form_submitted.cleaned_data['prix_vente']

            if prix_achat <= 0:
                return JsonResponse({"error": True, "msg": "Le prix d'achat doit être superieur à 0"}, status=400)
            if prix_vente <= 0:
                return JsonResponse({"error": True, "msg": "Le prix de vente doit être superieur à 0"}, status=400)

            Produit.objects.create(
                designation=designation, prix_achat=prix_achat, prix_vente=prix_vente
            )

            return JsonResponse({"success": True, "msg": "Produti céé avec succès !"}, status=201)
        else:
            return JsonResponse({"error": True, "msg": str(form_submitted.errors)}, status=400)
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Une erreur s'est produite"}, status=400)

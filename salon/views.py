import json

from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from client.models import Client
from employe.models import Employe
from salon.forms import ServiceForm, CategorieForm, PrixServiceForm, PrestationForm, ProduitForm, ApproProduitForm
from salon.models import CategorieService, Service, PrixService, Prestation, Produit, Approvisionnement, Vente, \
    ProduitVendu

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
        "appro_form": ApproProduitForm(),
        "page_title": "Produits",
    }
    return render(request, tmp + "produits.html", context)


@require_http_methods(["POST"])
def add_produit(request):
    try:
        form_submitted = ProduitForm(request.POST, request.FILES)
        if form_submitted.is_valid():
            designation = form_submitted.cleaned_data['designation']
            prix_achat = form_submitted.cleaned_data['prix_achat']
            prix_vente = form_submitted.cleaned_data['prix_vente']
            image = form_submitted.cleaned_data['image']
            stock_init = form_submitted.cleaned_data['stock']

            if prix_achat <= 0:
                return JsonResponse({"error": True, "msg": "Le prix d'achat doit être superieur à 0"}, status=400)
            if prix_vente <= 0:
                return JsonResponse({"error": True, "msg": "Le prix de vente doit être superieur à 0"}, status=400)

            new_product = Produit.objects.create(
                designation=designation, prix_achat=prix_achat, prix_vente=prix_vente, stock=stock_init, image=image
            )
            new_product.approvisionner_produit(quantite=stock_init, prix_achat_u=prix_achat, description="Stock initial")

            return JsonResponse({"success": True, "msg": "Produti céé avec succès !"}, status=201)
        else:
            return JsonResponse({"error": True, "msg": str(form_submitted.errors)}, status=400)
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Une erreur s'est produite"}, status=400)


@require_http_methods(["GET"])
def get_produits(request):
    list_produits: list = []
    list_appro: list = []
    try:
        produits = Produit.objects.all()

        approvisionnements = Approvisionnement.objects.all()

        if produits is None:
            return JsonResponse({"succes": True, "msg": "Aucun produit n'a été trouvé"})

        for produit in produits:
            pau = float(produit.prix_achat)
            pvu = float(produit.prix_vente)
            list_produits.append({
                "id": produit.id,
                "designation": produit.designation,
                "prix_achat": "{:,.0f} GNF".format(pau).replace(",", " "),
                "prix_vente": "{:,.0f} GNF".format(pvu).replace(",", " "),
                "stock": f'<span class="badge border border-success text-success">{produit.stock}</span>' if int(produit.stock) > 0 else f'<span class="badge rounded-pill bg-secondary">{produit.stock}</span>',
            })

        for appro in approvisionnements:
            list_appro.append({
                "id_appro": appro.id,
                "produit": appro.produit.designation,
                "pau": appro.pau,
                "quantite": appro.quantite,
                "stock": appro.produit.stock,
                "date_appro": appro.created_at.strftime("%d/%m/%Y"),
            })

        data = {"list_produits": list_produits, "list_appro": list_appro}
        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": str(e)})


@require_http_methods(["POST"])
def approvisionner_produit(request):
    try:
        appro_form_submitted = ApproProduitForm(request.POST)
        if appro_form_submitted.is_valid():
            produit = appro_form_submitted.cleaned_data['produit']
            quantite = appro_form_submitted.cleaned_data['quantite']
            pau = appro_form_submitted.cleaned_data['pau']

            produit_a_approvisionner = Produit.objects.get(id=produit.id)
            # Approvisionnement du Produit
            produit_a_approvisionner.approvisionner_produit(int(quantite), pau)

            return JsonResponse({"success": True, "msg": "Approvisionnement effectué !"}, status=200)

        else:
            return JsonResponse({"error": True, "msg": "Données invalides"}, status=400)
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Echec, une erreur s'est produite"}, status=400)


# Affiche le template où la vente des produits doit être fait
@require_http_methods(["GET"])
def shop_produits(request):
    liste_produits = Produit.objects.all()
    context = {
        "liste_produits": liste_produits,
        "page_title": "Vente Produits",
    }
    return render(request, tmp + "vente_produits.html", context)


@require_http_methods(["POST"])
def vente_produits(request):
    try:
        data = json.loads(request.body)

        products_ordered = data.get("produits", [])
        reduction = escape(data.get("reduction", 0))
        type_vente = escape(data.get("typeVente"))
        id_client = escape(data.get("id_client"))
        print("product ordered :", products_ordered)
        if not type_vente:
            return JsonResponse({"error": True, "msg": "Specifier le Type de Vente"}, status=400)

        with transaction.atomic():
            vente_produit_created = False # Flag pour savoir s'il y a eu erreur pendant l'execution de ce block

            # Check if Client exists
            current_client = Client.objects.get(id=id_client) if id_client else None
            # Init New Vente
            current_order = Vente.objects.create(reduction=reduction,
                                                 type_vente=type_vente, montant_total=0,
                                                 client=current_client
                                                 )
            current_order.reference = f"VP-{current_order.id.hex[:8].upper()}"
            current_order.save()
            montant_total = 0

            for prod in products_ordered:
                id_produit = escape(prod.get("designation"))
                quantite = escape(prod.get("quantite"))
                pvu = escape(prod.get('prix'))
                produit = Produit.objects.get(id=id_produit)
                # Verifier si la quantite de Produits commandée est disponible
                # Sinon, une exception est levée dans la method 'controle_stock_produit'
                produit.controle_stock_produit(int(quantite))

                # Enregistré le Produit vendu et l'assigner à la Vente Initialisée
                ProduitVendu.objects.create(
                    vente=current_order, produit=produit,
                    quantite=quantite, prix_vente_unitaire=pvu
                )
                # Mise à jour du STOCK
                produit.update_stock(quantite)

                montant_total += int(pvu) * int(quantite)

                vente_produit_created = True # True, pour dire le Produit a bien été vendu, sinon il reste sur Fasle
                # Et toutes les operations dans ce block sont annulées
        # Mise à jour du prix total de la
        current_order.montant_total = montant_total - int(reduction)
        current_order.save()
        if not vente_produit_created:
            raise ValueError("Impossible d'effectuer la Vente une erreur s'est produite.")

        return JsonResponse({"success": True, "msg": "Vente effectuée avec succès"}, status=200)

    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": str(e)}, status=400)


@require_http_methods(["GET"])
def get_clients(request):
    list_clients: list = []

    try:
        clients = Client.objects.all()
        for client in clients:
            list_clients.append({
                "id": client.id,
                "nom_complet":client.nom_complet,
                "telephone": client.telephone
            })
        return JsonResponse({"success": True, "data": list_clients})
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": str(e)})

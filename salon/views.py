import json
from datetime import datetime

from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from client.models import Client
from employe.models import Employe
from salon.forms import ServiceForm, CategorieForm, PrixServiceForm, ProduitForm, ApproProduitForm, PrestationForm
from salon.models import CategorieService, Service, PrixService, Produit, Approvisionnement, Vente, \
    ProduitVendu, Prestation, InitPrestation

tmp = "salon/"

def services(request):
    categories = CategorieService.objects.all()
    services_list = Service.objects.all()
    context = {
        "service_form": ServiceForm(),
        "categorie_form": CategorieForm(),
        "page_title": "Services",
    }
    return render(request, tmp + "services.html", context)


@require_http_methods(["GET"])
def get_services(request):
    try:
        list_services: list = []
        services_l = Service.objects.all()

        for service in services_l:
            prix = float(service.prix_service) if service.prix_service else 0.0
            list_services.append({
                "id": service.id,
                "designation": service.designation,
                "categorie": service.categorie.nom_categorie,
                "prix_service": "{:,.0f} GNF".format(prix).replace(",", " "),
                "actions": f'<i class="bi bi-pencil btn btn-primary update-service" id="{service.id}"></i>'
            })
        return JsonResponse({"success": True, "data": list_services}, status=200)
    except Service.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Aucun service trouvé."}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Erreur inattendue"}, status=400)


@require_http_methods(["GET"])
def get_service(request):
    id_service = request.GET.get('id')
    if not id_service:
        return JsonResponse({"error": True, "msg": "Aucun Service n'a été fourni pour l'update."}, status=400)

    try:
        service = Service.objects.get(id=id_service)
        data = {
            "id": service.id,
            "designation": service.designation,
            "categorie": service.categorie.nom_categorie,
            "id_category": service.categorie.id,
            "prix_service": service.prix_service
        }
        return JsonResponse({"success":True, "data": data}, status=200)

    except Service.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Service introuvable"})
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": str(e)})


@require_http_methods(["POST"])
def update_service(request):
    data = json.loads(request.body)
    id_service = escape(data['idService'])
    designation = escape(data['designation'])
    id_category = escape(data['categorie'])
    prix = escape(data['prix_service'])

    try:
        service = Service.objects.get(id=id_service)
        category = CategorieService.objects.get(id=id_category)

        service.designation = designation
        service.categorie = category
        service.prix_service = prix
        service.updated_at = datetime.now()

        service.save()

        return JsonResponse({"success": True, "msg": "Modification effectuée avec succès !"})

    except Service.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Erreur, ce Service n'existe pas"})
    except CategorieService.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Erreur, cette Categorie n'existe pas"})

    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Une erreur s'est produite."})



def add_category(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            required_fields = ['category']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({"error": f"{field} est obligatoire"}, status=400)

            category = CategorieService.objects.create(
                nom_categorie=escape(data['category']),
            )
            category.save()

            return JsonResponse({"msg": "Categorie créée avec succès",
                                 "id_categorie": category.id,
                                 "nom_categorie": category.nom_categorie,
                                 })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Données invalides."}, status=400)


@require_http_methods(["GET"])
def get_categories(request):
    try:
        list_categories: list = []

        categories = CategorieService.objects.all()
        for category in categories:
            list_categories.append({
                "id": category.id,
                "category": category.nom_categorie,
                "action": f'<a class="btn btn-danger btn-sm" href="{category.id}"><i class="bi bi-pencil"></i></a>'
            })

        return JsonResponse({"success": True, "data": list_categories}, status=200)

    except CategorieService.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Aucune Catégorie trouvée"}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Erreur inattendue"})


def add_service(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            required_fields = ['designation', 'category', 'prix_service']
            for field in required_fields:
                if not escape(data.get(field)):
                    return JsonResponse({"error": f"{field} est obligatoire"}, status=400)

            designation = escape(data['designation'])
            id_categorie = escape(data['categorie'])
            prix_service = escape(data['prix_service'])

            category = CategorieService.objects.get(id=id_categorie)
            Service.objects.create(
                designation=designation,
                categorie=category,
                prix_service=prix_service,
            )
            return JsonResponse({"success": True, "msg": "Service créé avec succès",}, status=201)
        except IntegrityError:
            return JsonResponse({"error": "Erreur: Ce Service existe déjà"})

        except Exception as e:
            print(e)
            return JsonResponse({"error": True, "msg": "Une erreur inattendue s'est produite."}, status=500)
    else:
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

    qs_services = Service.objects.all()
    prestataires = Employe.objects.all()

    context= {
        "form": PrestationForm(),
        "services":  qs_services if qs_services else [],
        "prestataires": prestataires if prestataires.exists else [],
        "page_title": "Prestations",
    }
    return render(request, tmp + "prestations.html", context)


@require_http_methods(["GET"])
def get_prestations(request):
    try:
        list_init_prestations = InitPrestation.objects.all()
        data: list = []
        for prestation in list_init_prestations:
            remise = float(prestation.remise)
            montant_total = float(prestation.montant_total)
            net_paye = float(prestation.montant_total) - float(prestation.remise)
            data.append({
                "reference": prestation.reference,
                "total": "{:,.0f} GNF".format(montant_total).replace(",", " "),
                "remise": "{:,.0f} GNF".format(remise).replace(",", " "),
                "client": f'<p>{prestation.client.nom_complet}<br><span class="badge border border-info text-body">{prestation.client.telephone}</span></p>' if prestation.client else "",
                "net_paye": "{:,.0f} GNF".format(net_paye).replace(",", " "),
                "actions": f'<a href="#" class="text-danger details"><i class="bi bi-box-arrow-up-right fs-5"></i></a>',
            })

        return JsonResponse({"success": True, "data": data})
    except InitPrestation.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Aucune données disponible."})




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


@require_http_methods(["POST"])
def add_prestation(request):
    try:
        data = json.loads(request.body)

        prestations_faites = data.get("prestations", [])
        remise = escape(data.get("remise", 0))
        id_client = escape(data.get("client"))

        with transaction.atomic():
            prestation_saved = False # Flag pour savoir si chacune des prestations a été enregistré sans interruption

            # Check if Client exists
            current_client = Client.objects.get(id=id_client) if id_client else None

            # Init New Prestation
            init_prestation = InitPrestation(montant_total=0, remise=remise, client=current_client)
            init_prestation.reference = f"PS-{init_prestation.id.hex[:8].upper()}"
            init_prestation.save()

            montant_total = 0

            for prestation in prestations_faites:

                id_service = escape(prestation.get("idService"))
                prix_service = escape(prestation.get("prixService"))
                id_prestataire = escape(prestation.get('prestataire'))
                current_service = Service.objects.get(id=id_service)

                prestataire = Employe.objects.get(id=id_prestataire)

                # Enregistré la Prestation
                Prestation.objects.create(service=current_service, prix_service=prix_service, init_prestation=init_prestation,
                                          fait_par=prestataire
                                          )

                montant_total += int(prix_service)

                prestation_saved = True # True, pour dire la Prestation a bien été enregistré, sinon il reste sur False
                # Et toutes les operations dans ce block sont annulées

        # Mise à jour du prix total de la Prestation
        init_prestation.montant_total = montant_total
        init_prestation.save()
        if not prestation_saved:
            return JsonResponse({"error": True, "msg": "Impossible de valider la Prestation, une erreur s'est produite."})

        return JsonResponse({"success": True, "msg": "Prestation enregistrée avec succès"}, status=200)

    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": str(e)}, status=400)


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
                designation=designation, prix_achat=prix_achat, prix_vente=prix_vente, image=image
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
                "description": appro.description,
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
            description = appro_form_submitted.cleaned_data['description']

            produit_a_approvisionner = Produit.objects.get(id=produit.id)
            # Approvisionnement du Produit
            produit_a_approvisionner.approvisionner_produit(int(quantite), pau, description=description)

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
        current_order.montant_total = montant_total
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


# reference, date, montant, remise, montant paye, actions
@require_http_methods(["GET"])
def get_ventes(request):
    try:
        list_ventes: list = []
        ventes = Vente.objects.all().order_by("-created_at")

        for vente in ventes:
            montant_total = float(vente.montant_total)
            montant_paye = float(vente.montant_total - vente.reduction)
            list_ventes.append({
                "id": vente.id,
                "reference": vente.reference,
                "client": vente.client.nom_complet if vente.client else "Anonyme",
                "date": vente.created_at.strftime("%d/%m/%Y %H:%M"),
                "montant_total": "{:,.0f} GNF".format(montant_total).replace(",", " "),
                "reduction": "{:,.0f} GNF".format(float(vente.reduction)).replace(",", " "),
                "montant_paye": "{:,.0f} GNF".format(montant_paye).replace(",", " "),
                "type_vente": f'<span class="badge rounded-pill bg-success">{vente.get_type_vente_display()}</span>' if int(vente.type_vente) == 1 else f'<span class="badge rounded-pill bg-secondary">{vente.get_type_vente_display()}</span>',
                'actions': f'<a href="/salon/produits/shop/{vente.id}" class="text-danger details"><i class="bi bi-box-arrow-up-right fs-5"></i></a>',
            })
        print("Ventes :", list_ventes)
        return JsonResponse({"success": True, "data": list_ventes})
    except Exception as e:
        print(e)
import http
import json
from datetime import datetime, timedelta
from http import HTTPStatus

from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from client.models import Client
from employe.models import Employe
from salon.forms import ServiceForm, CategorieForm, PrixServiceForm, ProduitForm, ApproProduitForm, PrestationForm, \
    DepensesForm
from salon.models import CategorieService, Service, PrixService, Produit, Approvisionnement, Vente, \
    ProduitVendu, Prestation, InitPrestation, Depense

tmp = "salon/"

def currency(value):
    # print("value :", value)
    try:
        float(value)
        return "{:,.0f} GNF".format(value).replace(",", " ")
    except (ValueError, TypeError):
        return value

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
                "actions": f'''
                            <a href="/salon/prestations/details/{prestation.id}" class="text-info me-2 showDetails"><i class="bi bi-eye fs-5"></i></i></a>
                            <a href="/salon/prestations/details/{prestation.id}" class="text-danger showTicket"><i class="bi bi-box-arrow-up-right fs-5"></i></a>
                            ''',
            })

        return JsonResponse({"success": True, "data": data})
    except InitPrestation.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Aucune données disponible."})


# Get Services inclus dans une Prestation
@require_http_methods(["GET"])
def get_prestation_details(request, id_prestation):
    try:
        prestation = InitPrestation.objects.get(id=id_prestation)
        prestation_services = Prestation.objects.filter(init_prestation=prestation)

        list_service: list = []
        for service in prestation_services:
            list_prestataires = [presta for presta in service.fait_par.all().values("first_name", "last_name", "email")]
            list_service.append({
                "designation": service.service.designation,
                "quantite": service.quantite,
                "prix": service.service.prix_service,
                "prestataires": list_prestataires,
            })

        data = {
            "reference": prestation.reference,
            "nom_client": prestation.client.nom_complet if prestation.client else "",
            "tel_client": prestation.client.telephone if prestation.client else "",
            "date": prestation.created_at.strftime("%d/%m/%Y %H:%M"),
            "total": prestation.montant_total,
            "remise": prestation.remise,
            "net_paye": prestation.montant_total - prestation.remise,
            "services": list_service,
        }

        return JsonResponse({"success": True, "data": data}, status=200)

    except Prestation.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Cette Prestation ne contient aucun Service"}, status=404)

    except InitPrestation.DoesNotExist:
        return JsonResponse({"error": True, "msg": "Aucune donnée pour cette prestation"}, status=404)
    except Exception as e:
        print("Erreur inattendue", str(e))
        return JsonResponse({"error": True, "msg": "Erreur inattendue"}, status=400)


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
                quantite = escape(prestation.get("quantite"))
                prestataires_ids = prestation.get('prestataire', [])

                if not prestataires_ids:
                    raise ValueError("Veuillez sélectionner les Prestataires")

                current_service = Service.objects.get(id=id_service)

                prestataires = Employe.objects.filter(id__in=prestataires_ids)

                # Enregistré la Prestation
                new_prestation = Prestation.objects.create(
                    service=current_service, prix_service=prix_service,
                    init_prestation=init_prestation, quantite=quantite,
                )
                new_prestation.fait_par.set(prestataires)

                montant_total += int(prix_service) * int(quantite)

                prestation_saved = True # True, pour dire la Prestation a bien été enregistré, sinon il reste sur False
                # Et toutes les operations dans ce block sont annulées
            if montant_total <= 0:
                raise Exception("Le montant est incorrect.")
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
            new_product.approvisionner_produit(quantite=stock_init, prix_achat_u=prix_achat, description="Stock initial - 1er approvisionnement")

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


@require_http_methods(["GET"])
def depenses(request):
    context = {
        "form": DepensesForm(),
        "page_title": "Dépenses",
    }
    return render(request, tmp + "depenses.html", context)


@require_http_methods(["GET"])
def get_depenses(request):
    try:
        depenses_resto = Depense.objects.filter(section="RESTAURANT")
        depenses_salon = Depense.objects.filter(section="SALON")

        list_depenses_resto: list = []
        list_depenses_salon: list = []

        for depense in depenses_resto:
            montant = float(depense.montant)
            list_depenses_resto.append({
                "motif": depense.motif,
                "montant": f'<span class="text-danger">' +"-{:,.0f} GNF".format(montant).replace(",", " ") + '</span>',
                "date": depense.created_at.strftime("%d/%m/%Y %H:%M"),
            })

        for depense in depenses_salon:
            montant = float(depense.montant)
            list_depenses_salon.append({
                "motif": depense.motif,
                "montant": f'<span class="text-danger">' +"-{:,.0f} GNF".format(montant).replace(",", " ") + '</span>',
                "date": depense.created_at.strftime("%d/%m/%Y %H:%M"),
            })

        data = {
            "resto": list_depenses_resto,
            "salon": list_depenses_salon,
        }
        return JsonResponse({"success": True, "data": data})
    except Depense.DoesNotExist:
        return JsonResponse({"error": "Aucune dépense trouvée"})


@require_http_methods(["POST"])
def creer_depense(request):
    try:
        depense_form_submited = DepensesForm(request.POST)
        if depense_form_submited.is_valid():
            montant = depense_form_submited.cleaned_data["montant"]
            motif = depense_form_submited.cleaned_data["motif"]
            section = depense_form_submited.cleaned_data["section"]
            Depense.objects.create(
                motif=motif, montant=montant, section=section
            )
            return JsonResponse({"success": True, "msg": "Dépense enregistrée avec succès."}, status=http.HTTPStatus.CREATED)
        else:
            return JsonResponse({"error": True, "msg": "Données soumises sont invalides, veuillez réessayer."}, status=400)
    except Exception as e:
        return JsonResponse({"error": True, "msg": str(e)})


# Cetter fonciton permet de recuperer les Depenses par periode et par Section selon les parametres fournis
# Ces periodes sont : Semaine en cours, Semaine precedente, Mois en cours et Annee en cours
# Il y a deux sections : Salon et Restaurant
def get_expenses_by_date_and_section(filtres):
    # Depense.objects.filter(
    #     created_at__date__gte=start_of_week,
    #     created_at__date__lte=today
    # ).aggregate(Sum("montant"))["montant__sum"] or 0
    return (
        Depense.objects.filter(**filtres)
        .aggregate(Sum("montant"))["montant__sum"] or 0
    )


@require_http_methods(["GET"])
def depense_semaine_mois_annee(request):
    try:
        # Date du jour
        today = timezone.now().date()

        # Debut de la semaine en cours
        start_of_week = today - timedelta(days=today.weekday())
        current_week_number = today.isocalendar().week

        # Debut de la semaine passee
        start_of_last_week = start_of_week - timedelta(days=7)
        end_of_last_week = start_of_week - timedelta(days=1)
        last_week_number = start_of_last_week.isocalendar().week


        # Debut du mois
        start_of_month = today.replace(day=1)

        # Debut de l'annee
        start_of_year = today.replace(month=1, day=1)

        # Debut de calcul des montants
        # Montant total des depenses de la semaine en cours
        # montant_total_service_semaine = get_montant_total_par_service(
        #     service_semaine["service__id"], {"created_at__date__week": week_num}
        # )
        total_semaine_en_cours_salon = get_expenses_by_date_and_section(
            {
                "section": "SALON",
                "created_at__date__gte": start_of_week,
                "created_at__date__lte": today
            }
        )
        total_semaine_en_cours_resto = get_expenses_by_date_and_section(
            {
                "section": "RESTAURANT",
                "created_at__date__gte": start_of_week,
                "created_at__date__lte": today
            }
        )
        # total_semaine_en_cours = Depense.objects.filter(
        #     created_at__date__gte=start_of_week,
        #     created_at__date__lte=today
        # ).aggregate(Sum("montant"))["montant__sum"] or 0

        # Montant total des depenses de la semaine passée
        total_semaine_passe_salon = get_expenses_by_date_and_section(
            {
                "section": "SALON",
                "created_at__date__gte": start_of_last_week,
                "created_at__date__lte": end_of_last_week,
            }
        )
        total_semaine_passe_resto = get_expenses_by_date_and_section(
            {
                "section": "RESTAURANT",
                "created_at__date__gte": start_of_last_week,
                "created_at__date__lte": end_of_last_week,
            }
        )

        # Montant total des depenses du Mois en Cours
        total_mois_en_cours_salon = get_expenses_by_date_and_section(
            {
                "section": "SALON",
                "created_at__date__gte": start_of_month
            }
        )
        total_mois_en_cours_resto = get_expenses_by_date_and_section(
            {
                "section": "RESTAURANT",
                "created_at__date__gte": start_of_month
            }
        )

        total_annee_en_cours_salon = get_expenses_by_date_and_section(
            {
                "section": "SALON",
                "created_at__date__gte": start_of_year
            }
        )
        total_annee_en_cours_resto = get_expenses_by_date_and_section(
            {
                "section": "RESTAURANT",
                "created_at__date__gte": start_of_year
            }
        )

        data = {
            "salon": {
                "total_semaine_en_cours": currency(total_semaine_en_cours_salon),
                "total_semaine_passe": currency(total_semaine_passe_salon),
                "total_mois_en_cours": currency(total_mois_en_cours_salon),
                "total_annee_en_cours": currency(total_annee_en_cours_salon),
            },
            "restaurant": {
                "total_semaine_en_cours": currency(total_semaine_en_cours_resto),
                "total_semaine_passe": currency(total_semaine_passe_resto),
                "total_mois_en_cours": currency(total_mois_en_cours_resto),
                "total_annee_en_cours": currency(total_annee_en_cours_resto),
            },
            "numero_semaine_en_cours": current_week_number,
            "numero_semaine_passe": last_week_number,
            "nom_du_mois": today.strftime("%B"),
            "annee_en_cours": today.strftime("%Y"),
        }

        return JsonResponse({"success": True, "data": data}, status=HTTPStatus.OK)
    except Exception as e:
        print(e)
        return JsonResponse({"error": True, "msg": "Erreur inattendue"})
    except (ValueError, TypeError):
        return JsonResponse({"error": True, "msg": "Erreur lors de la mise en forme du montant"})

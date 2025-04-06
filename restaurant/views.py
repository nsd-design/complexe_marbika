import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.html import escape
from datetime import datetime
from django.views.decorators.http import require_http_methods

from restaurant.forms import PlatForm, BoissonForm, ApprovisionnementBoissonForm
from restaurant.models import Plat, Boisson, Commande, CommandePlat, CommandeBoisson, ControleBoisson, \
    DetailsControleBoissons

tmp = "restaurant/"
def plats_boissons(request):

    context = {
        "form": PlatForm(),
        "from_boisson": BoissonForm(),
        "form_appro": ApprovisionnementBoissonForm(),
        "page_title": "Plats & Boissons"
    }
    return render(request, tmp + "plats_boissons.html", context)


def create_plat(request):
    if request.method == "POST":
        form = PlatForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                nom_plat = form.cleaned_data['nom_plat']
                prix = form.cleaned_data['prix']
                image = form.cleaned_data['photo_plat']

                Plat.objects.create(
                    nom_plat=nom_plat, prix=prix, photo_plat=image
                )

                return JsonResponse({"msg": "Platajouté avec succès !"}, status=200)
            else:
                return JsonResponse({"msg": "Erreur de validation"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)


def create_boisson(request):
    if request.method == "POST":
        form = BoissonForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                designation = form.cleaned_data['designation']
                prix = form.cleaned_data['prix_achat']
                image = form.cleaned_data['photo_boisson']

                Boisson.objects.create(
                    designation=designation, prix_achat=prix,
                    photo_boisson=image
                )

                return JsonResponse({"msg": "Boisson créée avec succès !"}, status=200)

        except Exception as e:
            print(e)
            return JsonResponse({"error": "Erreur de validation"}, status=400)
    else:
        return JsonResponse({"error": "Methode non autorisée"}, status=405)


def approvisionner_boisson(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            required_fields = ['boisson', 'quantite', 'prix_achat_unit']

            for field in required_fields:
                if not escape(data.get(field)):
                    return JsonResponse({"error": f"{field} est obligatoire"}, status=400)

            boisson = Boisson.objects.get(id=data['boisson'])
            quantite = int(data['quantite'])
            prix_achat = int(data['prix_achat_unit'])

            boisson.approvisionner(quantite, prix_achat)

            return JsonResponse({
                "msg": f"{quantite} unités ajoutées à {boisson.designation}",
                "stock": boisson.stock,
                "nouveau_prix_achat": boisson.prix_achat
            }, status=200)
        except Boisson.DoesNotExist:
            return JsonResponse({"error": "Boisson non trouvée"}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status1=405)
        except Exception as e:
            print(e)
            return  JsonResponse({"error": "Erreur de validation"})
    else:
        return JsonResponse({"error": "Methode non autorisée"}, status=405)


def commande(request):
    liste_plats = Plat.objects.all()
    liste_boissons = Boisson.objects.all()

    context = {
        "plats": liste_plats,
        "boissons": liste_boissons,
        "page_title": "Menu Restaurant"
    }
    return render(request, tmp + "commandes.html", context)


@require_http_methods(["GET"])
def get_commandes(request):
    if request.method == "GET":
        commandes = Commande.objects.all().order_by("-created_at")

        # Formater les Donnees pour DataTable
        data = []

        for commande in commandes:
            data.append({
                'id': commande.id,
                'reference': commande.reference,
                'date': commande.created_at.strftime("%d/%m/%Y %H:%M"),
                'montant': commande.prix_total,
                'reduction': commande.reduction,
                'montant_a_payer': commande.prix_total - commande.reduction,
                # Boutons d'action avec HTML (vous pouvez personnaliser)
                'actions': f'<a href="/restaurant/commandes/details/{commande.id}" class="text-danger details"><i class="bi bi-box-arrow-up-right fs-5"></i></a>'
            })

        response = {
            'data': data
        }
        return JsonResponse(response)


def passer_commande(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            plats_boissons = data.get("plat_boissons", [])
            reduction = data.get("reduction", 0)

            current_commande = Commande.objects.create(prix_total=0, reduction=reduction)
            current_commande.reference = f"CMD-{current_commande.id.hex[:8].upper()}"
            current_commande.save()
            print("reference:", current_commande.reference)
            prix_total = 0

            # Verifier si la quantite de la Boisson commandée est disponible
            for item in plats_boissons:
                if item['type'] == 'boisson':
                    boisson = Boisson.objects.get(id=item["designation"])
                    boisson.controle_stock(item['quantite'])

            for item in plats_boissons:
                if item['type'] == 'plat':
                    plat = Plat.objects.get(id=item["designation"])
                    CommandePlat.objects.create(
                        commande=current_commande,
                        plat=plat,
                        quantite=item['quantite'],
                        prix=item['prix']
                    )
                    prix_total += item['quantite'] * item['prix']
                elif item['type'] == 'boisson':
                    boisson = Boisson.objects.get(id=item["designation"])
                    CommandeBoisson.objects.create(
                        commande=current_commande,
                        boisson=boisson,
                        quantite=item['quantite'],
                        prix=item['prix']
                    )
                    boisson.vente_boissons(item['quantite'])
                    prix_total += item['quantite'] * item['prix']


            # Mise a jour du prix total de la Commande
            current_commande.prix_total = prix_total - int(reduction)
            current_commande.save()
            return JsonResponse({"success": True, "msg": "Commande recu"})
        except Exception as e:
            print(e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False, "error": "Méthode non autorisée"}, status=405)


@require_http_methods(["GET"])
def details_commande(request, id_commande):
    try:
        commande = Commande.objects.get(id=id_commande)
        plats = CommandePlat.objects.filter(commande=commande)
        boissons = CommandeBoisson.objects.filter(commande=commande)

        data = {
            "reference": commande.reference,
            "montant": commande.prix_total,
            "reduction": commande.reduction,
            "plats": [],
            "boissons": [],
        }

        for item in plats:
            data["plats"].append({
                "id": item.plat.id,
                "nom": item.plat.nom_plat,
                "quantite": item.quantite,
                "prix": item.prix
            })

        for item in boissons:
            data["boissons"].append({
                "id": item.boisson.id,
                "nom": item.boisson.designation,
                "quantite": item.quantite,
                "prix": item.prix
            })

        return JsonResponse(data, safe=False)
    except Exception as e:
        print('Exception:', str(e))


    return JsonResponse({"success": True})


@require_http_methods(["GET"])
def controle_boissons(request):
    boissons = Boisson.objects.filter(stock__gt=0)
    data = []
    for boisson in boissons:
        data.append({
            "designation": f'{boisson.designation}<br><input type="text" class="id_boisson" value="{boisson.id}" hidden>',
            "stock": boisson.stock,
            "stock_val": f'<div class="col-12  col-md-6 col-xl-6"><input type="number" name="stock" class="form-control col-12 quantite" value="{boisson.stock}"></div>'
        })
    try:
        controle_ouvert = ControleBoisson.objects.get(statut=1)

        details_controle = DetailsControleBoissons.objects.filter(controle=controle_ouvert)

        if details_controle is None:
            return JsonResponse({"ouvert": False, "data": data}, status=404)

        # Si un controle ouvert ayant des elements a ete trouvé, renvoyé ses informations
        details_controle_list = []
        for detail in details_controle:
            details_controle_list.append({
                "boisson": detail.boisson.id,
                "quantite_init": f'<span class="id_boisson" hidden="hidden">{detail.boisson.id}</span><span>{detail.boisson.designation}</span> \
                <span class="fw-bold text-white qteInit">{detail.quantite_init}</span>',
                "quantite_vendue": f'<input type="number" class="form-control qteVendue">',
                "quantite_restante": f'<input type="number" class="form-control qteRestante">',
                "manquant": f'<input type="number" class="form-control manquante">',
                "control_date": detail.controle.created_at.strftime("%d/%m/%Y %H:%M")
            })
        control_ouvert_trouve = {
            "id": controle_ouvert.id,
            "statut": controle_ouvert.statut,
            "created_at": controle_ouvert.created_at,
            "details": details_controle_list,
        }
        return JsonResponse({"ouvert": True, "data": control_ouvert_trouve})

    except ControleBoisson.DoesNotExist:
        return JsonResponse({"ouvert": False, "data": data}, status=404)
    except Exception as e:
        print("except:", e)
        return JsonResponse({"error": str(e)})


def create_controle_boissons(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            boissons = data.get("boissons", [])

            if not boissons:
                return JsonResponse({"success": False, "msg": "Aucune boisson sélectionnée pour le contrôle."},
                                    status=400)

            with transaction.atomic():
                # Ouvrir un Nouveau Control
                new_control = ControleBoisson.objects.create(statut=1)
                details_control_created = False
                for boisson in boissons:
                    id_boisson = escape(boisson.get("id"))
                    quantite = escape(boisson.get("quantite"))
                    # Renseigner les Boissons qui ont été controlée
                    try:
                        boisson_controle = Boisson.objects.get(id=id_boisson)
                        # if boisson_controle:
                        DetailsControleBoissons.objects.create(boisson=boisson_controle, quantite_init=quantite, controle=new_control)
                        details_control_created = True
                    except Exception as e:
                        print(e)
                        return JsonResponse({"success": False, "msg": str(e)})
            if not details_control_created:
                raise ValueError("Aucune boisson valide n'a été enregistrée")

            return JsonResponse({"success": True, "msg": "Nouveau contrôle initialié avec succès !"})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "msg": "Données JSON invalides."}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({"success": False, "msg": str(e)}, status=500)


@require_http_methods(["POST"])
def cloture_controle(request):
    try:
        data = json.loads(request.body)
        details_a_cloture = data.get("detail_cloture", [])

        if not details_a_cloture:
            return JsonResponse({"success": False, "msg": "Aucune boisson sélectionnée pour le contrôle"}, status=400)

        with transaction.atomic():
            control_id = escape(data.get("control_id"))

            try:
                controle_a_cloture = ControleBoisson.objects.get(id=control_id)
            except ControleBoisson.DoesNotExist:
                return JsonResponse({"success": False, "msg": "Données invalides"}, status=404)

            controle_cloture = False
            for detail in details_a_cloture:
                id_boisson = escape(detail.get("id_boisson"))
                qte_vendue = escape(detail.get("qteVendue"))
                qte_restante = escape(detail.get("qteRestante"))
                manquante = escape(detail.get("manquante"))

                try:
                    boisson_controlee = DetailsControleBoissons.objects.get(
                        boisson=id_boisson,
                        controle=controle_a_cloture
                    )
                    boisson_controlee.quantite_vendue = qte_vendue if qte_vendue else 0
                    boisson_controlee.quantite_restante = qte_restante if qte_restante else 0
                    boisson_controlee.manquant = manquante if manquante else 0
                    boisson_controlee.updated_at = datetime.now()
                    controle_cloture = True
                    boisson_controlee.save()
                except DetailsControleBoissons.DoesNotExist:
                    raise Exception(f"Détail pour boisson {id_boisson} introuvable")

            if not controle_cloture:
                raise Exception("Échec de la clôture du contrôle")

            # ✅ Mise à jour du contrôle (statut et date) une fois que tout s’est bien passé
            controle_a_cloture.statut = 2
            controle_a_cloture.updated_at = datetime.now()
            controle_a_cloture.save()

            return JsonResponse({"success": True, "msg": "Contrôle clôturé avec succès"})
    except Exception as e:
        print("Erreur:", e)
        return JsonResponse({"success": False, "msg": str(e)}, status=500)
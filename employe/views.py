import http
import json
import uuid
from collections import defaultdict
from datetime import date, timedelta, datetime

import django.db.utils
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.db import IntegrityError, transaction
from django.db.models import Sum, Q, Count, ExpressionWrapper, BigIntegerField, F
from django.db.models.functions import Extract, ExtractWeek
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from client.models import Piscine
from employe.forms import EmployeForm
from employe.models import Employe
from restaurant.models import Commande
from salon.models import Vente, Depense, InitPrestation, Prestation, RepartitionMontantPrestation, Service

from salon.views import currency
from employe.common.utils import date_str_to_date_naive

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


def groupe_prestations_par_reference(year: int):
    init_prestations = InitPrestation.objects.prefetch_related(
        'prestation_set__fait_par',
        'prestation_set__service',
    ).order_by('-created_at')

    prestation_par_prestataire: list = []

    for init_pres in init_prestations:
        employe_data = defaultdict(lambda : {
            "initiales": "",
            "nom": "",
            "prenom": "",
            "email": "",
            "nb_services": 0,
            "services": list(),
        })

        for prestation in init_pres.prestation_set.all():
            prestataire = prestation.fait_par.all()
            service = prestation.service

            if prestataire and service:
                key = prestataire.id
                employe_data[key]["nom"] = prestataire.last_name
                employe_data[key]["prenom"] = prestataire.first_name
                employe_data[key]["email"] = prestataire.email
                employe_data[key]["nb_services"] += 1
                employe_data[key]["services"].append(service.designation)

        prestation_par_prestataire.append({
            "reference": init_pres.reference,
            "montant_total": currency(init_pres.montant_total),
            "remise": currency(init_pres.remise),
            "net_paye": currency(init_pres.montant_total - init_pres.remise),
            "date": init_pres.created_at.strftime("%d/%m/%Y"),
            "prestataire": [
                {
                    "initiales": data["prenom"][0] + "" + data["nom"][0],
                    "nom_complet": data["prenom"] + " " + data["nom"],
                    "email": data["email"],
                    "nb_services": data["nb_services"],
                    "services": ", ".join(data["services"]),
                } for data in employe_data.values()
            ]
        })

    return prestation_par_prestataire


@login_required(login_url="login")
def dashmin(request):
    current_year = date.today().year

    # prestations_par_reference = groupe_prestations_par_reference(year=current_year)
    context = {
        "semaines": semaines(),
        "page_title": "Analytics",
        "prestations_par_reference": [],
    }
    return render(request, "dashboard.html", context)


@login_required(login_url="login")
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


@login_required(login_url="login")
def add_employe(request):
    if request.method == "POST":

        try:
            data = json.loads(request.body)
            #  Verification des champs cote serveur
            required_fields = ['first_name', 'last_name', 'telephone']
            for field in required_fields:
                if not escape(data.get(field)):
                    return JsonResponse({"error": f"{field} est obligatoire"}, status=400)

            # Enregistrement de l'employe
            # Recuperer le prenom de l'employe et le mettre tout en minuscule sans espace
            base_first_name = data['first_name'].lower().replace(" ", "")

            # Ajouter 8 caracteres uniques d'un uuid au prenom pour former le username par default
            unique_part = str(uuid.uuid4())[:8]
            username = f"{base_first_name}_{unique_part}"
            password = get_random_string(10)
            employee = Employe.objects.create_user(
                first_name=data['first_name'], last_name=data['last_name'], password=password,
                email=data['email'], telephone=data['telephone'], username=username,
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


def get_stats_vente_produits(date_debut_str, date_fin_str):
    try:
        ventes = Vente.objects.filter(
            created_at__gte=date_debut_str,
            created_at__lte=date_fin_str,
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
        sum_remise_ventes_cash = resultats_ventes_cash['sum_remise_vente_cash'] or 0

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


def get_service_le_plus_demande(filtre):
    # le parametre 'filtre' est de type dictionnaire au format:
    # {"created_at__date__week": week_num}
    return (
        Prestation.objects.filter(**filtre)
        .values("service__id", "service__designation")
        .annotate(nb_services=Count("id"))
        .order_by("-nb_services")
        .first()
    )

def get_montant_total_par_service(id_service, filtres):
    return (
        Prestation.objects.filter(service__id=id_service, **filtres)
        .aggregate(total_montant=Sum("prix_service"))["total_montant"] or 0
    )


def get_stats_prestaions(date_debut, date_fin):
    try:
        prestations = InitPrestation.objects.filter(
            created_at__gte=date_debut,
            created_at__lte=date_fin,
        )

        # Montant total des Prestations
        resultats_montant_prestations = prestations.aggregate(
            sum_montant_prestations=Sum("montant_total"),
            sum_remises=Sum("remise"),
        )
        sum_montant_prestations = resultats_montant_prestations['sum_montant_prestations'] or 0
        sum_remises = resultats_montant_prestations['sum_remises'] or 0

        montant_net_prestations = sum_montant_prestations - sum_remises

        # Nombre de Prestations
        nb_prestations = prestations.count()

        data = {
            "montant_net_prestations": currency(montant_net_prestations) if montant_net_prestations else currency(0),
            "nb_prestations": nb_prestations if nb_prestations else 0,
        }

        return data

    except InitPrestation.DoesNotExist:
        return None

    except Exception as e:
        print("erreur inattendue in get_stats_prestaions :", str(e))
        return None


def get_stats_piscine(date_debut, date_fin):
    try:
        pool_data = Piscine.objects.filter(
            created_at__gte=date_debut,
            created_at__lte=date_fin,
        )
        calcul_montants = pool_data.aggregate(
            sum_prix_unit=Sum(
                ExpressionWrapper(
                    F("nb_client") * F("prix_unitaire"),
                    output_field=BigIntegerField(),
                )
            ),
            sum_remise=Sum(
                ExpressionWrapper(
                    F("nb_client") * F("reduction"),
                    output_field=BigIntegerField(),
                )
            )
        )

        montant_net_entre = calcul_montants["sum_prix_unit"] - calcul_montants["sum_remise"]
        montant_net_entre_str = currency(montant_net_entre)

        return montant_net_entre_str
    except Exception as e:
        print("erreur inattendue :", str(e))
        return 0



@require_http_methods(["POST"])
def filtre_dashmin_data(request):
    try:
        data = json.loads(request.body)

        date_debut_str = data.get("startDate")
        date_fin_str = data.get("endDate")

        date_debut, date_fin = date_str_to_date_naive(date_debut_str, date_fin_str)
        data = {
            "stats_vente_produits": get_stats_vente_produits(date_debut, date_fin),
            "get_stats_prestaions": get_stats_prestaions(date_debut, date_fin),
            "get_stats_piscine": get_stats_piscine(date_debut, date_fin),
        }

        return JsonResponse({"success": True, "data": data}, status=http.HTTPStatus.OK)
    except json.JSONDecodeError:
        return JsonResponse({"error": True, "msg": "Format de données invalides"}, status=400)



current_week = date.today().isocalendar().week
@require_http_methods(["POST"])
def entrees_sorties_salon(request):
    try:
        filters = json.loads(request.body)
        date_debut_str = filters.get("start_date")
        date_fin_str = filters.get("end_date")
        date_debut, date_fin = date_str_to_date_naive(date_debut_str, date_fin_str)

        list_prestations: list = []

        prestations = InitPrestation.objects.filter(
            created_at__gte=date_debut, created_at__lte=date_fin
        ).annotate(
            total_montant=Sum("montant_total"),
            total_remise=Sum("remise")
        )


        sum_montant = prestations.aggregate(Sum("total_montant"))["total_montant__sum"] or 0
        sum_remise = prestations.aggregate(Sum("total_remise"))["total_remise__sum"] or 0
        total_net_entree = sum_montant - sum_remise

        depenses, details_depenses = depenses_par_section("SALON", date_debut, date_fin)

        data = {
            "total_net_entree": total_net_entree,
            "depenses": depenses,
            "details_depenses": details_depenses,
        }
        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        print("Erreur: ", str(e))
        return JsonResponse({"success": False, "msg": str(e)}, status=400)


# Renvoie les Depenses d'une Section du Complexe par Date a savoir :
# Salon ou le Restaurant
# Le param Filters represente soit le numero de la semaine ou du mois
def depenses_par_section(section, date_debut, date_fin):
    try:
        list_depenses: list = []

        depenses = (
            Depense.objects
            .filter(section=section, created_at__gte=date_debut, created_at__lte=date_fin)
            .annotate(
                sum_montant=Sum("montant")
            )
        )
        # for depense in depenses:
            # depense_formatee = depense.copy()
            # depense_formatee['sum_montant'] = currency(depense['sum_montant'])
            # list_depenses.append(depense_formatee)

        sum_depenses = depenses.aggregate(Sum("montant"))["montant__sum"] or 0
        return sum_depenses, list_depenses
    except Depense.DoesNotExist:
        return None, None


def entrees_sorties_restaurant(request):
    try:
        filters = json.loads(request.body)
        date_debut_str = filters.get("start_date")
        date_fin_str = filters.get("end_date")
        date_debut, date_fin = date_str_to_date_naive(date_debut_str, date_fin_str)

        list_commandes: list = []

        commandes = (
            Commande.objects
            .filter(created_at__gte=date_debut, created_at__lte=date_fin)
            .annotate(
                total_montant=Sum("prix_total"),
                total_remise=Sum("reduction")
            )
        )

        # for cmd in commandes:
        #     cmd_formatee = cmd.copy()
        #     cmd_formatee['total_montant'] = currency(cmd['total_montant'])
        #     list_commandes.append(
        #         cmd_formatee
        #     )

        sum_montant = commandes.aggregate(Sum("total_montant"))["total_montant__sum"] or 0
        sum_remise = commandes.aggregate(Sum("total_remise"))["total_remise__sum"] or 0
        total_net_entree = sum_montant - sum_remise

        depenses, details_depenses = depenses_par_section("RESTAURANT", date_debut, date_fin)

        data = {
            "total_net_entree": total_net_entree,
            # "details_entrees": list_commandes,
            "depenses": depenses,
            "details_depenses": details_depenses,
        }
        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        print("Erreur: ", str(e))
        return JsonResponse({"success": False, "msg": str(e)}, status=400)


@login_required(login_url="login")
def performances(request):
    return render(request, tmp_base + "performances.html")


@require_http_methods(["POST"])
def performances_par_date(request):

    try:
        data = json.loads(request.body)
        date_debut_str = data.get("dateDebut")
        date_fin_str = data.get("dateFin")

        date_debut, date_fin = date_str_to_date_naive(date_debut_str, date_fin_str)

        init_prestations_du_jour = InitPrestation.objects.filter(
            created_at__gte=date_debut, created_at__lte=date_fin, montant_attribue=False
        ).order_by("-created_at")

        init_prestations: list = []
        for init_prest in init_prestations_du_jour:
            init_prestations.append({
                "id": init_prest.id,
                "created_at": init_prest.created_at.strftime("%d/%m/%Y %H:%M"),
                "montant_total": init_prest.montant_total,
                "remise": init_prest.remise,
                "client": init_prest.client.nom_complet,
            })
        return JsonResponse({"success": True, "data": init_prestations}, status=200)
    except Exception as e:
        print("Erreur: ", str(e))
        return JsonResponse({"success": False, "msg": str(e)}, status=400)

def details_prestation_par_id(request, id_init_prest):
    try:
        details_prestation = Prestation.objects.filter(init_prestation__id=id_init_prest)
        list_details_prestation: list = []
        for prest in details_prestation:
            list_details_prestation.append({
                "id": prest.id,
                "service": prest.service.designation,
                "id_service": prest.service.id,
                "nb_prestataires": prest.fait_par.count(),
                "prestataires": [(prestataire.id, prestataire.first_name, prestataire.last_name) for prestataire in prest.fait_par.all() ]
            })
        return JsonResponse({"success": True, "data": list_details_prestation}, status=200)
    except Prestation.DoesNotExist:
        return JsonResponse({"success": False, "msg": "Aucun service trouvé pour cette prestation"}, status=404)


def dejaAttribue(id_init_prest, id_employe, id_service):
        return RepartitionMontantPrestation.objects.filter(
            init_prestation__id=id_init_prest,
            employe__id=id_employe,
            service__id=id_service,
        ).exists()

@login_required(login_url="login")
@require_http_methods(["POST"])
def add_attributions(request):
    try:
        data = json.loads(request.body)
        id_init_prestation = data.get("idInitPrestation")
        data_prestation = data.get("tabPrestations")

        init_prestation = InitPrestation.objects.get(id=id_init_prestation)

        total_montant_attribue = sum(int(item['montantAttribue']) for item in data_prestation)
        net_paye = init_prestation.montant_total - init_prestation.remise

        if total_montant_attribue > net_paye:
            return JsonResponse({"success": False, "msg": "Le total des montants attribués depassent le montant de la prestation."}, status=400)

        nb_prestataires: int = 0

        with transaction.atomic():
            nb_prestataires = 0

            for prestation in data_prestation:
                # Si le montant est déjà attribué → passer
                if dejaAttribue(
                        id_init_prestation,
                        prestation['idPrestataire'],
                        prestation['idService']
                ):
                    continue

                employee = Employe.objects.get(id=prestation['idPrestataire'])
                service = Service.objects.get(id=prestation['idService'])

                r = RepartitionMontantPrestation.objects.create(
                    init_prestation=init_prestation,
                    employe=employee,
                    montant_attribue=prestation['montantAttribue'],
                    service=service,
                    created_by=request.user
                )

                if r:
                    nb_prestataires += 1

            # 🚨 CETTE PARTIE NE S’EXÉCUTE
            # 🚨 QUE SI TOUT S’EST BIEN PASSÉ AU-DESSUS
            init_prestation.montant_attribue = True
            init_prestation.created_by = request.user
            init_prestation.save()

        return JsonResponse({"success": True, "msg": f"Montant répartie entre {nb_prestataires} Employé(s)"}, status=201)
    except Exception as e:
        print("Erreur: ", str(e))
        return JsonResponse({"success": False, "msg": str(e)}, status=400)


@require_http_methods(["POST"])
def montant_genere_par_employe(request):
    try:
        data = json.loads(request.body)
        date_debut_str = data.get("dateDebut")
        date_fin_str = data.get("dateFin")

        date_debut, date_fin = date_str_to_date_naive(date_debut_str, date_fin_str)

        total_repartition_par_employe = RepartitionMontantPrestation.objects.filter(
            created_at__range=[date_debut, date_fin]
        ).values(
            "employe__id", "employe__first_name", "employe__last_name", "employe__telephone"
        ).annotate(
            total_attribue=Sum("montant_attribue")
        )
        list_total_repartitions: list = []
        for rep in total_repartition_par_employe:
            list_total_repartitions.append(rep)
        return JsonResponse({"success": True, "data": list_total_repartitions}, status=200)

    except Exception as e:
        print("Erreur: ", str(e))
        return JsonResponse({"success": False, "msg": str(e)}, status=400)


@require_http_methods(["POST", "GET"])
def login_user(request):

    # Si l'utilisateur demande une url dont l'accès necessite l'auth alors
    # on recupere cette url via le parametre 'next'

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(next_url if next_url else 'dashmin')
        else:
            messages.error(request, "Identifiants incorrects. Veuillez réessayer.")
    return render(request, tmp_base + 'login.html', context={"next": next_url})


@login_required(login_url="login")
def logout_user(request):
    logout(request)
    return redirect('login')

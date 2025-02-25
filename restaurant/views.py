import json

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.html import escape

from restaurant.forms import PlatForm, BoissonForm, ApprovisionnementBoissonForm
from restaurant.models import Plat, Boisson

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
                prix = form.cleaned_data['prix_boisson']
                image = form.cleaned_data['prix_achat']

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


def create_commande(request):
    pass

def commande(request):
    return render(request, tmp + "commandes.html")
from django.http import JsonResponse
from django.shortcuts import render

from restaurant.forms import PlatForm, BoissonForm
from restaurant.models import Plat, Boisson

tmp = "restaurant/"
def plats_boissons(request):

    context = {
        "form": PlatForm(),
        "from_boisson": BoissonForm(),
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
                image = form.cleaned_data['photo_boisson']

                Boisson.objects.create(
                    designation=designation, prix_boisson=prix,
                    photo_boisson=image
                )

                return JsonResponse({"msg": "Boisson créée avec succès !"}, status=200)

        except Exception as e:
            print(e)
            return JsonResponse({"error": "Erreur de validation"}, status=400)
    else:
        return JsonResponse({"error": "Methode non autorisée"}, status=405)


def create_commande(request):
    pass

def commande(request):
    return render(request, tmp + "commandes.html")
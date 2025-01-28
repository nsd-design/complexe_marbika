from django.db import models

from employe.models import MyBaseModel


class Plat(MyBaseModel):
    nom_plat = models.CharField(120)
    photo_plat = models.ImageField(null=True, blank=True)
    qr_code = models.CharField(max_length=255)

    def __str__(self):
        return self.nom_plat


class Boisson(MyBaseModel):
    designation = models.CharField(max_length=100)
    qr_code = models.CharField(max_length=255)

    def __str__(self):
        return self.designation


class Commande(MyBaseModel):
    plat_commande = models.ForeignKey(Plat, null=True, on_delete=models.SET_NULL)
    boisson_commande = models.ForeignKey(Boisson, null=True, on_delete=models.SET_NULL)
    prix = models.IntegerField(null=True)
    quantite = models.IntegerField()
    reduction = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.plat_commande.nom_plat} - {self.boisson_commande.designation}"


class ControleBoisson(MyBaseModel):
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE)
    quantite_init = models.IntegerField()
    quantite_vendue = models.IntegerField(null=True)
    quantite_restante = models.IntegerField(null=True)

    def __str__(self):
        return self.boisson.designation

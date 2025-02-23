import uuid

from django.db import models

from employe.models import MyBaseModel


class Plat(MyBaseModel):
    nom_plat = models.CharField(120)
    photo_plat = models.ImageField(null=True, blank=True)
    prix = models.BigIntegerField(null=True)
    qr_code = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.nom_plat


class Boisson(MyBaseModel):
    designation = models.CharField(max_length=100)
    prix_boisson = models.BigIntegerField(null=True)
    qr_code = models.CharField(max_length=255, null=True)
    photo_boisson = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.designation


class Commande(MyBaseModel):
    plat_commande = models.ManyToManyField(Plat, through="CommandePlat")
    boisson_commande = models.ManyToManyField(Boisson, through="CommandeBoisson")
    prix_total = models.BigIntegerField(null=True)
    reduction = models.BigIntegerField(null=True)


    def __str__(self):
        return f"{self.plat_commande.nom_plat} - {self.boisson_commande.designation}"


class CommandePlat(MyBaseModel):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE)
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    prix = models.BigIntegerField()


class CommandeBoisson(MyBaseModel):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE)
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    prix = models.BigIntegerField()

    def __str__(self):
        return f"{self.commande}"


class ControleBoisson(MyBaseModel):
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE)
    quantite_init = models.IntegerField()
    quantite_vendue = models.IntegerField(null=True)
    quantite_restante = models.IntegerField(null=True)


    def __str__(self):
        return self.boisson.designation

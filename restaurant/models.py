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
    prix_achat = models.BigIntegerField(null=True)
    qr_code = models.CharField(max_length=255, null=True)
    photo_boisson = models.ImageField(null=True, blank=True)
    prix_vente = models.BigIntegerField(null=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.designation} - Stock: {self.stock} - PAU: {self.prix_achat}"

    def approvisionner(self, quantite, prix_achat_unitaire):
        if quantite <= 0 or prix_achat_unitaire <= 0:
            raise ValueError("La quantité et le prix d'achat doivent être positifs.")

        ancien_total = self.prix_achat * self.stock if self.prix_achat else 0
        nouveau_total = prix_achat_unitaire * quantite
        self.stock += quantite
        self.prix_achat = int((ancien_total + nouveau_total) / self.stock)
        self.save()

        #  Enregistrement dans l'historique des Approvisionnements
        ApprovisionnementBoisson.objects.create(
            boisson=self,
            quantite=quantite,
            prix_achat_unit=prix_achat_unitaire
        )


class ApprovisionnementBoisson(MyBaseModel):
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_achat_unit = models.BigIntegerField()
    date_approvisionnement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.boisson.designation} Qte: {self.quantite} - Date: {self.date_approvisionnement}"


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

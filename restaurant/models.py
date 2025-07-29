import uuid
from django.db import models
from django.utils import timezone

from employe.models import MyBaseModel


class Plat(MyBaseModel):
    nom_plat = models.CharField(max_length=120)
    photo_plat = models.ImageField(null=True, blank=True, upload_to="plats/")
    prix = models.BigIntegerField(null=True)
    qr_code = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.nom_plat


class Boisson(MyBaseModel):
    designation = models.CharField(max_length=100)
    prix_achat = models.BigIntegerField(null=True)
    qr_code = models.CharField(max_length=255, null=True)
    photo_boisson = models.ImageField(null=True, blank=True, upload_to="boissons/")
    prix_vente = models.BigIntegerField(null=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.designation} - Stock: {self.stock} - PAU: {self.prix_achat}"

    def approvisionner(self, quantite, prix_achat_unitaire, description):
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
            prix_achat_unit=prix_achat_unitaire,
            description=description
        )

    def controle_stock(self, quantite):
        if quantite <= 0:
            raise ValueError("La quantité doit être positive.")
        if quantite > self.stock:
            raise ValueError(f"Stock {self.designation} insuffisant.")

    def vente_boissons(self, quantite):
        self.stock -= int(quantite)
        self.updated_at = timezone.now()
        self.save()


class ApprovisionnementBoisson(MyBaseModel):
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_achat_unit = models.BigIntegerField()
    date_approvisionnement = models.DateTimeField(auto_now_add=True)
    description = models.CharField(null=True, blank=True)


    def __str__(self):
        return f"{self.boisson.designation} Qte: {self.quantite} - Date: {self.date_approvisionnement}"


class Commande(MyBaseModel):
    plat_commande = models.ManyToManyField(Plat, through="CommandePlat")
    boisson_commande = models.ManyToManyField(Boisson, through="CommandeBoisson")
    prix_total = models.BigIntegerField(null=True)
    reduction = models.BigIntegerField(null=True)
    reference = models.CharField(max_length=20, unique=True, blank=True)

    def __str__(self):
        return f"{self.reference} - {self.prix_total}"


class CommandePlat(MyBaseModel):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE)
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    prix = models.BigIntegerField()

    def __str__(self):
        return f"{self.commande} - {self.plat}"


class CommandeBoisson(MyBaseModel):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE)
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    prix = models.BigIntegerField()

    def __str__(self):
        return f"{self.commande} - {self.boisson} - QTE: {self.quantite}"


class ControleBoisson(MyBaseModel):
    status = [(1, "Ouvert"), (2, "Clôturé")]
    statut = models.SmallIntegerField(choices=status, default=1)

    def __str__(self):
        return f"{self.id} - {self.created_at} - {self.statut}"


class DetailsControleBoissons(MyBaseModel):
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE)
    quantite_init = models.IntegerField()
    quantite_vendue = models.IntegerField(null=True)
    quantite_restante = models.IntegerField(null=True)
    controle = models.ForeignKey(ControleBoisson, on_delete=models.CASCADE)
    manquant = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.boisson}"

import uuid
from django.db import models

from employe.models import MyBaseModel, Employe


class CategorieService(MyBaseModel):
    nom_categorie = models.CharField(max_length=120)

    def __str__(self):
        return self.nom_categorie


class Service(MyBaseModel):
    designation = models.CharField(max_length=120)
    categorie = models.ForeignKey(CategorieService, on_delete=models.CASCADE)
    prix_service = models.BigIntegerField(null=True)

    def __str__(self):
        return self.designation


class PrixService(MyBaseModel):
    prix_service = models.BigIntegerField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.service.designation} - {self.prix_service}"

class Prestation(MyBaseModel):
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    montant_a_payer = models.BigIntegerField()
    montant_reduit = models.BigIntegerField(default=0)
    fait_par = models.ForeignKey(Employe, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.service.designation} - {self.fait_par.first_name} {self.fait_par.last_name}"


class Produit(MyBaseModel):
    designation = models.CharField(max_length=120)
    qr_code = models.CharField(max_length=255, null=True)
    stock = models.PositiveIntegerField(default=0)
    prix_achat = models.BigIntegerField(default=0)
    prix_vente = models.BigIntegerField(default=0)
    image = models.ImageField(null=True, blank=True, upload_to="produits/")

    def __str__(self):
        return f"{self.designation} - {self.prix_achat} - {self.prix_vente} | Stock {self.stock}"

    def approvisionner_produit(self, quantite, prix_achat_u, description):
        if quantite <= 0 or prix_achat_u <= 0:
            raise ValueError("La quantité et le prix d'achat doivent être positifs.")

        ancien_total = self.prix_achat * self.stock if self.prix_achat else 0
        nouveau_total = prix_achat_u * quantite
        self.stock += quantite

        # Nouveau prix moyen pondéré
        self.prix_achat = int((ancien_total + nouveau_total) / self.stock)
        self.save()

        #  Enregistrement dans l'historique des Approvisionnements
        Approvisionnement.objects.create(
            produit=self, quantite=quantite, pau=prix_achat_u, description = description
        )


    def controle_stock_produit(self, quantite):
        if quantite <= 0:
            raise ValueError("La quantité doit être positive.")

        if quantite > self.stock:
            raise ValueError(f"{self.designation}, Stock insuffisant.")

    def update_stock(self, quantite):
        self.stock -= int(quantite)
        self.save()


class PrixProduit(MyBaseModel):
    prix_vente = models.BigIntegerField()
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.produit.designation} - {self.prix_vente}"


class Vente(MyBaseModel):
    TYPE_DE_VENTE = [(1, "Cash"), (2, "Crédit")]
    reduction = models.IntegerField(null=True)
    type_vente = models.SmallIntegerField(choices=TYPE_DE_VENTE, default=1)
    montant_total = models.BigIntegerField(null=True)
    reference = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey('client.client', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.reference


class ProduitVendu(MyBaseModel):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name="produits_vendus")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    prix_vente_unitaire = models.BigIntegerField()

    def __str__(self):
        return f"{self.produit.designation} x {self.quantite} - {self.prix_vente_unitaire} GNF"

class Approvisionnement(MyBaseModel):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    pau = models.BigIntegerField()
    description = models.CharField(max_length=255, null=True)


    def __str__(self):
        return f"{self.produit.designation} - {self.quantite}"


class Depense(MyBaseModel):
    motif = models.TextField()
    montant = models.BigIntegerField()
    section = models.UUIDField(db_index=True)

    def __str__(self):
        return f"{self.montant} - {self.motif}"

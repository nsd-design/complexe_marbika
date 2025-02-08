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

    def __str__(self):
        return self.designation


class PrixProduit(MyBaseModel):
    prix_vente = models.BigIntegerField()
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.produit.designation} - {self.prix_vente}"


class Vente(MyBaseModel):
    TYPE_DE_VENTE = [(1, "Cash"), (2, "Crédit")]
    produit = models.ManyToManyField(Produit)
    pvu = models.IntegerField()
    reduction = models.IntegerField(null=True)
    type_vente = models.SmallIntegerField(choices=TYPE_DE_VENTE, default=1)

    def __str__(self):
        return self.produit.designation


class Approvisionnement(MyBaseModel):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    pau = models.BigIntegerField()

    def __str__(self):
        return f"{self.produit.designation} - {self.quantite}"


class Depense(MyBaseModel):
    motif = models.TextField()
    montant = models.BigIntegerField()
    section = models.UUIDField(db_index=True)

    def __str__(self):
        return f"{self.montant} - {self.motif}"

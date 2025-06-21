from django.db import models

from employe.models import MyBaseModel


class Client(MyBaseModel):
    sexes = [(1, "Homme"), (2, "Femme")]

    nom_complet = models.CharField(max_length=200, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    sexe = models.SmallIntegerField(choices=sexes, null=True)

    def __str__(self):
        return f'{self.nom_complet} - {self.telephone}'


class Reservation(MyBaseModel):
    TYPE = [(1, "Service"), (2, "Evénement")]
    ZONE_RESERVE = [(1, "Salon"), (2, "Piscine"), (3, "Local")]
    ETAT_RESERVATION = [(1, "En cours"), (2, "Terminée"), (3, "Annulée"), ]

    type = models.SmallIntegerField(choices=TYPE, default=1)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    zone = models.SmallIntegerField(choices=ZONE_RESERVE)
    etat_reservation = models.SmallIntegerField(choices=ETAT_RESERVATION)


class Location(MyBaseModel):
    locateur = models.ForeignKey(Client, on_delete=models.CASCADE)
    objet = models.CharField(max_length=120, null=True)
    description = models.CharField(max_length=255, null=True)
    montant_a_payer = models.BigIntegerField()
    montant_reduit = models.BigIntegerField(null=True)


class Piscine(MyBaseModel):
    nb_client = models.IntegerField()
    prix_unitaire = models.BigIntegerField()
    reduction = models.BigIntegerField(null=True)
    note = models.CharField(max_length=255, null=True)


class AbonnementGym(MyBaseModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class SeanceGym(MyBaseModel):
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    date_seance = models.DateTimeField(auto_now_add=True)



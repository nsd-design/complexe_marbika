from django.db import models, transaction
from django.db.models import Max

from employe.models import MyBaseModel


class Client(MyBaseModel):
    sexes = [(1, "Homme"), (2, "Femme")]

    code_client = models.CharField(
        max_length=7,
        unique=True,
        null=True,
        blank=True,
    )

    nom_complet = models.CharField(max_length=200, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    sexe = models.SmallIntegerField(choices=sexes, null=True)


    def save(self, *args, **kwargs):
        if not self.code_client:
            self.code_client = self.generate_code_client()
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.code_client} - {self.nom_complet} - {self.telephone}'


    @staticmethod
    def generate_code_client():
        with transaction.atomic():
            last_code = (
                Client.objects.select_for_update()
                .aggregate(max_code=Max("code_client"))["max_code"]
            )

            if last_code:
                last_number = int(last_code[1:])
            else:
                last_number = 0

            return f"C{last_number + 1:04d}"


class ZoneAReserver(MyBaseModel):
    STATUT_CHOICES = [('libre', "LIBRE"), ('reserve', "RESERVEE")]

    nom = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='libre')

    def __str__(self):
        return f"Zone: {self.nom} - {self.get_statut_display()}"

class Reservation(MyBaseModel):
    TYPE = [(1, "Service"), (2, "Evénement")]
    ETAT_RESERVATION = [(1, "En cours"), (2, "Terminée"), (3, "Annulée"), (4, "En attente"), (5, "Confirmée")]

    type = models.SmallIntegerField(choices=TYPE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    zone = models.ForeignKey(ZoneAReserver, on_delete=models.CASCADE)
    etat_reservation = models.SmallIntegerField(choices=ETAT_RESERVATION)
    date_debut = models.DateField()
    date_fin = models.DateField()
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.zone.nom}"


class Location(MyBaseModel):
    STATUT_LOCATION = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('expiree', 'Expirée'),
    ]
    TYPE = [(1, "Service"), (2, "Evénement")]

    locateur = models.ForeignKey(Client, on_delete=models.CASCADE)
    objet = models.CharField(max_length=120, null=True)
    zone = models.ForeignKey(ZoneAReserver, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    montant_a_payer = models.BigIntegerField()
    montant_reduit = models.BigIntegerField(null=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_LOCATION, default='en_attente')
    type_location = models.SmallIntegerField(choices=TYPE)

    def __str__(self):
        return f"{self.zone.nom} - {self.locateur.nom_complet} - Début: {self.date_debut}, Fin: {self.date_fin}"


class Piscine(MyBaseModel):
    nb_client = models.IntegerField()
    prix_unitaire = models.BigIntegerField()
    reduction = models.BigIntegerField(null=True, default=0)
    note = models.CharField(max_length=255, null=True, blank=True)


class AbonnementGym(MyBaseModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class SeanceGym(MyBaseModel):
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    date_seance = models.DateTimeField(auto_now_add=True)



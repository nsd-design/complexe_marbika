from django.db import models

from employe.models import MyBaseModel


class Apprenti(MyBaseModel):
    nom_complet = models.CharField(max_length=120)
    telephone = models.CharField(max_length=20)


class Formation(MyBaseModel):
    titre = models.CharField(max_length=120)
    cout_formation = models.BigIntegerField()


class Inscription(MyBaseModel):
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True)
    apprenti = models.ForeignKey(Apprenti, null=True, on_delete=models.SET)
    frais_insrciption = models.BigIntegerField(null=True)
    cout_formation = models.BigIntegerField()
    reduction = models.BigIntegerField(null=True)

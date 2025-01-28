import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Employe(AbstractUser):
    pass

class MyBaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True,
                                   related_name="created_%(class)s_set")
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(Employe, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="updated_%(class)s_set")


    class Meta:
        abstract = True

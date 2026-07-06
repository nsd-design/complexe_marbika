import secrets
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Employe(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    telephone = models.CharField(max_length=18)

    # Jeton opaque encodé dans le QR du badge. Aléatoire (~128 bits), donc non
    # énumérable/falsifiable, et rotatif (révocable si le badge est perdu/volé) :
    # voir rotate_badge_token(). Distinct de la PK exprès (identité interne).
    badge_token = models.CharField(max_length=32, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)

    @staticmethod
    def generate_badge_token():
        return secrets.token_urlsafe(16)  # ~22 caractères, 128 bits

    def rotate_badge_token(self):
        """Révoque le badge courant en régénérant le jeton (badge perdu/volé)."""
        self.badge_token = self.generate_badge_token()
        self.save(update_fields=["badge_token"])

    def save(self, *args, **kwargs):
        if not self.badge_token:
            self.badge_token = self.generate_badge_token()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.telephone})"



class MyBaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True,
                                   related_name="created_%(class)s_set")
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(Employe, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="updated_%(class)s_set")


    class Meta:
        abstract = True

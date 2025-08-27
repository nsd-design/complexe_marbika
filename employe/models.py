import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class EmployeManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire")

        extra_fields.setdefault('is_active', True)
        # Normaliser l'email s'il est fourni
        if 'email' in extra_fields and extra_fields['email']:
            extra_fields['email'] = self.normalize_email(extra_fields['email'])

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)

class Employe(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(null=True, blank=True, max_length=255)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    telephone = models.CharField(max_length=18)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = EmployeManager()

    USERNAME_FIELD = 'username'  # Définit l'identifiant principal
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} {self.telephone}'



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

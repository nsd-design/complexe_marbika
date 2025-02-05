import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class EmployeManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class Employe(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    telephone = models.CharField(max_length=18)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = EmployeManager()

    USERNAME_FIELD = 'email'  # Définit l'identifiant principal
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return {self.email}



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

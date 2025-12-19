from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import Employe


class EmployeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = Employe
        fields = ["first_name", "last_name", "email", "telephone"]


class EmployeCreationForm(UserCreationForm):
    class Meta:
        model = Employe
        fields = ("username", "first_name", "last_name", "email", "telephone")


class EmployeChangeForm(UserChangeForm):
    class Meta:
        model = Employe
        fields = ("username", "first_name", "last_name", "email", "telephone", "is_active", "is_staff")
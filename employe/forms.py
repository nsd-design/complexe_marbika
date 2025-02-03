from django import forms
from .models import Employe


class EmployeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = Employe
        fields = ["first_name", "last_name", "email", "telephone"]
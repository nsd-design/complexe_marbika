from django import forms
from . import models


class LocationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].label = ''

    montant_reduit = forms.CharField(required=False)
    objet = forms.CharField(required=False)

    class Meta:
        model = models.Location
        fields = [
            'locateur', 'objet', 'zone','description', 'montant_a_payer',
            'montant_reduit', 'date_debut', 'date_fin', 'statut', 'type_location'
        ]

        widgets = {
            'date_debut' : forms.DateInput(attrs={'type': 'date'}),
            'date_fin' : forms.DateInput(attrs={'type': 'date'})
        }

from django import forms
from .models import CategorieService, Service, Prestation, PrixService


class CategorieForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = CategorieService
        fields = ['nom_categorie']


class ServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = Service
        fields = ['designation', 'categorie']


class PrixServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer les Labels par defaut
        for field_name in self.fields:
            self.fields[field_name].label = ''

    class Meta:
        model = PrixService
        fields = ['prix_service', 'service']

class PrestationForm(forms.ModelForm):
    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Supprimer les Labels par defaut
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = Prestation
        fields = ['service', 'montant_a_payer', 'montant_reduit', 'fait_par']
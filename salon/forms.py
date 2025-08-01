from django import forms
from .models import CategorieService, Service, Prestation, PrixService, Produit, Approvisionnement, InitPrestation, Depense


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


class InitPrestationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer les Labels par defaut
        for field_name in self.fields:
            self.fields[field_name].label = ''

    class Meta:
        model = InitPrestation
        fields = ['reference', 'montant_total', 'remise']

class PrestationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Supprimer les Labels par defaut
        for field_name in self.fields:
            self.fields[field_name].label = ''

    class Meta:
        model = Prestation
        fields = ['service', 'prix_service', 'init_prestation']


class ProduitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''

    class Meta:
        model = Produit
        fields = ["designation", "prix_achat", "prix_vente", "stock", "image"]


class ApproProduitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''

    class Meta:
        model = Approvisionnement
        fields = ["produit", "quantite", "pau", "description"]


class DepensesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = Depense
        fields = ["motif", "montant", "section"]
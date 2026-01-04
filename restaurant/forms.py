from django import forms

from restaurant.models import Plat, Boisson, ApprovisionnementBoisson
from salon.models import Approvisionnement


class PlatForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = Plat
        fields = ['nom_plat', 'prix', 'photo_plat']


class BoissonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = Boisson
        fields = ['designation', 'photo_boisson', 'prix_vente', 'stock']


class ApprovisionnementBoissonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''


    class Meta:
        model = ApprovisionnementBoisson
        fields = ['boisson', 'quantite', 'prix_achat_unit']
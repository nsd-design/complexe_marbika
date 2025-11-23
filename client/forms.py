from django import forms
from . import models


class LocationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].label = ''

    montant_reduit = forms.FloatField(
        required=False,
        widget=forms.NumberInput()
    )
    objet = forms.CharField(required=False)
    locateur = forms.CharField(required=False)

    class Meta:
        model = models.Location
        fields = [
            'locateur', 'objet', 'zone','description', 'montant_a_payer',
            'montant_reduit', 'date_debut', 'date_fin', 'statut', 'type_location'
        ]

        widgets = {
            'date_debut' : forms.DateInput(attrs={'type': 'date'}),
            'date_fin' : forms.DateInput(attrs={'type': 'date'}),
        }


class ZoneForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].label = ''

    class Meta:
        model = models.ZoneAReserver
        fields = ['nom', 'statut']


class ReservationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].label = ''

    class Meta:
        model = models.Reservation
        fields = ["type", "client", "zone", "etat_reservation", "date_debut", "date_fin", "commentaire"]

        widgets = {
            'date_debut' : forms.DateInput(attrs={'type': 'date', 'id': 'date_debut_reservation'}),
            'date_fin' : forms.DateInput(attrs={'type': 'date', 'id': 'date_fin_reservation'}),
            'zone' : forms.Select(attrs={'id': 'zone_reservation'})
        }

class PiscineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].label = ''

        self.fields['reduction'].widget.attrs['min'] = 0
        self.fields['nb_client'].widget.attrs['min'] = 1
        self.fields['prix_unitaire'].widget.attrs['min'] = 10000


    class Meta:
        model = models.Piscine
        fields = ['nb_client', 'prix_unitaire', 'reduction', 'note']

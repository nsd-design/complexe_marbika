from datetime import date, timedelta, datetime
from django.utils import timezone

def date_str_to_date_naive(date_debut_str, date_fin_str):
    # Convertir en datetime naive
    date_debut_naive = datetime.strptime(date_debut_str, "%Y-%m-%d")
    date_fin_naive = datetime.strptime(date_fin_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    # Rendre aware selon TIME_ZONE défini dans settings.py
    date_debut = timezone.make_aware(date_debut_naive)
    date_fin = timezone.make_aware(date_fin_naive)

    return date_debut, date_fin
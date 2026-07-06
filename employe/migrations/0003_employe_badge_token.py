import secrets

from django.db import migrations, models


def backfill_badge_token(apps, schema_editor):
    Employe = apps.get_model("employe", "Employe")
    for employe in Employe.objects.filter(badge_token__isnull=True):
        # Boucle défensive contre une éventuelle collision (probabilité infime).
        while True:
            token = secrets.token_urlsafe(16)
            if not Employe.objects.filter(badge_token=token).exists():
                break
        employe.badge_token = token
        employe.save(update_fields=["badge_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("employe", "0002_employe_created_at_employe_created_by_and_more"),
    ]

    operations = [
        # 1. Ajout nullable pour ne pas casser sur la table déjà peuplée.
        #    Pas de db_index ici : unique=True (étape 3) crée déjà l'index ;
        #    le cumuler ferait entrer en collision les index "_like" varchar.
        migrations.AddField(
            model_name="employe",
            name="badge_token",
            field=models.CharField(editable=False, max_length=32, null=True),
        ),
        # 2. Génération d'un jeton pour chaque employé existant.
        migrations.RunPython(backfill_badge_token, migrations.RunPython.noop),
        # 3. Passage en unique + non-null une fois tout peuplé.
        migrations.AlterField(
            model_name="employe",
            name="badge_token",
            field=models.CharField(editable=False, max_length=32, unique=True),
        ),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pointage", "0004_alter_attendance_employee"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Renommage (préserve la colonne et ses données, contrairement à un
        # remove+add qu'aurait généré un changement de related_name en auto).
        migrations.RenameField(
            model_name="attendance",
            old_name="recorded_by",
            new_name="created_by",
        ),
        migrations.AlterField(
            model_name="attendance",
            name="created_by",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pointages_crees",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="attendance",
            name="updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendance",
            name="updated_by",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pointages_modifies",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

import uuid

from django.db import migrations, models


def forward_migration(apps, schema_editor):
    Repartition = apps.get_model('salon', 'RepartitionMontantPrestation')
    Detail = apps.get_model('salon', 'DetailRepartitionMontant')

    batch_size = 1000
    qs = Repartition.objects.all().iterator(chunk_size=batch_size)

    details_to_create = []

    for rep in qs:
        if rep.service:
            details_to_create.append(
                Detail(
                    repartition=rep,
                    service=rep.service,
                )
            )

        if len(details_to_create) >= batch_size:
            Detail.objects.bulk_create(details_to_create, batch_size)
            details_to_create = []

    if details_to_create:
        Detail.objects.bulk_create(details_to_create, batch_size)


def reverse_migration(apps, schema_editor):
    """
    Rollback : on restaure le champ service depuis le premier detail trouvé
    """
    Repartition = apps.get_model('salon', 'RepartitionMontantPrestation')
    Detail = apps.get_model('salon', 'DetailRepartitionMontant')

    for rep in Repartition.objects.all().iterator():
        detail = Detail.objects.filter(repartition=rep.id).first()
        if detail:
            rep.service = detail.service
            rep.save(update_fields=['service'])


class Migration(migrations.Migration):

    dependencies = [
        ('salon', '0012_alter_prestation_created_at'),
    ]

    operations = [

        migrations.CreateModel(
            name='DetailRepartitionMontant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('repartition', models.ForeignKey(on_delete=models.CASCADE, to='salon.repartitionmontantprestation')),
                ('service', models.ForeignKey(null=True, on_delete=models.SET_NULL, to='salon.service')),
            ],
        ),

        migrations.RunPython(forward_migration, reverse_migration),
    ]
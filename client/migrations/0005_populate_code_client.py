from django.db import migrations


def populate_code_client(apps, schema_editor):
    Client = apps.get_model('client', 'Client')

    clients = Client.objects.order_by("created_at")

    for index, client in enumerate(clients, start=1):
        if not client.code_client:
            client.code_client = f"C{index:04d}"
            client.save(update_fields=["code_client"])


class Migration(migrations.Migration):
    dependencies = [
        ('client', '0004_client_code_client'),
    ]

    operations = [
        migrations.RunPython(populate_code_client)
    ]
import uuid
from django.db import migrations, models


def assign_unique_tokens(apps, schema_editor):
    Mekan = apps.get_model('venues', 'Mekan')
    for mekan in Mekan.objects.all():
        mekan.dogrulama_token = uuid.uuid4()
        mekan.save(update_fields=['dogrulama_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0011_mekan_latitude_mekan_longitude_mekan_telefon_and_more'),
    ]

    operations = [
        # 1) Alan null olarak ekle
        migrations.AddField(
            model_name='mekan',
            name='dogrulama_token',
            field=models.UUIDField(null=True, blank=True),
        ),
        # 2) Mevcut kayıtlara benzersiz UUID ata
        migrations.RunPython(assign_unique_tokens, migrations.RunPython.noop),
        # 3) unique=True ve null=False yap
        migrations.AlterField(
            model_name='mekan',
            name='dogrulama_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]

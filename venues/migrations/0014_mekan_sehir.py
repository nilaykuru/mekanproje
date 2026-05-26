from django.db import migrations, models


def mevcut_istanbul_yap(apps, schema_editor):
    Mekan = apps.get_model('venues', 'Mekan')
    Mekan.objects.filter(sehir__isnull=True).update(sehir='istanbul')


class Migration(migrations.Migration):
    dependencies = [('venues', '0013_profile_email_verification')]

    operations = [
        migrations.AddField(
            model_name='mekan',
            name='sehir',
            field=models.CharField(
                blank=True, null=True, max_length=20,
                choices=[
                    ('istanbul', 'İstanbul'),
                    ('izmir', 'İzmir'),
                    ('samsun', 'Samsun'),
                    ('sakarya', 'Sakarya'),
                ],
                verbose_name='Şehir',
            ),
        ),
        migrations.RunPython(mevcut_istanbul_yap, migrations.RunPython.noop),
    ]

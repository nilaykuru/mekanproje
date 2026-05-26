import uuid
from django.db import migrations, models


def assign_unique_tokens(apps, schema_editor):
    Profile = apps.get_model('venues', 'Profile')
    for profile in Profile.objects.all():
        profile.email_verification_token = uuid.uuid4()
        profile.save(update_fields=['email_verification_token'])


class Migration(migrations.Migration):
    dependencies = [('venues', '0012_dogrulama_token')]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='email_verification_token',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.RunPython(assign_unique_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='profile',
            name='email_verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]

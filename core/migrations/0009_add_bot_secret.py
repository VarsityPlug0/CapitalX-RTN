# Generated migration to add bot_secret field to CustomUser model

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_delete_voucher'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='bot_secret',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
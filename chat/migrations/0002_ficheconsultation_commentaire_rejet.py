from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ficheconsultation',
            name='commentaire_rejet',
            field=models.TextField(blank=True, null=True, help_text='Motif détaillé en cas de rejet'),
        ),
    ]

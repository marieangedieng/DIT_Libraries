from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("gestion_emprunts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emprunt",
            name="date_emprunt",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]

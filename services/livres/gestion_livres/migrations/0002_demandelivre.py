from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gestion_livres", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DemandeLivre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("utilisateur_id", models.PositiveIntegerField()),
                ("utilisateur_nom", models.CharField(max_length=255)),
                ("titre", models.CharField(max_length=255)),
                ("auteur", models.CharField(blank=True, max_length=255)),
                ("isbn", models.CharField(blank=True, max_length=32)),
                ("categorie_suggeree", models.CharField(blank=True, max_length=120)),
                ("description", models.TextField(blank=True)),
                ("commentaire_gestionnaire", models.TextField(blank=True)),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("en_cours_traitement", "En cours de traitement"),
                            ("en_attente_livre", "En attente du livre"),
                            ("refuse", "Refusé"),
                            ("livre_disponible", "Livre disponible"),
                            ("cloturee", "Clôturée"),
                        ],
                        default="en_cours_traitement",
                        max_length=32,
                    ),
                ),
                ("fermee_le", models.DateTimeField(blank=True, null=True)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-cree_le"],
            },
        ),
    ]

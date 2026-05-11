from django.contrib.auth.hashers import make_password
from django.db import migrations, models


DEFAULT_PASSWORD_HASH = make_password("ChangeMe123!")


def migrer_roles(apps, schema_editor):
    utilisateur_model = apps.get_model("membres", "UtilisateurBibliotheque")
    utilisateur_model.objects.filter(type_utilisateur="personnel").update(type_utilisateur="gestionnaire")
    utilisateur_model.objects.filter(mot_de_passe="").update(mot_de_passe=DEFAULT_PASSWORD_HASH)


class Migration(migrations.Migration):

    dependencies = [
        ("membres", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="utilisateurbibliotheque",
            name="mot_de_passe",
            field=models.CharField(default=DEFAULT_PASSWORD_HASH, max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="utilisateurbibliotheque",
            name="type_utilisateur",
            field=models.CharField(
                choices=[
                    ("etudiant", "Étudiant"),
                    ("professeur", "Professeur"),
                    ("gestionnaire", "Gestionnaire"),
                    ("admin", "Administrateur"),
                ],
                default="etudiant",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrer_roles, migrations.RunPython.noop),
    ]

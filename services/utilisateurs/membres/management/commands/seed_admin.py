import os

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from membres.models import UtilisateurBibliotheque


class Command(BaseCommand):
    help = "Crée ou met à jour le compte admin Django et les comptes métier par défaut."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_ADMIN_USERNAME", "ditadmin")
        email = os.getenv("DJANGO_ADMIN_EMAIL", "admin@dit.local")
        password = os.getenv("DJANGO_ADMIN_PASSWORD", "AdminDIT123!")
        first_name = os.getenv("DJANGO_ADMIN_FIRST_NAME", "DIT")
        last_name = os.getenv("DJANGO_ADMIN_LAST_NAME", "Admin")
        card_number = os.getenv("DJANGO_ADMIN_CARD_NUMBER", username)

        user_model = get_user_model()
        admin_user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        updated = False
        if admin_user.email != email:
            admin_user.email = email
            updated = True
        if not admin_user.is_staff:
            admin_user.is_staff = True
            updated = True
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            updated = True
        if first_name and admin_user.first_name != first_name:
            admin_user.first_name = first_name
            updated = True
        if last_name and admin_user.last_name != last_name:
            admin_user.last_name = last_name
            updated = True

        admin_user.set_password(password)
        updated = True

        if updated:
            admin_user.save()

        UtilisateurBibliotheque.objects.update_or_create(
            email=email,
            defaults={
                "prenom": first_name,
                "nom": last_name,
                "telephone": "",
                "departement": "Administration",
                "numero_carte": card_number,
                "type_utilisateur": UtilisateurBibliotheque.TypeUtilisateur.ADMIN,
                "actif": True,
                "mot_de_passe": make_password(password),
            },
        )

        manager_username = os.getenv("DIT_MANAGER_USERNAME", "manager1")
        manager_email = os.getenv("DIT_MANAGER_EMAIL", "manager1@dit.local")
        manager_password = os.getenv("DIT_MANAGER_PASSWORD", "manager")
        manager_first_name = os.getenv("DIT_MANAGER_FIRST_NAME", "Manager")
        manager_last_name = os.getenv("DIT_MANAGER_LAST_NAME", "Demo")
        manager_card_number = os.getenv("DIT_MANAGER_CARD_NUMBER", manager_username)

        UtilisateurBibliotheque.objects.update_or_create(
            email=manager_email,
            defaults={
                "prenom": manager_first_name,
                "nom": manager_last_name,
                "telephone": "",
                "departement": "Bibliothèque",
                "numero_carte": manager_card_number,
                "type_utilisateur": UtilisateurBibliotheque.TypeUtilisateur.GESTIONNAIRE,
                "actif": True,
                "mot_de_passe": make_password(manager_password),
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Comptes prêts: admin={username} / {email}, manager={manager_username} / {manager_email}"
            )
        )

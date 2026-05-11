import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée ou met à jour le compte administrateur Django pour le service emprunts."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_ADMIN_USERNAME", "ditadmin")
        email = os.getenv("DJANGO_ADMIN_EMAIL", "admin@dit.local")
        password = os.getenv("DJANGO_ADMIN_PASSWORD", "AdminDIT123!")
        first_name = os.getenv("DJANGO_ADMIN_FIRST_NAME", "DIT")
        last_name = os.getenv("DJANGO_ADMIN_LAST_NAME", "Admin")

        user_model = get_user_model()
        admin_user, _created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        admin_user.email = email
        admin_user.first_name = first_name
        admin_user.last_name = last_name
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password(password)
        admin_user.save()

        self.stdout.write(self.style.SUCCESS(f"Compte admin emprunts prêt: {username}"))

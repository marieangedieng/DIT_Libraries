from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Emprunt


class EmpruntModeleTestCase(TestCase):
    def test_creation_emprunt(self):
        emprunt = Emprunt.objects.create(
            utilisateur_id=1,
            utilisateur_nom="Aminata Ndiaye",
            livre_id=1,
            livre_titre="Architecture des API",
            date_retour_prevue=timezone.now().date() + timedelta(days=7),
        )
        self.assertIn("Aminata", str(emprunt))

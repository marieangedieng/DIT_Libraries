from django.test import TestCase

from .models import UtilisateurBibliotheque


class UtilisateurModeleTestCase(TestCase):
    def test_creation_utilisateur(self):
        utilisateur = UtilisateurBibliotheque.objects.create(
            nom="Ndiaye",
            prenom="Aminata",
            email="aminata.ndiaye@example.com",
            numero_carte="DIT-001",
        )
        self.assertEqual(str(utilisateur), "Aminata Ndiaye")

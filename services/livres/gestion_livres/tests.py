from django.test import TestCase

from .models import Livre


class LivreModeleTestCase(TestCase):
    def test_creation_livre(self):
        livre = Livre.objects.create(
            titre="Python pour la data",
            auteur="DIT",
            isbn="ISBN-TEST-001",
            categorie="Programmation",
            quantite_totale=3,
            quantite_disponible=3,
        )
        self.assertEqual(str(livre), "Python pour la data - DIT")

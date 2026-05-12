from django.db import migrations


BOOKS = [
    {
        "titre": "Clean Code",
        "auteur": "Robert C. Martin",
        "isbn": "9780132350884",
        "categorie": "Développement logiciel",
        "description": "Bonnes pratiques de conception, lisibilité et maintenance du code professionnel.",
        "langue": "English",
        "quantite_totale": 4,
        "quantite_disponible": 4,
    },
    {
        "titre": "Design Patterns",
        "auteur": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
        "isbn": "0201633612",
        "categorie": "Architecture logicielle",
        "description": "Catalogue des patrons de conception orientés objet les plus utilisés.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "The Pragmatic Programmer",
        "auteur": "Andrew Hunt, David Thomas",
        "isbn": "9780135957059",
        "categorie": "Développement logiciel",
        "description": "Principes concrets pour écrire, tester et faire évoluer des logiciels durables.",
        "langue": "English",
        "quantite_totale": 4,
        "quantite_disponible": 4,
    },
    {
        "titre": "Refactoring",
        "auteur": "Martin Fowler",
        "isbn": "9780134757599",
        "categorie": "Développement logiciel",
        "description": "Méthodes pour améliorer un code existant sans en changer le comportement.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "Code Complete",
        "auteur": "Steve McConnell",
        "isbn": "9780735619678",
        "categorie": "Génie logiciel",
        "description": "Référence sur la construction logicielle, la qualité et les pratiques d'équipe.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "Introduction to Algorithms",
        "auteur": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
        "isbn": "9780262046305",
        "categorie": "Algorithmes",
        "description": "Ouvrage de référence sur les structures algorithmiques et leur analyse.",
        "langue": "English",
        "quantite_totale": 2,
        "quantite_disponible": 2,
    },
    {
        "titre": "Computer Networking: A Top-Down Approach",
        "auteur": "James F. Kurose, Keith W. Ross",
        "isbn": "9780133594140",
        "categorie": "Réseaux",
        "description": "Introduction progressive aux réseaux et aux protocoles modernes.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "Operating System Concepts",
        "auteur": "Abraham Silberschatz, Peter B. Galvin, Greg Gagne",
        "isbn": "9781119456339",
        "categorie": "Systèmes d'exploitation",
        "description": "Fondamentaux des processus, de la mémoire, des fichiers et de la concurrence.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "Artificial Intelligence: A Modern Approach",
        "auteur": "Stuart Russell, Peter Norvig",
        "isbn": "9780134610993",
        "categorie": "Intelligence artificielle",
        "description": "Vue d'ensemble des techniques majeures de l'intelligence artificielle.",
        "langue": "English",
        "quantite_totale": 2,
        "quantite_disponible": 2,
    },
    {
        "titre": "Deep Learning",
        "auteur": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
        "isbn": "9780262035613",
        "categorie": "Machine learning",
        "description": "Base théorique solide sur les réseaux de neurones et l'apprentissage profond.",
        "langue": "English",
        "quantite_totale": 2,
        "quantite_disponible": 2,
    },
    {
        "titre": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow",
        "auteur": "Aurelien Geron",
        "isbn": "9781492032649",
        "categorie": "Machine learning",
        "description": "Approche pratique du machine learning avec les bibliothèques Python courantes.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "Python Crash Course",
        "auteur": "Eric Matthes",
        "isbn": "9781593279288",
        "categorie": "Programmation Python",
        "description": "Introduction rapide à Python avec projets d'application.",
        "langue": "English",
        "quantite_totale": 4,
        "quantite_disponible": 4,
    },
    {
        "titre": "Fluent Python",
        "auteur": "Luciano Ramalho",
        "isbn": "9781492056355",
        "categorie": "Programmation Python",
        "description": "Utilisation avancée de Python idiomatique et de ses mécanismes internes.",
        "langue": "English",
        "quantite_totale": 2,
        "quantite_disponible": 2,
    },
    {
        "titre": "Head First Design Patterns",
        "auteur": "Eric Freeman, Elisabeth Robson",
        "isbn": "9780596007126",
        "categorie": "Architecture logicielle",
        "description": "Introduction pédagogique aux patterns avec exemples orientés pratique.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "Cracking the Coding Interview",
        "auteur": "Gayle Laakmann McDowell",
        "isbn": "9780984782857",
        "categorie": "Préparation entretien",
        "description": "Exercices et stratégies pour les entretiens techniques en informatique.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "The Mythical Man-Month",
        "auteur": "Frederick P. Brooks Jr.",
        "isbn": "9780201835953",
        "categorie": "Gestion de projet",
        "description": "Essais classiques sur la coordination d'équipes et les risques logiciels.",
        "langue": "English",
        "quantite_totale": 2,
        "quantite_disponible": 2,
    },
    {
        "titre": "Structure and Interpretation of Computer Programs",
        "auteur": "Harold Abelson, Gerald Jay Sussman",
        "isbn": "9780262510875",
        "categorie": "Informatique fondamentale",
        "description": "Texte majeur sur les abstractions, langages et principes computationnels.",
        "langue": "English",
        "quantite_totale": 2,
        "quantite_disponible": 2,
    },
    {
        "titre": "Effective Java",
        "auteur": "Joshua Bloch",
        "isbn": "9780134685991",
        "categorie": "Programmation Java",
        "description": "Recommandations concrètes pour écrire des applications Java robustes.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "You Don't Know JS Yet",
        "auteur": "Kyle Simpson",
        "isbn": "9781091210097",
        "categorie": "Programmation JavaScript",
        "description": "Exploration détaillée du langage JavaScript moderne et de son fonctionnement.",
        "langue": "English",
        "quantite_totale": 3,
        "quantite_disponible": 3,
    },
    {
        "titre": "Domain-Driven Design",
        "auteur": "Eric Evans",
        "isbn": "9780321125217",
        "categorie": "Architecture logicielle",
        "description": "Conception métier pour structurer des systèmes complexes et évolutifs.",
        "langue": "English",
        "quantite_totale": 2,
        "quantite_disponible": 2,
    },
]


def seed_books(apps, schema_editor):
    livre_model = apps.get_model("gestion_livres", "Livre")

    for book in BOOKS:
        livre_model.objects.update_or_create(
            isbn=book["isbn"],
            defaults=book,
        )


def unseed_books(apps, schema_editor):
    livre_model = apps.get_model("gestion_livres", "Livre")
    livre_model.objects.filter(isbn__in=[book["isbn"] for book in BOOKS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("gestion_livres", "0002_demandelivre"),
    ]

    operations = [
        migrations.RunPython(seed_books, unseed_books),
    ]

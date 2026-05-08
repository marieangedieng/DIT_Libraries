from django.contrib import admin

from .models import DemandeLivre, Livre


@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    list_display = ("titre", "auteur", "isbn", "categorie", "quantite_disponible", "actif")
    search_fields = ("titre", "auteur", "isbn", "categorie")
    list_filter = ("categorie", "actif")


@admin.register(DemandeLivre)
class DemandeLivreAdmin(admin.ModelAdmin):
    list_display = ("titre", "utilisateur_nom", "statut", "cree_le", "fermee_le")
    search_fields = ("titre", "auteur", "isbn", "utilisateur_nom")
    list_filter = ("statut",)
    readonly_fields = ("cree_le", "modifie_le", "fermee_le")

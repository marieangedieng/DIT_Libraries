from django.contrib import admin

from .models import Emprunt


@admin.register(Emprunt)
class EmpruntAdmin(admin.ModelAdmin):
    list_display = ("utilisateur_nom", "livre_titre", "date_emprunt", "date_retour_prevue", "statut")
    search_fields = ("utilisateur_nom", "livre_titre")
    list_filter = ("statut",)

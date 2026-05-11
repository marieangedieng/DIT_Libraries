from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from .models import UtilisateurBibliotheque


class UtilisateurBibliothequeAdminForm(forms.ModelForm):
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Saisissez un mot de passe en clair. Il sera chiffré automatiquement.",
    )

    class Meta:
        model = UtilisateurBibliotheque
        fields = "__all__"

    def clean_mot_de_passe(self):
        mot_de_passe = self.cleaned_data.get("mot_de_passe", "")
        if not mot_de_passe:
            if self.instance.pk:
                return self.instance.mot_de_passe
            raise ValidationError("Le mot de passe est obligatoire.")

        if mot_de_passe.startswith("pbkdf2_"):
            return mot_de_passe
        return make_password(mot_de_passe)


@admin.register(UtilisateurBibliotheque)
class UtilisateurBibliothequeAdmin(admin.ModelAdmin):
    form = UtilisateurBibliothequeAdminForm
    list_display = ("prenom", "nom", "email", "type_utilisateur", "numero_carte", "actif")
    search_fields = ("prenom", "nom", "email", "numero_carte")
    list_filter = ("type_utilisateur", "actif")
    readonly_fields = ("cree_le", "modifie_le")

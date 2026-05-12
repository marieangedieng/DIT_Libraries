from django.db.models import Q
from rest_framework import serializers

from .models import DemandeLivre, Livre


class LivreSerializer(serializers.ModelSerializer):
    disponibilite = serializers.SerializerMethodField()

    class Meta:
        model = Livre
        fields = "__all__"

    def validate(self, attrs):
        quantite_totale = attrs.get("quantite_totale", getattr(self.instance, "quantite_totale", 0))
        quantite_disponible = attrs.get(
            "quantite_disponible",
            getattr(self.instance, "quantite_disponible", 0),
        )
        if quantite_disponible > quantite_totale:
            raise serializers.ValidationError(
                "La quantité disponible ne peut pas dépasser la quantité totale."
            )
        return attrs

    def get_disponibilite(self, obj):
        return "Disponible" if obj.quantite_disponible > 0 else "Pas disponible"


class DemandeLivreSerializer(serializers.ModelSerializer):
    statut_label = serializers.SerializerMethodField()

    class Meta:
        model = DemandeLivre
        fields = "__all__"

    def validate(self, attrs):
        titre = attrs.get("titre", getattr(self.instance, "titre", "")).strip()
        auteur = attrs.get("auteur", getattr(self.instance, "auteur", "")).strip()
        isbn = attrs.get("isbn", getattr(self.instance, "isbn", "")).strip()

        if self.instance is None:
            filtres = Q(titre__iexact=titre)
            if auteur:
                filtres &= Q(auteur__iexact=auteur)
            if isbn:
                filtres |= Q(isbn__iexact=isbn)

            if Livre.objects.filter(filtres).exists():
                raise serializers.ValidationError("Ce livre est déjà disponible.")

            demandes_ouvertes = DemandeLivre.objects.exclude(
                statut__in=[DemandeLivre.Statut.REFUSE, DemandeLivre.Statut.CLOTUREE]
            )
            if demandes_ouvertes.filter(titre__iexact=titre).filter(
                Q(auteur__iexact=auteur) | Q(auteur="")
            ).exists():
                raise serializers.ValidationError("Une demande similaire est déjà en cours de traitement.")
        return attrs

    def get_statut_label(self, obj):
        return obj.get_statut_display()

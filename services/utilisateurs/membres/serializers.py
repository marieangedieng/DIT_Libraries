from rest_framework import serializers

from .models import UtilisateurBibliotheque


ROLE_PERMISSIONS = {
    UtilisateurBibliotheque.TypeUtilisateur.ETUDIANT: [
        "consulter_livres",
        "emprunter_livres",
        "creer_requetes",
    ],
    UtilisateurBibliotheque.TypeUtilisateur.PROFESSEUR: [
        "consulter_livres",
        "emprunter_livres",
        "creer_requetes",
    ],
    UtilisateurBibliotheque.TypeUtilisateur.GESTIONNAIRE: [
        "consulter_livres",
        "gerer_livres",
        "gerer_requetes",
    ],
    UtilisateurBibliotheque.TypeUtilisateur.ADMIN: [
        "consulter_livres",
        "consulter_statistiques",
        "gerer_utilisateurs",
        "administrer_plateforme",
    ],
}


class UtilisateurSerializer(serializers.ModelSerializer):
    mot_de_passe = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    nom_complet = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = UtilisateurBibliotheque
        fields = "__all__"
        extra_kwargs = {
            "mot_de_passe": {"write_only": True},
        }

    def validate(self, attrs):
        if self.instance is None and not attrs.get("mot_de_passe"):
            raise serializers.ValidationError({"mot_de_passe": "Le mot de passe est obligatoire."})
        return attrs

    def create(self, validated_data):
        raw_password = validated_data.pop("mot_de_passe")
        utilisateur = UtilisateurBibliotheque(**validated_data)
        utilisateur.set_password(raw_password)
        utilisateur.save()
        return utilisateur

    def update(self, instance, validated_data):
        raw_password = validated_data.pop("mot_de_passe", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if raw_password:
            instance.set_password(raw_password)
        instance.save()
        return instance

    def get_nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"

    def get_permissions(self, obj):
        return ROLE_PERMISSIONS.get(obj.type_utilisateur, [])

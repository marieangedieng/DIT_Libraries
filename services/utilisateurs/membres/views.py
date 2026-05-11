from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UtilisateurBibliotheque
from .serializers import UtilisateurSerializer


ROLES_AUTO_INSCRIPTIBLES = {
    UtilisateurBibliotheque.TypeUtilisateur.ETUDIANT,
    UtilisateurBibliotheque.TypeUtilisateur.PROFESSEUR,
}


def extraire_role(request):
    return request.headers.get("X-User-Role", "").strip().lower()


def extraire_utilisateur_id(request):
    try:
        return int(request.headers.get("X-User-Id", "0"))
    except ValueError:
        return 0


def est_admin(request):
    return extraire_role(request) == UtilisateurBibliotheque.TypeUtilisateur.ADMIN


def est_requete_interservice(request):
    return not extraire_role(request) and extraire_utilisateur_id(request) == 0


def peut_acceder_compte(request, utilisateur):
    return est_requete_interservice(request) or est_admin(request) or extraire_utilisateur_id(request) == utilisateur.id


def reponse_interdite():
    return Response(
        {"detail": "Vous n'avez pas les permissions nécessaires pour cette action."},
        status=status.HTTP_403_FORBIDDEN,
    )


class UtilisateurListCreateView(APIView):
    def get(self, request):
        if extraire_role(request) and not est_admin(request):
            return reponse_interdite()

        type_utilisateur = request.query_params.get("type")
        utilisateurs = UtilisateurBibliotheque.objects.all()
        if type_utilisateur:
            utilisateurs = utilisateurs.filter(type_utilisateur=type_utilisateur)
        return Response(UtilisateurSerializer(utilisateurs, many=True).data)

    def post(self, request):
        donnees = request.data.copy()
        role_demande = donnees.get(
            "type_utilisateur",
            UtilisateurBibliotheque.TypeUtilisateur.ETUDIANT,
        )

        if not est_admin(request) and role_demande not in ROLES_AUTO_INSCRIPTIBLES:
            return Response(
                {
                    "detail": (
                        "Seuls les comptes étudiant et professeur peuvent être créés "
                        "depuis l'interface publique."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UtilisateurSerializer(data=donnees)
        serializer.is_valid(raise_exception=True)
        utilisateur = serializer.save()
        return Response(UtilisateurSerializer(utilisateur).data, status=status.HTTP_201_CREATED)


class UtilisateurDetailView(APIView):
    def get_object(self, pk):
        return UtilisateurBibliotheque.objects.filter(pk=pk).first()

    def get(self, request, pk):
        utilisateur = self.get_object(pk)
        if not utilisateur:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if not peut_acceder_compte(request, utilisateur):
            return reponse_interdite()
        return Response(UtilisateurSerializer(utilisateur).data)

    def put(self, request, pk):
        return self._mettre_a_jour(request, pk, partial=False)

    def patch(self, request, pk):
        return self._mettre_a_jour(request, pk, partial=True)

    def _mettre_a_jour(self, request, pk, partial):
        utilisateur = self.get_object(pk)
        if not utilisateur:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if not peut_acceder_compte(request, utilisateur):
            return reponse_interdite()

        donnees = request.data.copy()
        if not est_admin(request):
            donnees.pop("type_utilisateur", None)
            donnees.pop("actif", None)

        serializer = UtilisateurSerializer(utilisateur, data=donnees, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        if not est_admin(request):
            return reponse_interdite()
        utilisateur = self.get_object(pk)
        if not utilisateur:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
        utilisateur.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UtilisateursParTypeView(APIView):
    def get(self, request, type_utilisateur):
        if not est_admin(request):
            return reponse_interdite()
        utilisateurs = UtilisateurBibliotheque.objects.filter(type_utilisateur=type_utilisateur)
        return Response(UtilisateurSerializer(utilisateurs, many=True).data)


class UtilisateursActifsView(APIView):
    def get(self, request):
        if not est_admin(request):
            return reponse_interdite()
        utilisateurs = UtilisateurBibliotheque.objects.filter(actif=True)
        return Response(UtilisateurSerializer(utilisateurs, many=True).data)


class TypesUtilisateurView(APIView):
    def get(self, request):
        types = [
            {"code": code, "libelle": libelle}
            for code, libelle in UtilisateurBibliotheque.TypeUtilisateur.choices
            if est_admin(request) or code in ROLES_AUTO_INSCRIPTIBLES
        ]
        return Response(types)


class ProfilParCarteView(APIView):
    def get(self, request, numero_carte):
        if not est_admin(request):
            return reponse_interdite()
        utilisateur = UtilisateurBibliotheque.objects.filter(numero_carte=numero_carte).first()
        if not utilisateur:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UtilisateurSerializer(utilisateur).data)


class MeView(APIView):
    def get(self, request):
        utilisateur = UtilisateurBibliotheque.objects.filter(pk=extraire_utilisateur_id(request)).first()
        if not utilisateur:
            return Response({"detail": "Utilisateur non authentifié."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(UtilisateurSerializer(utilisateur).data)

    def patch(self, request):
        utilisateur = UtilisateurBibliotheque.objects.filter(pk=extraire_utilisateur_id(request)).first()
        if not utilisateur:
            return Response({"detail": "Utilisateur non authentifié."}, status=status.HTTP_401_UNAUTHORIZED)

        donnees = request.data.copy()
        donnees.pop("type_utilisateur", None)
        donnees.pop("actif", None)

        serializer = UtilisateurSerializer(utilisateur, data=donnees, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ConnexionView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        identifiant = request.data.get("identifiant", "").strip()
        mot_de_passe = request.data.get("mot_de_passe", "")

        if not identifiant or not mot_de_passe:
            return Response(
                {"detail": "Les champs identifiant et mot_de_passe sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        utilisateur = UtilisateurBibliotheque.objects.filter(
            Q(email__iexact=identifiant) | Q(numero_carte__iexact=identifiant)
        ).first()

        if not utilisateur:
            user_model = get_user_model()
            django_user = user_model.objects.filter(username__iexact=identifiant).first()
            if django_user and django_user.check_password(mot_de_passe):
                utilisateur = UtilisateurBibliotheque.objects.filter(email__iexact=django_user.email).first()

        if not utilisateur or not utilisateur.check_password(mot_de_passe):
            return Response(
                {"detail": "Identifiants invalides."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not utilisateur.actif:
            return Response(
                {"detail": "Ce compte est désactivé."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": "Connexion réussie.",
                "utilisateur": UtilisateurSerializer(utilisateur).data,
            }
        )


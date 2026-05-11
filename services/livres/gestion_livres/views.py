from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DemandeLivre, Livre
from .serializers import DemandeLivreSerializer, LivreSerializer


ROLES_GESTION = {"gestionnaire", "admin"}


def extraire_role(request):
    return request.headers.get("X-User-Role", "").strip().lower()


def extraire_utilisateur_id(request):
    try:
        return int(request.headers.get("X-User-Id", "0"))
    except ValueError:
        return 0


def extraire_utilisateur_nom(request):
    return request.headers.get("X-User-Name", "").strip()


def reponse_interdite():
    return Response(
        {"detail": "Vous n'avez pas les permissions nécessaires pour cette action."},
        status=status.HTTP_403_FORBIDDEN,
    )


class LivreListCreateView(APIView):
    def get(self, request):
        livres = Livre.objects.all()
        terme = request.query_params.get("q", "").strip()
        categorie = request.query_params.get("categorie", "").strip()
        disponible = request.query_params.get("disponible", "").strip().lower()
        limite = request.query_params.get("limite")
        tri = request.query_params.get("tri", "").strip().lower()

        if terme:
            livres = livres.filter(
                Q(titre__icontains=terme)
                | Q(auteur__icontains=terme)
                | Q(isbn__icontains=terme)
                | Q(categorie__icontains=terme)
            )

        if categorie:
            livres = livres.filter(categorie__icontains=categorie)

        if disponible in {"1", "true", "oui"}:
            livres = livres.filter(quantite_disponible__gt=0, actif=True)

        if tri == "recents":
            livres = livres.order_by("-cree_le")

        if limite:
            try:
                livres = livres[: max(1, int(limite))]
            except ValueError:
                pass

        return Response(LivreSerializer(livres, many=True).data)

    def post(self, request):
        if extraire_role(request) not in ROLES_GESTION:
            return reponse_interdite()
        serializer = LivreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        livre = serializer.save()
        return Response(LivreSerializer(livre).data, status=status.HTTP_201_CREATED)


class LivreDetailView(APIView):
    def get_object(self, pk):
        return Livre.objects.filter(pk=pk).first()

    def get(self, _request, pk):
        livre = self.get_object(pk)
        if not livre:
            return Response({"detail": "Livre introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(LivreSerializer(livre).data)

    def put(self, request, pk):
        return self._mettre_a_jour(request, pk, partial=False)

    def patch(self, request, pk):
        return self._mettre_a_jour(request, pk, partial=True)

    def _mettre_a_jour(self, request, pk, partial):
        if extraire_role(request) not in ROLES_GESTION:
            return reponse_interdite()
        livre = self.get_object(pk)
        if not livre:
            return Response({"detail": "Livre introuvable."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LivreSerializer(livre, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        if extraire_role(request) not in ROLES_GESTION:
            return reponse_interdite()
        livre = self.get_object(pk)
        if not livre:
            return Response({"detail": "Livre introuvable."}, status=status.HTTP_404_NOT_FOUND)
        livre.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RechercheLivresView(APIView):
    def get(self, request):
        terme = request.query_params.get("q", "").strip()
        livres = Livre.objects.all()
        if terme:
            livres = livres.filter(
                Q(titre__icontains=terme)
                | Q(auteur__icontains=terme)
                | Q(isbn__icontains=terme)
                | Q(categorie__icontains=terme)
            )
        return Response(LivreSerializer(livres, many=True).data)


class LivresDisponiblesView(APIView):
    def get(self, _request):
        livres = Livre.objects.filter(quantite_disponible__gt=0, actif=True)
        return Response(LivreSerializer(livres, many=True).data)


class LivresRecentsView(APIView):
    def get(self, request):
        limite = request.query_params.get("limite", "8")
        try:
            limite_int = max(1, int(limite))
        except ValueError:
            limite_int = 8
        livres = Livre.objects.order_by("-cree_le")[:limite_int]
        return Response(LivreSerializer(livres, many=True).data)


class LivreParIsbnView(APIView):
    def get(self, _request, isbn):
        livre = Livre.objects.filter(isbn=isbn).first()
        if not livre:
            return Response({"detail": "Livre introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(LivreSerializer(livre).data)


class MettreAJourStockView(APIView):
    def post(self, request, pk):
        livre = Livre.objects.filter(pk=pk).first()
        if not livre:
            return Response({"detail": "Livre introuvable."}, status=status.HTTP_404_NOT_FOUND)

        delta = int(request.data.get("delta", 0))
        nouvelle_quantite = livre.quantite_disponible + delta

        if nouvelle_quantite < 0 or nouvelle_quantite > livre.quantite_totale:
            return Response(
                {"detail": "Le stock demandé est invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        livre.quantite_disponible = nouvelle_quantite
        livre.save(update_fields=["quantite_disponible", "modifie_le"])
        return Response(LivreSerializer(livre).data)


class DemandeLivreListCreateView(APIView):
    def get(self, request):
        role = extraire_role(request)
        utilisateur_id = extraire_utilisateur_id(request)

        if role in ROLES_GESTION:
            demandes = DemandeLivre.objects.all()
        elif utilisateur_id:
            demandes = DemandeLivre.objects.filter(utilisateur_id=utilisateur_id)
        else:
            return Response({"detail": "Utilisateur non authentifié."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(DemandeLivreSerializer(demandes, many=True).data)

    def post(self, request):
        utilisateur_id = extraire_utilisateur_id(request)
        utilisateur_nom = extraire_utilisateur_nom(request)
        role = extraire_role(request)

        if role not in {"etudiant", "professeur", "gestionnaire", "admin"} or not utilisateur_id:
            return Response(
                {"detail": "Vous devez être connecté pour soumettre une requête."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        donnees = request.data.copy()
        donnees["utilisateur_id"] = utilisateur_id
        donnees["utilisateur_nom"] = utilisateur_nom or request.data.get("utilisateur_nom", "")

        serializer = DemandeLivreSerializer(data=donnees)
        serializer.is_valid(raise_exception=True)
        demande = serializer.save()
        return Response(DemandeLivreSerializer(demande).data, status=status.HTTP_201_CREATED)


class DemandeLivreDetailView(APIView):
    def get_object(self, pk):
        return DemandeLivre.objects.filter(pk=pk).first()

    def patch(self, request, pk):
        if extraire_role(request) not in ROLES_GESTION:
            return reponse_interdite()

        demande = self.get_object(pk)
        if not demande:
            return Response({"detail": "Requête introuvable."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DemandeLivreSerializer(demande, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if instance.statut in {
            DemandeLivre.Statut.REFUSE,
            DemandeLivre.Statut.LIVRE_DISPONIBLE,
            DemandeLivre.Statut.CLOTUREE,
        }:
            instance.fermee_le = timezone.now()
        else:
            instance.fermee_le = None
        instance.save(update_fields=["fermee_le", "modifie_le"])

        return Response(DemandeLivreSerializer(instance).data)

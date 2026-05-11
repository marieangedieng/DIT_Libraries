import csv
import io
import os

import requests
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Emprunt
from .serializers import EmpruntSerializer


SERVICE_LIVRES_URL = os.getenv("SERVICE_LIVRES_URL", "http://localhost:8001")
SERVICE_UTILISATEURS_URL = os.getenv("SERVICE_UTILISATEURS_URL", "http://localhost:8002")
ROLES_LECTEURS = {"etudiant", "professeur"}
ROLES_GESTION = {"gestionnaire", "admin"}


def extraire_role(request):
    return request.headers.get("X-User-Role", "").strip().lower()


def extraire_utilisateur_id(request):
    try:
        return int(request.headers.get("X-User-Id", "0"))
    except ValueError:
        return 0


def reponse_interdite():
    return Response(
        {"detail": "Vous n'avez pas les permissions nécessaires pour cette action."},
        status=status.HTTP_403_FORBIDDEN,
    )


def recuperer_livre(livre_id):
    response = requests.get(f"{SERVICE_LIVRES_URL}/api/livres/{livre_id}/", timeout=5)
    if response.status_code != 200:
        return None
    return response.json()


def recuperer_utilisateur(utilisateur_id):
    response = requests.get(f"{SERVICE_UTILISATEURS_URL}/api/utilisateurs/{utilisateur_id}/", timeout=5)
    if response.status_code != 200:
        return None
    return response.json()


def ajuster_stock(livre_id, delta):
    response = requests.post(
        f"{SERVICE_LIVRES_URL}/api/livres/{livre_id}/stock/",
        json={"delta": delta},
        timeout=5,
    )
    return response.status_code < 400


class EmpruntListCreateView(APIView):
    def get(self, request):
        role = extraire_role(request)
        utilisateur_id = extraire_utilisateur_id(request)

        emprunts = Emprunt.objects.all()
        if role in ROLES_LECTEURS and utilisateur_id:
            emprunts = emprunts.filter(utilisateur_id=utilisateur_id)
        return Response(EmpruntSerializer(emprunts, many=True).data)

    def post(self, request):
        role = extraire_role(request)
        utilisateur_id = request.data.get("utilisateur_id")
        livre_id = request.data.get("livre_id")

        if role not in ROLES_LECTEURS:
            return reponse_interdite()

        if not utilisateur_id or not livre_id:
            return Response(
                {"detail": "Les champs utilisateur_id et livre_id sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if extraire_utilisateur_id(request) != int(utilisateur_id):
            return Response(
                {"detail": "Vous ne pouvez emprunter des livres que pour votre propre compte."},
                status=status.HTTP_403_FORBIDDEN,
            )

        utilisateur = recuperer_utilisateur(utilisateur_id)
        if not utilisateur:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_400_BAD_REQUEST)

        livre = recuperer_livre(livre_id)
        if not livre:
            return Response({"detail": "Livre introuvable."}, status=status.HTTP_400_BAD_REQUEST)

        if livre.get("quantite_disponible", 0) <= 0:
            return Response({"detail": "Aucun exemplaire disponible."}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "utilisateur_id": utilisateur["id"],
            "utilisateur_nom": utilisateur["nom_complet"],
            "livre_id": livre["id"],
            "livre_titre": livre["titre"],
            "date_retour_prevue": request.data.get("date_retour_prevue"),
            "commentaire": request.data.get("commentaire", ""),
        }
        serializer = EmpruntSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        emprunt = serializer.save()

        if not ajuster_stock(livre["id"], -1):
            emprunt.delete()
            return Response(
                {"detail": "Impossible de mettre à jour le stock du livre."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(EmpruntSerializer(emprunt).data, status=status.HTTP_201_CREATED)


class EmpruntDetailView(APIView):
    def get_object(self, pk):
        return Emprunt.objects.filter(pk=pk).first()

    def get(self, _request, pk):
        emprunt = self.get_object(pk)
        if not emprunt:
            return Response({"detail": "Emprunt introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmpruntSerializer(emprunt).data)

    def delete(self, _request, pk):
        emprunt = self.get_object(pk)
        if not emprunt:
            return Response({"detail": "Emprunt introuvable."}, status=status.HTTP_404_NOT_FOUND)
        emprunt.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarquerRetourView(APIView):
    def post(self, request, pk):
        emprunt = Emprunt.objects.filter(pk=pk).first()
        if not emprunt:
            return Response({"detail": "Emprunt introuvable."}, status=status.HTTP_404_NOT_FOUND)

        role = extraire_role(request)
        utilisateur_id = extraire_utilisateur_id(request)
        if role not in ROLES_GESTION and utilisateur_id != emprunt.utilisateur_id:
            return reponse_interdite()

        if emprunt.statut == Emprunt.Statut.RETOURNE:
            return Response({"detail": "Cet emprunt est déjà clôturé."}, status=status.HTTP_400_BAD_REQUEST)

        emprunt.date_retour_effective = request.data.get("date_retour_effective", timezone.now().date())
        emprunt.statut = (
            Emprunt.Statut.EN_RETARD
            if emprunt.date_retour_effective > emprunt.date_retour_prevue
            else Emprunt.Statut.RETOURNE
        )
        emprunt.save(update_fields=["date_retour_effective", "statut", "modifie_le"])

        if not ajuster_stock(emprunt.livre_id, 1):
            return Response(
                {"detail": "Retour enregistré, mais impossible de restaurer le stock."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(EmpruntSerializer(emprunt).data)


class HistoriqueUtilisateurView(APIView):
    def get(self, request, utilisateur_id):
        role = extraire_role(request)
        requete_utilisateur_id = extraire_utilisateur_id(request)
        if role in ROLES_LECTEURS and requete_utilisateur_id != utilisateur_id:
            return reponse_interdite()
        emprunts = Emprunt.objects.filter(utilisateur_id=utilisateur_id)
        return Response(EmpruntSerializer(emprunts, many=True).data)


class RetardsView(APIView):
    def get(self, _request):
        aujourd_hui = timezone.now().date()
        emprunts = Emprunt.objects.filter(statut=Emprunt.Statut.EN_COURS, date_retour_prevue__lt=aujourd_hui)
        donnees = EmpruntSerializer(emprunts, many=True).data
        return Response(donnees)


class ExportHistoriqueCsvView(APIView):
    def get(self, _request):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "utilisateur_id",
                "utilisateur_nom",
                "livre_id",
                "livre_titre",
                "date_emprunt",
                "date_retour_prevue",
                "date_retour_effective",
                "statut",
            ]
        )

        for emprunt in Emprunt.objects.all():
            writer.writerow(
                [
                    emprunt.utilisateur_id,
                    emprunt.utilisateur_nom,
                    emprunt.livre_id,
                    emprunt.livre_titre,
                    emprunt.date_emprunt,
                    emprunt.date_retour_prevue,
                    emprunt.date_retour_effective or "",
                    emprunt.statut,
                ]
            )

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="loans.csv"'
        return response

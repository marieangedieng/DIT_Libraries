from collections import Counter
import os

import requests
from requests import RequestException
from rest_framework.response import Response
from rest_framework.views import APIView


SERVICE_LIVRES_URL = os.getenv("SERVICE_LIVRES_URL", "http://localhost:8001")
SERVICE_UTILISATEURS_URL = os.getenv("SERVICE_UTILISATEURS_URL", "http://localhost:8002")
SERVICE_EMPRUNTS_URL = os.getenv("SERVICE_EMPRUNTS_URL", "http://localhost:8003")
ROLE_ADMIN = "admin"


def extraire_role(request):
    return request.headers.get("X-User-Role", "").strip().lower()


def verifier_admin(request):
    if extraire_role(request) != ROLE_ADMIN:
        return Response(
            {"detail": "Cette section est réservée aux administrateurs."},
            status=403,
        )
    return None


def recuperer_json(url, default):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json(), None
    except RequestException as exc:
        return default, str(exc)


class TableauDeBordView(APIView):
    def get(self, request):
        erreur = verifier_admin(request)
        if erreur:
            return erreur

        livres, err_livres = recuperer_json(f"{SERVICE_LIVRES_URL}/api/livres/", [])
        utilisateurs, err_utilisateurs = recuperer_json(f"{SERVICE_UTILISATEURS_URL}/api/utilisateurs/", [])
        emprunts, err_emprunts = recuperer_json(f"{SERVICE_EMPRUNTS_URL}/api/emprunts/", [])
        retards, err_retards = recuperer_json(f"{SERVICE_EMPRUNTS_URL}/api/emprunts/retards/", [])
        erreurs = [err for err in [err_livres, err_utilisateurs, err_emprunts, err_retards] if err]

        return Response(
            {
                "nombre_livres": len(livres),
                "nombre_utilisateurs": len(utilisateurs),
                "nombre_emprunts": len(emprunts),
                "nombre_retards": len(retards),
                "livres_disponibles": sum(1 for livre in livres if livre["quantite_disponible"] > 0),
                "emprunts_en_cours": sum(1 for emprunt in emprunts if emprunt["statut"] == "en_cours"),
                "services_indisponibles": len(erreurs),
                "erreurs": erreurs,
            }
        )


class TopLivresView(APIView):
    def get(self, request):
        erreur = verifier_admin(request)
        if erreur:
            return erreur

        emprunts, _ = recuperer_json(f"{SERVICE_EMPRUNTS_URL}/api/emprunts/", [])
        compteur = Counter(emprunt["livre_titre"] for emprunt in emprunts)
        top = [{"livre": titre, "total": total} for titre, total in compteur.most_common(5)]
        return Response(top)


class RepartitionUtilisateursView(APIView):
    def get(self, request):
        erreur = verifier_admin(request)
        if erreur:
            return erreur

        utilisateurs, _ = recuperer_json(f"{SERVICE_UTILISATEURS_URL}/api/utilisateurs/", [])
        compteur = Counter(utilisateur["type_utilisateur"] for utilisateur in utilisateurs)
        repartition = [{"type_utilisateur": cle, "total": valeur} for cle, valeur in compteur.items()]
        return Response(repartition)


class ListeRetardsView(APIView):
    def get(self, request):
        erreur = verifier_admin(request)
        if erreur:
            return erreur

        retards, _ = recuperer_json(f"{SERVICE_EMPRUNTS_URL}/api/emprunts/retards/", [])
        return Response(retards)


class SanteServicesView(APIView):
    def get(self, request):
        erreur = verifier_admin(request)
        if erreur:
            return erreur

        etats = {}
        for nom, url in {
            "livres": SERVICE_LIVRES_URL,
            "utilisateurs": SERVICE_UTILISATEURS_URL,
            "emprunts": SERVICE_EMPRUNTS_URL,
        }.items():
            try:
                response = requests.get(url, timeout=5)
                etats[nom] = "ok" if response.status_code < 400 else "erreur"
            except RequestException:
                etats[nom] = "indisponible"
        return Response(etats)

from django.urls import path

from .views import (
    ConnexionView,
    MeView,
    ProfilParCarteView,
    TypesUtilisateurView,
    UtilisateurDetailView,
    UtilisateurListCreateView,
    UtilisateursActifsView,
    UtilisateursParTypeView,
)


urlpatterns = [
    path("utilisateurs/connexion/", ConnexionView.as_view(), name="utilisateurs-connexion"),
    path("utilisateurs/", UtilisateurListCreateView.as_view(), name="utilisateurs-liste-creation"),
    path("utilisateurs/me/", MeView.as_view(), name="utilisateurs-me"),
    path("utilisateurs/actifs/", UtilisateursActifsView.as_view(), name="utilisateurs-actifs"),
    path("utilisateurs/types/", TypesUtilisateurView.as_view(), name="utilisateurs-types"),
    path("utilisateurs/type/<str:type_utilisateur>/", UtilisateursParTypeView.as_view(), name="utilisateurs-par-type"),
    path("utilisateurs/carte/<str:numero_carte>/", ProfilParCarteView.as_view(), name="utilisateurs-par-carte"),
    path("utilisateurs/<int:pk>/", UtilisateurDetailView.as_view(), name="utilisateurs-detail"),
]

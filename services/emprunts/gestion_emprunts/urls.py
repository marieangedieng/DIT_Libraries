from django.urls import path

from .views import (
    EmpruntDetailView,
    EmpruntListCreateView,
    ExportHistoriqueCsvView,
    HistoriqueUtilisateurView,
    MarquerRetourView,
    RetardsView,
)


urlpatterns = [
    path("emprunts/", EmpruntListCreateView.as_view(), name="emprunts-liste-creation"),
    path("emprunts/retards/", RetardsView.as_view(), name="emprunts-retards"),
    path("emprunts/export/csv/", ExportHistoriqueCsvView.as_view(), name="emprunts-export-csv"),
    path("emprunts/utilisateur/<int:utilisateur_id>/", HistoriqueUtilisateurView.as_view(), name="emprunts-historique-utilisateur"),
    path("emprunts/<int:pk>/", EmpruntDetailView.as_view(), name="emprunts-detail"),
    path("emprunts/<int:pk>/retour/", MarquerRetourView.as_view(), name="emprunts-retour"),
]

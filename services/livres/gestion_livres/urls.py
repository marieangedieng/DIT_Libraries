from django.urls import path

from .views import (
    DemandeLivreDetailView,
    DemandeLivreListCreateView,
    LivreDetailView,
    LivreListCreateView,
    LivreParIsbnView,
    LivresDisponiblesView,
    LivresRecentsView,
    MettreAJourStockView,
    RechercheLivresView,
)


urlpatterns = [
    path("livres/", LivreListCreateView.as_view(), name="livres-liste-creation"),
    path("livres/disponibles/", LivresDisponiblesView.as_view(), name="livres-disponibles"),
    path("livres/recents/", LivresRecentsView.as_view(), name="livres-recents"),
    path("livres/recherche/", RechercheLivresView.as_view(), name="livres-recherche"),
    path("livres/isbn/<str:isbn>/", LivreParIsbnView.as_view(), name="livres-par-isbn"),
    path("livres/<int:pk>/", LivreDetailView.as_view(), name="livres-detail"),
    path("livres/<int:pk>/stock/", MettreAJourStockView.as_view(), name="livres-stock"),
    path("demandes-livres/", DemandeLivreListCreateView.as_view(), name="demandes-livres"),
    path("demandes-livres/<int:pk>/", DemandeLivreDetailView.as_view(), name="demandes-livres-detail"),
]

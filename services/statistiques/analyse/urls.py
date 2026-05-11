from django.urls import path

from .views import (
    ListeRetardsView,
    RepartitionUtilisateursView,
    SanteServicesView,
    TableauDeBordView,
    TopLivresView,
)


urlpatterns = [
    path("statistiques/tableau-de-bord/", TableauDeBordView.as_view(), name="tableau-de-bord"),
    path("statistiques/top-livres/", TopLivresView.as_view(), name="top-livres"),
    path("statistiques/repartition-utilisateurs/", RepartitionUtilisateursView.as_view(), name="repartition-utilisateurs"),
    path("statistiques/retards/", ListeRetardsView.as_view(), name="retards"),
    path("statistiques/sante-services/", SanteServicesView.as_view(), name="sante-services"),
]

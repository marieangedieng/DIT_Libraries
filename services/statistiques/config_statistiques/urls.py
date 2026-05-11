from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def accueil(_request):
    return JsonResponse(
        {
            "service": "statistiques",
            "statut": "ok",
            "message": "Service Statistiques opérationnel",
        }
    )


urlpatterns = [
    path("", accueil),
    path("admin/", admin.site.urls),
    path("api/", include("analyse.urls")),
]

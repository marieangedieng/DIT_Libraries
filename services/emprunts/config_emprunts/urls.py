from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def accueil(_request):
    return JsonResponse(
        {
            "service": "emprunts",
            "statut": "ok",
            "message": "Service Emprunts opérationnel",
        }
    )


urlpatterns = [
    path("", accueil),
    path("admin/", admin.site.urls),
    path("api/", include("gestion_emprunts.urls")),
]

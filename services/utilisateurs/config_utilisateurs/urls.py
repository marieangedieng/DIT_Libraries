from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def accueil(_request):
    return JsonResponse(
        {
            "service": "utilisateurs",
            "statut": "ok",
            "message": "Service Utilisateurs opérationnel",
        }
    )


urlpatterns = [
    path("", accueil),
    path("admin/", admin.site.urls),
    path("api/", include("membres.urls")),
]

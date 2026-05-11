from rest_framework import serializers
from django.utils import timezone

from .models import Emprunt


class EmpruntSerializer(serializers.ModelSerializer):
    en_retard = serializers.SerializerMethodField()

    class Meta:
        model = Emprunt
        fields = "__all__"

    def get_en_retard(self, obj):
        if obj.date_retour_effective:
            return obj.date_retour_effective > obj.date_retour_prevue
        return obj.date_retour_prevue < timezone.now().date()

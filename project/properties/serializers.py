from rest_framework import serializers

from .models import Room


class RoomConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = (
            "allow_co_tenant",
            "co_tenant_maximum",
        )

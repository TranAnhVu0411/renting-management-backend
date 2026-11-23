from rest_framework import serializers

from .models import Room, RoomMeter


class RoomConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = (
            "has_water_meter",
            "allow_co_tenant",
            "co_tenant_maximum",
        )


class RoomMetersSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMeter
        fields = (
            "id",
            "meter_type",
            "meter_id",
        )

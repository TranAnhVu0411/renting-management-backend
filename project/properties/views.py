from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissions

from .models import Room, RoomMeter
from .serializers import RoomConditionsSerializer, RoomMetersSerializer


class RoomConditionsAPIView(RetrieveAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomConditionsSerializer
    permission_classes = [DjangoModelPermissions]


class RoomMetersAPIView(ListAPIView):
    serializer_class = RoomMetersSerializer
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        return RoomMeter.objects.filter(
            room_id=self.kwargs["pk"],
        ).order_by(
            "meter_type",
            "meter_id",
        )

from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissions

from .models import Room
from .serializers import RoomConditionsSerializer


class RoomConditionsAPIView(RetrieveAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomConditionsSerializer
    permission_classes = [DjangoModelPermissions]

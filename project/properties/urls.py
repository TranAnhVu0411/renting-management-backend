from django.urls import path

from .views import RoomConditionsAPIView, RoomMetersAPIView

app_name = "properties"

urlpatterns = [
    path(
        "rooms/<uuid:pk>/conditions/",
        RoomConditionsAPIView.as_view(),
        name="room-conditions",
    ),
    path(
        "rooms/<uuid:pk>/meters/",
        RoomMetersAPIView.as_view(),
        name="room-meters",
    ),
]

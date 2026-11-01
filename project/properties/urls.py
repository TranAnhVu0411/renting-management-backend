from django.urls import path

from .views import RoomConditionsAPIView

app_name = "properties"

urlpatterns = [
    path(
        "rooms/<str:pk>/conditions/",
        RoomConditionsAPIView.as_view(),
        name="room-conditions",
    ),
]

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Room


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = (
        "room_id",
        "allow_co_tenant",
        "co_tenant_maximum",
        "area",
        "status",
    )
    list_filter = ("status",)
    search_fields = ("room_id",)
    conditional_fields = {"co_tenant_maximum": "allow_co_tenant == true"}
    fieldsets = (
        (None, {"fields": ("room_id", "area")}),
        (
            "Thông tin ở ghép",
            {
                "fields": (
                    "allow_co_tenant",
                    "co_tenant_maximum",
                )
            },
        ),
        (
            "Hệ thống",
            {
                "fields": ("status",),
                "classes": ("collapse",),
            },
        ),
    )

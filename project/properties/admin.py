from django import forms
from django.contrib import admin
from django.urls import reverse
from django.shortcuts import redirect
from unfold.admin import ModelAdmin
from unfold.decorators import action

from .models import Room


class RoomAdminForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        area = cleaned_data.get("area")
        if area is not None and area <= 0:
            self.add_error(
                "area",
                "Area must be greater than 0.",
            )

        allow_co_tenant = cleaned_data.get("allow_co_tenant")
        co_tenant_maximum = cleaned_data.get("co_tenant_maximum")

        if allow_co_tenant and co_tenant_maximum == 0:
            self.add_error(
                "co_tenant_maximum",
                "Co-tenant maximum must be greater than 0 "
                "when co-tenants are allowed.",
            )

        if not allow_co_tenant:
            cleaned_data["co_tenant_maximum"] = 0

        return cleaned_data


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
    actions_row = ["delete_room_row"]
    form = RoomAdminForm
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

    @action(
        description="Delete room",
        icon="delete_forever",
    )
    def delete_room_row(self, request, object_id):
        room = Room.objects.get(pk=object_id)
        room.delete()

        return redirect(reverse("admin:properties_room_changelist"))

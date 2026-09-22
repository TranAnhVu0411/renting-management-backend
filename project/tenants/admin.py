from django.contrib import admin
from .models import Tenant


@admin.action(description="Deactivate tenant")
def deactivate_tenant(modeladmin, request, queryset):
    queryset.update(active=False)


@admin.action(description="Activate tenant")
def activate_tenant(modeladmin, request, queryset):
    queryset.update(active=True)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "identity_card_number",
        "phone_number",
        "active",
    )
    list_filter = ("active",)
    search_fields = ("name", "identity_card_number", "phone_number")
    actions = [deactivate_tenant, activate_tenant]
    fieldsets = (
        (None, {"fields": ("name", "identity_card_number", "phone_number")}),
        (
            "CCCD/CMND",
            {"fields": ("identity_card_created_date", "identity_card_created_place")},
        ),
        ("Địa chỉ", {"fields": ("permanent_address",)}),
        (
            "Hệ thống",
            {
                "fields": ("active",),
                "classes": ("collapse",),
            },
        ),
    )

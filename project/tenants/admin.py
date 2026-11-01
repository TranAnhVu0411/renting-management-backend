from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin
from unfold.decorators import action

from .models import Tenant


@admin.action(description="Deactivate tenant")
def deactivate_tenant_bulk(modeladmin, request, queryset):
    queryset.update(active=False)


@admin.action(description="Activate tenant")
def activate_tenant_bulk(modeladmin, request, queryset):
    queryset.update(active=True)


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = (
        "name",
        "identity_card_number",
        "phone_number",
        "active",
    )
    list_filter = ("active",)
    search_fields = ("name", "identity_card_number", "phone_number")
    actions = [deactivate_tenant_bulk, activate_tenant_bulk]
    actions_row = ["update_tenant_status_row", "delete_tenant_row"]
    fieldsets = (
        (None, {"fields": ("name", "phone_number", "permanent_address")}),
        (
            "CCCD/CMND",
            {
                "fields": (
                    "identity_card_number",
                    "identity_card_created_date",
                    "identity_card_created_place",
                )
            },
        ),
        (
            "Hệ thống",
            {
                "fields": ("active",),
                "classes": ("collapse",),
            },
        ),
    )

    @action(description="Update tenant status", icon="sync_alt")
    def update_tenant_status_row(self, request, object_id):
        tenant = Tenant.objects.get(pk=object_id)
        tenant.active = not tenant.active
        tenant.save(update_fields=["active"])

        return redirect(reverse("admin:tenants_tenant_changelist"))

    @action(
        description="Delete tenant",
        icon="delete_forever",
    )
    def delete_tenant_row(self, request, object_id):
        tenant = Tenant.objects.get(pk=object_id)
        tenant.delete()

        return redirect(reverse("admin:tenants_tenant_changelist"))

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request,
            queryset,
            search_term,
        )

        if (
            request.GET.get("app_label") == "contracts"
            and request.GET.get("model_name") == "tenancytenant"
            and request.GET.get("field_name") == "tenant"
        ):
            queryset = queryset.filter(active=True)

            raw_ids = request.GET.get("exclude_tenant_ids", "")
            tenant_ids = []

            for value in raw_ids.split(","):
                if not value:
                    continue

                try:
                    tenant_ids.append(
                        Tenant._meta.pk.to_python(value)
                    )
                except (ValidationError, ValueError, TypeError):
                    continue

            if tenant_ids:
                queryset = queryset.exclude(pk__in=tenant_ids)

        return queryset, may_have_duplicates

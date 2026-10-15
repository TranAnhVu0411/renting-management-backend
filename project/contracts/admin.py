from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.contrib.forms.widgets import ArrayWidget

from .models import Tenancy, TenancyTenant, TenancyService


class TenancyTenantInline(TabularInline):
    model = TenancyTenant
    extra = 1
    autocomplete_fields = ("tenant",)
    fields = ("tenant", "role", "active")
    show_change_link = True


class TenancyServiceInline(StackedInline):
    model = TenancyService
    can_delete = False
    show_change_link = False
    show_title = False

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "rent_price",
                    "electricity_price",
                    "water_price",
                ]
            },
        ),
        (
            "Dịch vụ",
            {
                "fields": [
                    ("laundry", "laundry_price"),
                    ("parking", "parking_price"),
                    ("internet", "internet_price"),
                    ("cleaner", "cleaner_price"),
                ]
            },
        ),
    ]

    class Media:
        js = ("admin/js/tenancy_service_inline.js",)


@admin.register(Tenancy)
class TenancyAdmin(ModelAdmin):
    formfield_overrides = {
        ArrayField: {
            "widget": ArrayWidget,
        }
    }

    list_display = (
        "tenant",
        "room",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status",)
    search_fields = (
        "tenant__name",
        "room__room_id",
    )

    fields = (
        ("tenant", "room"),
        "vehicle_plate_numbers",
        ("start_date", "end_date"),
        "status",
    )

    inlines = [
        TenancyTenantInline,
        TenancyServiceInline,
    ]

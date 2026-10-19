from django import forms
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.contrib.forms.widgets import ArrayWidget

from .models import Tenancy, TenancyTenant, TenancyService


class TenancyTenantInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        primary_count = 0
        is_primary_tenant_active = False
        active_count = 0

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if not form.cleaned_data:
                continue

            tenant = form.cleaned_data.get("tenant")
            role = form.cleaned_data.get("role")
            active = form.cleaned_data.get("active")

            if tenant and role == "primary":
                primary_count += 1
                if active:
                    is_primary_tenant_active = True
            if active:
                active_count += 1

        if primary_count == 0:
            raise ValidationError("One Tenancy must have one primary tenant.")

        if primary_count > 1:
            raise ValidationError("One Tenancy can only have one primary tenant.")

        if active_count == 0:
            raise ValidationError("One Tenancy must have at least one active tenant.")

        if not is_primary_tenant_active:
            raise ValidationError("The primary tenant must be active.")


class TenancyTenantInline(TabularInline):
    model = TenancyTenant
    formset = TenancyTenantInlineFormSet
    extra = 1
    autocomplete_fields = ("tenant",)
    fields = ("tenant", "role", "active")
    show_change_link = True


class TenancyServiceInlineForm(forms.ModelForm):
    class Meta:
        model = TenancyService
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("laundry"):
            cleaned_data["laundry_price"] = None
        if not cleaned_data.get("parking"):
            cleaned_data["parking_price"] = None
        if not cleaned_data.get("internet"):
            cleaned_data["internet_price"] = None
        if not cleaned_data.get("cleaner"):
            cleaned_data["cleaner_price"] = None

        return cleaned_data


class TenancyServiceInline(StackedInline):
    model = TenancyService
    form = TenancyServiceInlineForm
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


class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_date",
                "End date must be after start date.",
            )

        return cleaned_data


@admin.register(Tenancy)
class TenancyAdmin(ModelAdmin):
    form = TenancyForm
    inlines = [
        TenancyTenantInline,
        TenancyServiceInline,
    ]
    list_display = (
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
        "room",
        "vehicle_plate_numbers",
        ("start_date", "end_date"),
        "status",
    )
    formfield_overrides = {
        ArrayField: {
            "widget": ArrayWidget,
        }
    }

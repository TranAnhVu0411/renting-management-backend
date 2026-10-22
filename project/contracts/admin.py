from django import forms
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.contrib.forms.widgets import ArrayWidget

from .models import Tenancy, TenancyTenant, TenancyService
from properties.models import Room


class TenancyTenantInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        primary_count = 0
        cotenant_count = 0
        is_primary_tenant_active = False
        active_count = 0

        room_id = self.data.get("room")
        if not room_id:
            room_id = getattr(self.instance, "room_id", None)
        try:
            room = Room.objects.get(pk=room_id)
        except (Room.DoesNotExist, ValueError, TypeError):
            return

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if not form.cleaned_data:
                continue

            data = form.cleaned_data
            if not data or not data.get("tenant"):
                continue

            role = form.cleaned_data.get("role")
            active = form.cleaned_data.get("active")

            if role == "primary":
                primary_count += 1
                if active:
                    is_primary_tenant_active = True
            if role == "co-tenant":
                cotenant_count += 1
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

        if room.allow_co_tenant:
            if cotenant_count > room.co_tenant_maximum:
                raise ValidationError(
                    f"Co-tenants cannot exceed the maximum of {room.co_tenant_maximum} for this room."
                )
        else:
            if cotenant_count > 0:
                raise ValidationError("Co-tenants are not allowed for this room.")


class TenancyTenantInline(TabularInline):
    model = TenancyTenant
    formset = TenancyTenantInlineFormSet
    extra = 1
    autocomplete_fields = ("tenant",)
    fields = ("tenant", "role", "active")
    show_change_link = True
    show_title = False


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
    change_form_before_template = ("admin/tenancy/room_conditions.html",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "room":
            kwargs["queryset"] = Room.objects.filter(status="empty")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        js = ("admin/js/room_condition.js",)

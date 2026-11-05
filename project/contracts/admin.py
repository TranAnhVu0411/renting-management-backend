from django import forms
from django.db.models import Q
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.contrib.forms.widgets import ArrayWidget

from .models import ServicePriceRule, Tenancy, TenancyTenant, TenancyService
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
        seen_tenant_ids = set()

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if not form.cleaned_data:
                continue

            data = form.cleaned_data
            tenant = data.get("tenant")
            if not tenant:
                continue

            if tenant.pk in seen_tenant_ids:
                form.add_error(
                    "tenant",
                    ValidationError(
                        "This tenant has already been selected " "in another line."
                    ),
                )
            else:
                seen_tenant_ids.add(tenant.pk)

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

        room_id = self.data.get("room")
        if not room_id:
            room_id = getattr(self.instance, "room_id", None)
        try:
            room = Room.objects.get(pk=room_id)
        except (Room.DoesNotExist, ValueError, TypeError):
            return
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

    class Media:
        js = ("admin/js/tenancy_tenant_autocomplete.js",)


class TenancyServiceInlineForm(forms.ModelForm):
    class Meta:
        model = TenancyService
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        is_water_flat_fee = self.initial.get(
            "is_water_flat_fee",
            self.instance.is_water_flat_fee,
        )

        self.fields["water_price"].help_text = (
            "Giá nước (khoán)" if is_water_flat_fee else "Giá nước (theo m3)"
        )

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


class TenancyServiceInlineFormSet(forms.models.BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)

        if i == 0:
            form.empty_permitted = False

        return form


class TenancyServiceInline(StackedInline):
    model = TenancyService
    form = TenancyServiceInlineForm
    formset = TenancyServiceInlineFormSet
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
                    ("is_water_flat_fee", "water_price"),
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
        "primary_tenant",
        "room",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status",)
    search_fields = (
        "tenants__tenant__name",
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.prefetch_related("tenants")

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request,
            queryset,
            search_term,
        )

        primary_tenant_ids = TenancyTenant.objects.filter(
            role="primary",
            tenant__name__icontains=search_term,
        ).values_list("tenancy_id", flat=True)

        primary_room_ids = Room.objects.filter(
            room_id__icontains=search_term,
        ).values_list("id", flat=True)

        queryset = Tenancy.objects.filter(
            Q(id__in=queryset.values("id"))
            & (Q(id__in=primary_tenant_ids) | Q(room_id__in=primary_room_ids))
        )

        return queryset, may_have_duplicates

    @admin.display(description="Primary Tenant")
    def primary_tenant(self, obj):
        for tenancy_tenant in obj.tenants.all():
            if tenancy_tenant.role == "primary":
                return tenancy_tenant.tenant

        return "-"

    class Media:
        js = ("admin/js/room_condition.js",)


@admin.register(ServicePriceRule)
class ServicePriceRuleAdmin(ModelAdmin):
    list_display = (
        "electric_price",
        "water_price",
        "water_flat_fee",
        "parking_price",
        "laundry_price",
        "internet_price",
        "cleaner_price",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

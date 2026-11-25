from django import forms
from django.db.models import Q
from django.contrib import admin
from django.contrib.admin.utils import display_for_field
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, path
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.contrib.forms.widgets import ArrayWidget, UnfoldAdminSelectWidget
from unfold.decorators import action

from .models import (
    ServicePriceRule,
    Tenancy,
    TenancyMeter,
    TenancyTenant,
    TenancyService,
)
from .services.tenancy import officialize_tenancy
from properties.models import Room, RoomMeter
from core.widgets import ThousandsInput, LocalizedDateInputWidget


class TenancyTenantInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        primary_count = 0
        cotenant_count = 0
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

            if role == "primary":
                primary_count += 1
            if role == "co-tenant":
                cotenant_count += 1

        if primary_count == 0:
            raise ValidationError("One Tenancy must have one primary tenant.")

        if primary_count > 1:
            raise ValidationError("One Tenancy can only have one primary tenant.")

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
    extra = 0
    autocomplete_fields = ("tenant",)
    fields = ("tenant", "role")
    show_change_link = True
    show_title = False

    class Media:
        js = ("admin/js/tenancy_tenant_inline.js",)


class TenancyMeterInlineForm(forms.ModelForm):
    class Meta:
        model = TenancyMeter
        fields = ["meter", "meter_reading"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["meter"].queryset = RoomMeter.objects.all()


class TenancyMeterInline(TabularInline):
    model = TenancyMeter
    form = TenancyMeterInlineForm
    extra = 0
    fields = ["meter", "meter_reading"]
    show_change_link = True
    show_title = False

    class Media:
        css = {"all": ("admin/css/tenancy_meter_inline.css",)}


class TenancyServiceInlineForm(forms.ModelForm):
    show_required = (
        "parking_price",
        "internet_price",
        "laundry_price",
        "cleaner_price",
    )

    class Meta:
        model = TenancyService
        fields = "__all__"
        localized_fields = (
            "rent_price",
            "electricity_price",
            "water_price",
            "parking_price",
            "laundry_price",
            "internet_price",
            "cleaner_price",
        )
        widgets = {name: ThousandsInput() for name in localized_fields}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set help text for water_price field based on whether the room has a water meter (If the tenancy is draft update or newly created)
        # For the case of viewing an official tenancy, water_price field will be replaced to water_price_display field, so this logic will not be executed
        if "water_price" in self.fields:
            tenancy = self.instance.tenancy if self.instance.tenancy_id else None
            room = tenancy.room if tenancy else None

            if room and room.has_water_meter is not None:
                self.fields["water_price"].help_text = (
                    "Giá nước (VND/m³)"
                    if room.has_water_meter
                    else "Giá nước (VND/người/tháng)"
                )
            else:
                self.fields["water_price"].help_text = "Giá nước"

        # Set required attribute and remove HTML required for specified fields
        for name in self.show_required:
            if name in self.fields:
                self.fields[name].required = True
                self.fields[name].widget.is_required = False

    def full_clean(self):
        # Temporarily disable required validation for specified fields to allow empty values to pass initial validation
        required_backup = {}
        for name in self.show_required:
            if name in self.fields:
                required_backup[name] = self.fields[name].required
                self.fields[name].required = False
        try:
            super().full_clean()
        finally:
            for name, val in required_backup.items():
                self.fields[name].required = val

    def clean(self):
        cleaned_data = super().clean()
        tenancy = cleaned_data.get("tenancy")
        required_prices = [
            (
                bool(tenancy and tenancy.vehicle_plate_numbers),
                "parking_price",
                "Parking",
            ),
            (cleaned_data.get("laundry"), "laundry_price", "Laundry"),
            (cleaned_data.get("internet"), "internet_price", "Internet"),
            (cleaned_data.get("cleaner"), "cleaner_price", "Cleaner"),
        ]
        for service_enabled, price_field, label in required_prices:
            if service_enabled and cleaned_data.get(price_field) is None:
                self.add_error(
                    price_field,
                    f"{label} price is required.",
                )

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
                    "water_price",
                ]
            },
        ),
        (
            "Dịch vụ",
            {
                "fields": [
                    "parking_price",
                    ("laundry", "laundry_price"),
                    ("internet", "internet_price"),
                    ("cleaner", "cleaner_price"),
                ]
            },
        ),
    ]

    # Setup readonly water_price field if the tenancy is official (form is readonly)
    @admin.display(description="Water price")
    def water_price_display(self, instance):
        field = self.model._meta.get_field("water_price")

        formatted_price = display_for_field(
            instance.water_price,
            field,
            self.get_empty_value_display(),
        )
        help_text = (
            "Giá nước (VND/người/tháng)"
            if instance.is_water_flat_fee
            else "Giá nước (VND/m³)"
        )

        return format_html(
            '<div class="font-medium">{}</div>' '<p class="help">{}</p>',
            formatted_price,
            help_text,
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not obj or obj.status == Tenancy.Status.DRAFT:
            return fieldsets
        tenancy_service = obj.services
        updated_fieldsets = []

        for title, options in fieldsets:
            fields = []

            for item in options["fields"]:
                if isinstance(item, (tuple, list)):
                    # Replace water_price field with water_price_display field for official tenancy
                    if "water_price" in item:
                        if tenancy_service.is_water_flat_fee:
                            item = "water_price_display"
                        else:
                            item = tuple(
                                (
                                    "water_price_display"
                                    if field == "water_price"
                                    else field
                                )
                                for field in item
                            )
                    # Skip laundry, internet, and cleaner fields if the service is not available
                    if "laundry" in item and not tenancy_service.laundry:
                        item = ("laundry",)
                    if "internet" in item and not tenancy_service.internet:
                        item = ("internet",)
                    if "cleaner" in item and not tenancy_service.cleaner:
                        item = ("cleaner",)
                # Skip parking_price field if there are no vehicle plate numbers
                elif item == "parking_price" and not obj.vehicle_plate_numbers:
                    continue

                fields.append(item)

            updated_fieldsets.append((title, {**options, "fields": fields}))

        return updated_fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))

        if obj and obj.status != Tenancy.Status.DRAFT:
            # Add water_price_display to readonly_fields for official tenancy
            readonly_fields.append("water_price_display")

        return readonly_fields

    class Media:
        js = ("admin/js/tenancy_service_inline.js",)
        css = {"all": ("admin/css/tenancy_service_inline.css",)}


class RoomSelectWidget(UnfoldAdminSelectWidget):
    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex,
            attrs,
        )

        room = getattr(value, "instance", None)
        if room:
            option["attrs"]["data-room-meters-url"] = reverse(
                "properties:room-meters", kwargs={"pk": room.pk}
            )
            option["attrs"]["data-has-water-meter"] = str(room.has_water_meter).lower()

        return option


class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = "__all__"
        widgets = {
            "room": RoomSelectWidget(),
            "contract_start_date": LocalizedDateInputWidget(),
            "contract_end_date": LocalizedDateInputWidget(),
            "billing_start_date": LocalizedDateInputWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        contract_start_date = cleaned_data.get("contract_start_date")
        contract_end_date = cleaned_data.get("contract_end_date")
        if (
            contract_start_date
            and contract_end_date
            and contract_start_date > contract_end_date
        ):
            self.add_error(
                "contract_end_date",
                "End date must be after start date.",
            )

        return cleaned_data


@admin.register(Tenancy)
class TenancyAdmin(ModelAdmin):
    form = TenancyForm
    inlines = [
        TenancyTenantInline,
        TenancyMeterInline,
        TenancyServiceInline,
    ]
    list_display = (
        "primary_tenant",
        "room",
        "contract_start_date",
        "contract_end_date",
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
        ("contract_start_date", "contract_end_date"),
        ("billing_start_date", "deposit"),
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

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "service-price-rule/",
                self.admin_site.admin_view(self.get_service_price_rule),
                name="tenancy_service_price_rule",
            ),
        ]

        return custom_urls + urls

    def get_service_price_rule(self, request):
        rule = ServicePriceRule.get_solo()

        return JsonResponse(
            {
                "electricity_price": rule.electricity_price,
                "water_price": rule.water_price,
                "water_flat_fee": rule.water_flat_fee,
                "parking_price": rule.parking_price,
                "laundry_price": rule.laundry_price,
                "internet_price": rule.internet_price,
                "cleaner_price": rule.cleaner_price,
            }
        )

    def save_formset(self, request, form, formset, change):
        if formset.model is TenancyMeter and change:
            # When the selected Room changes, JavaScript replaces all meter forms
            # with new extra forms and resets INITIAL_FORMS to 0.
            #
            # Django therefore treats these forms as entirely new records and
            # does not automatically delete the existing TenancyMeter records.
            # Delete the old records first so that only meters belonging to the
            # newly selected Room remain after saving.
            #
            # If the Room has not changed, INITIAL_FORMS retains its original
            # value, allowing Django to update existing meter readings normally.
            if formset.initial_form_count() == 0:
                TenancyMeter.objects.filter(tenancy=form.instance).delete()

        # Let Django handle the normal formset save process, including creating
        # the replacement TenancyMeter records when the Room has changed.
        super().save_formset(
            request,
            form,
            formset,
            change,
        )

    actions_submit_line = ["changeform_officialize_tenancy_action"]

    @action(
        description="Officialize tenancy",
        permissions=["officialize_tenancy_action"],
    )
    def changeform_officialize_tenancy_action(self, request, obj):
        officialize_tenancy(obj.id)

    def has_officialize_tenancy_action_permission(self, request, object_id):
        if object_id:
            tenancy = Tenancy.objects.get(pk=object_id)
            if tenancy.status != Tenancy.Status.DRAFT:
                return False
        return True

    def has_change_permission(self, request, obj=None):
        if obj and obj.status != Tenancy.Status.DRAFT:
            return False
        return super().has_change_permission(request, obj)

    class Media:
        js = ("admin/js/tenancy.js",)


class ServicePriceRuleForm(forms.ModelForm):
    class Meta:
        model = ServicePriceRule
        fields = "__all__"
        localized_fields = (
            "electricity_price",
            "water_price",
            "water_flat_fee",
            "parking_price",
            "laundry_price",
            "internet_price",
            "cleaner_price",
        )
        widgets = {name: ThousandsInput() for name in localized_fields}


@admin.register(ServicePriceRule)
class ServicePriceRuleAdmin(ModelAdmin):
    form = ServicePriceRuleForm
    list_display = (
        "electricity_price",
        "water_price",
        "water_flat_fee",
        "parking_price",
        "laundry_price",
        "internet_price",
        "cleaner_price",
    )

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "",
                self.admin_site.admin_view(self.redirect_to_change),
                name="contracts_servicepricerule_changelist",
            ),
        ]

        return custom_urls + urls

    def redirect_to_change(self, request):
        obj = ServicePriceRule.get_solo()

        url = reverse(
            "admin:contracts_servicepricerule_change",
            args=[obj.pk],
        )

        return redirect(url)

    def has_add_permission(self, request):
        return not ServicePriceRule.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

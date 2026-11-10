import uuid
from django.db import models
from contracts.models import Tenancy
from tenants.models import Tenant


class TenancyTenantPeriod(models.Model):
    class Role(models.TextChoices):
        PRIMARY = "primary", "Chính"
        CO_TENANT = "co-tenant", "Ở ghép"

    class Meta:
        verbose_name_plural = "Tenancy Tenant Periods"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.ForeignKey(
        Tenancy,
        on_delete=models.CASCADE,
        help_text="Hợp đồng thuê",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, help_text="Người thuê")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        help_text="Vai trò của người thuê trong hợp đồng",
    )
    start_date = models.DateField(help_text="Ngày bắt đầu thuê")
    end_date = models.DateField(help_text="Ngày kết thúc thuê")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, help_text="Ngày cập nhật")

    def __str__(self):
        return f"Tenancy Tenant Period ({self.id})"


class TenancyServicePeriod(models.Model):
    class Service(models.TextChoices):
        LAUNDRY = "laundry", "Giặt là"
        PARKING = "parking", "Gửi xe"
        INTERNET = "internet", "Internet"
        CLEANER = "cleaner", "Dọn dẹp"
        WATER = "water", "Nước"
        ELECTRICITY = "electricity", "Điện"

    class Meta:
        verbose_name_plural = "Tenancy Service Periods"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.ForeignKey(
        Tenancy,
        on_delete=models.CASCADE,
        help_text="Hợp đồng thuê",
    )
    service = models.CharField(
        max_length=50,
        help_text="Tên dịch vụ",
        choices=Service.choices,
    )
    price = models.PositiveIntegerField(
        help_text="Giá dịch vụ",
        null=True,
        blank=True,
    )
    start_date = models.DateField(help_text="Ngày bắt đầu tính phí dịch vụ")
    end_date = models.DateField(help_text="Ngày kết thúc tính phí dịch vụ")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, help_text="Ngày cập nhật")

    def __str__(self):
        return f"Tenancy Service Period ({self.id})"


class TenancyVehiclePeriod(models.Model):
    class Meta:
        verbose_name_plural = "Tenancy Vehicle Periods"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.ForeignKey(
        Tenancy,
        on_delete=models.CASCADE,
        help_text="Hợp đồng thuê",
    )
    license_plate = models.CharField(max_length=20, help_text="Biển số xe")
    start_date = models.DateField(help_text="Ngày bắt đầu gửi xe")
    end_date = models.DateField(help_text="Ngày kết thúc gửi xe")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, help_text="Ngày cập nhật")

    def __str__(self):
        return f"Tenancy Vehicle Period ({self.id})"

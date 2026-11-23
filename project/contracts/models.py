import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

from tenants.models import Tenant
from properties.models import Room, RoomMeter


class Tenancy(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Nháp"
        OFFICIAL = "official", "Chính thức"
        OUTDATE = "outdate", "Hết hạn"
        TERMINATE = "terminate", "Chấm dứt"

    class Meta:
        ordering = ["room", "contract_start_date", "contract_end_date"]
        verbose_name_plural = "Tenancies"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, help_text="Phòng thuê")
    vehicle_plate_numbers = ArrayField(
        models.CharField(max_length=20), help_text="Biển số xe", null=True, blank=True
    )
    contract_start_date = models.DateField(help_text="Ngày hợp đồng có hiệu lực")
    contract_end_date = models.DateField(help_text="Ngày hợp đồng hết hiệu lực")
    billing_start_date = models.DateField(help_text="Ngày bắt đầu tính phí thuê nhà")
    deposit = models.PositiveIntegerField(help_text="Tiền đặt cọc")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Trạng thái hợp đồng",
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        updates = {
            "is_water_flat_fee": not self.room.has_water_meter,
        }

        if not self.vehicle_plate_numbers:
            updates["parking_price"] = None

        TenancyService.objects.filter(tenancy=self).update(**updates)

    def __str__(self):
        return f"Tenancy ({self.id}) (From {self.contract_start_date} to {self.contract_end_date}) (Room {self.room.room_id})"


class TenancyTenant(models.Model):
    class Role(models.TextChoices):
        PRIMARY = "primary", "Chính"
        CO_TENANT = "co-tenant", "Ở ghép"

    class Meta:
        ordering = ["tenancy", "tenant", "role"]
        verbose_name_plural = "Tenancy Tenants"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.ForeignKey(
        "Tenancy",
        on_delete=models.CASCADE,
        help_text="Hợp đồng thuê",
        related_name="tenants",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, help_text="Người thuê")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        help_text="Vai trò của người thuê trong hợp đồng",
    )

    def __str__(self):
        return f"Tenancy Tenant ({self.id})"


class TenancyMeter(models.Model):
    class Meta:
        ordering = ["tenancy", "meter"]
        verbose_name_plural = "Tenancy Meters"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.ForeignKey(
        "Tenancy",
        on_delete=models.CASCADE,
        help_text="Hợp đồng thuê",
        related_name="meters",
    )
    meter = models.ForeignKey(
        RoomMeter,
        on_delete=models.CASCADE,
        help_text="Đồng hồ phòng",
        related_name="tenancies",
    )
    meter_reading = models.PositiveIntegerField(
        help_text="Chỉ số đồng hồ tại thời điểm thuê"
    )

    def __str__(self):
        return f"Tenancy Meter ({self.id})"


class TenancyService(models.Model):
    class Meta:
        ordering = ["tenancy"]
        verbose_name_plural = "Tenancy Services"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.OneToOneField(
        Tenancy,
        on_delete=models.CASCADE,
        help_text="Hợp đồng thuê",
        related_name="services",
    )
    rent_price = models.PositiveIntegerField(help_text="Giá thuê")
    electricity_price = models.PositiveIntegerField(help_text="Giá điện (VND/kWh)")
    water_price = models.PositiveIntegerField(help_text="Giá nước")
    is_water_flat_fee = models.BooleanField(
        default=False, help_text="Có tính phí nước cố định"
    )
    laundry = models.BooleanField(default=False, help_text="Dịch vụ giặt là")
    laundry_price = models.PositiveIntegerField(
        help_text="Giá dịch vụ giặt là (VND/người/tháng)",
        null=True,
        blank=True,
    )
    parking_price = models.PositiveIntegerField(
        help_text="Giá dịch vụ gửi xe (VND/phương tiện/tháng)",
        null=True,
        blank=True,
    )
    internet = models.BooleanField(default=False, help_text="Dịch vụ internet")
    internet_price = models.PositiveIntegerField(
        help_text="Giá dịch vụ internet (VND/người/tháng)",
        null=True,
        blank=True,
    )
    cleaner = models.BooleanField(default=False, help_text="Dịch vụ dọn dẹp")
    cleaner_price = models.PositiveIntegerField(
        help_text="Giá dịch vụ dọn dẹp (VND/người/tháng)",
        null=True,
        blank=True,
    )

    def _reset_unused_prices(self):
        if not self.tenancy.vehicle_plate_numbers:
            self.parking_price = None
        if not self.laundry:
            self.laundry_price = None
        if not self.internet:
            self.internet_price = None
        if not self.cleaner:
            self.cleaner_price = None
        self.is_water_flat_fee = not self.tenancy.room.has_water_meter

    def save(self, *args, **kwargs):
        self._reset_unused_prices()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Tenancy Service ({self.id})"


class ServicePriceRule(models.Model):
    """
    Singleton model storing default prices for rental services.
    Only one record is allowed (primary key = 1).
    """

    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=1,
        editable=False,
    )
    electricity_price = models.PositiveIntegerField(
        default=0,
        verbose_name="Giá điện (VND/kWh)",
    )
    water_price = models.PositiveIntegerField(
        default=0,
        verbose_name="Giá nước (VND/m³)",
    )
    water_flat_fee = models.PositiveIntegerField(
        default=0,
        verbose_name="Giá nước cố định (VND/người/tháng)",
    )
    parking_price = models.PositiveIntegerField(
        default=0,
        verbose_name="Giá dịch vụ gửi xe (VND/phương tiện/tháng)",
    )
    laundry_price = models.PositiveIntegerField(
        default=0,
        verbose_name="Giá dịch vụ giặt là (VND/người/tháng)",
    )
    internet_price = models.PositiveIntegerField(
        default=0,
        verbose_name="Giá dịch vụ internet (VND/người/tháng)",
    )
    cleaner_price = models.PositiveIntegerField(
        default=0,
        verbose_name="Giá dịch vụ dọn dẹp (VND/người/tháng)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service Price Rule"
        verbose_name_plural = "Service Price Rule"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("ServicePriceRule singleton instance cannot be deleted.")

    @classmethod
    def get_solo(cls):
        """Get the singleton instance, creating it if necessary."""
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self):
        return "Default Service Price Rule"

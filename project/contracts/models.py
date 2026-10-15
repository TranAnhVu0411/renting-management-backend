import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import ArrayField

from tenants.models import Tenant
from properties.models import Room


class Tenancy(models.Model):
    class Meta:
        ordering = ["tenant", "room", "start_date", "end_date"]
        verbose_name_plural = "Tenancies"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, help_text="Người thuê đứng tên hợp đồng"
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE, help_text="Phòng thuê")
    vehicle_plate_numbers = ArrayField(
        models.CharField(max_length=20), help_text="Biển số xe"
    )
    start_date = models.DateField(null=True, blank=True, help_text="Ngày bắt đầu thuê")
    end_date = models.DateField(null=True, blank=True, help_text="Ngày kết thúc thuê")
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Nháp"),
            ("official", "Chính thức"),
            ("outdate", "Hết hạn"),
            ("terminate", "Chấm dứt"),
        ],
        default="draft",
        help_text="Trạng thái hợp đồng",
    )

    def __str__(self):
        return f"{self.tenant.name} ({self.start_date} - {self.end_date}) ({self.room.room_id})"


class TenancyTenant(models.Model):
    class Meta:
        ordering = ["tenancy", "tenant", "role"]
        verbose_name_plural = "Tenancy Tenants"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.ForeignKey(
        "Tenancy", on_delete=models.CASCADE, help_text="Hợp đồng thuê"
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, help_text="Người thuê")
    role = models.CharField(
        max_length=20,
        choices=[("primary", "Chính"), ("co-tenant", "Ở ghép")],
        help_text="Vai trò của người thuê trong hợp đồng",
    )
    active = models.BooleanField(
        default=True, help_text="Trạng thái hoạt động của người thuê trong hợp đồng"
    )


class TenancyService(models.Model):
    class Meta:
        ordering = ["tenancy"]
        verbose_name_plural = "Tenancy Services"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenancy = models.OneToOneField(
        Tenancy, on_delete=models.CASCADE, help_text="Hợp đồng thuê"
    )
    rent_price = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Giá thuê"
    )
    electricity_price = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Giá điện (theo kWh)"
    )
    water_price = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Giá nước (theo m3)"
    )
    laundry = models.BooleanField(default=False, help_text="Dịch vụ giặt là")
    laundry_price = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Giá dịch vụ giặt là"
    )
    parking = models.BooleanField(default=False, help_text="Dịch vụ gửi xe")
    parking_price = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Giá dịch vụ gửi xe"
    )
    internet = models.BooleanField(default=False, help_text="Dịch vụ internet")
    internet_price = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Giá dịch vụ internet"
    )
    cleaner = models.BooleanField(default=False, help_text="Dịch vụ dọn dẹp")
    cleaner_price = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Giá dịch vụ dọn dẹp"
    )

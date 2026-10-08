import uuid

from django.db import models


class Tenant(models.Model):
    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Tenants"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, help_text="Họ tên người thuê")
    identity_card_number = models.CharField(
        max_length=30, unique=True, db_index=True, help_text="Số CCCD/CMND"
    )
    permanent_address = models.CharField(max_length=255, help_text="Địa chỉ thường trú")
    identity_card_created_date = models.DateField(
        null=True, blank=True, help_text="Ngày cấp CCCD/CMND"
    )
    identity_card_created_place = models.CharField(
        max_length=255, null=True, blank=True, help_text="Nơi cấp CCCD/CMND"
    )
    phone_number = models.CharField(
        max_length=20, null=True, blank=True, help_text="Số điện thoại"
    )
    active = models.BooleanField(default=True, help_text="Trạng thái hoạt động")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, help_text="Ngày cập nhật")

    def __str__(self):
        return f"{self.name} ({self.identity_card_number})"

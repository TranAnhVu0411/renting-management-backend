import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Room(models.Model):
    class Meta:
        ordering = ["room_id"]
        verbose_name_plural = "Rooms"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(area__gt=0.00), name="room_area_gt_0"
            )
        ]

    class Status(models.TextChoices):
        EMPTY = "empty", "Trống"
        OCCUPY = "occupy", "Đang cho thuê"
        MAINTENANCE = "maintenance", "Đang bảo trì"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_id = models.CharField(max_length=150, unique=True, help_text="Mã số phòng")
    allow_co_tenant = models.BooleanField(
        default=False, help_text="Có cho phép ở ghép không"
    )
    co_tenant_maximum = models.PositiveSmallIntegerField(
        default=0, help_text="Số người được ở ghép tối đa"
    )
    area = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Diện tích phòng (m2)",
    )
    has_water_meter = models.BooleanField(
        default=True,
        help_text="Phòng có đồng hồ nước riêng",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.EMPTY,
        help_text="Trạng thái phòng",
    )

    def __str__(self):
        return f"{self.room_id}"

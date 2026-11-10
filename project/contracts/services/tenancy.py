from django.db import transaction
from contracts.models import Tenancy, TenancyTenant, TenancyService
from billing.models import (
    TenancyServicePeriod,
    TenancyVehiclePeriod,
    TenancyTenantPeriod,
)


def create_tenancy_service_periods(tenancy, tenancy_service):
    service_periods = []
    service_periods.extend(
        [
            TenancyServicePeriod(
                tenancy=tenancy,
                service=TenancyServicePeriod.Service.WATER,
                price=tenancy_service.water_price,
                start_date=tenancy.start_date,
                end_date=tenancy.end_date,
            ),
            TenancyServicePeriod(
                tenancy=tenancy,
                service=TenancyServicePeriod.Service.ELECTRICITY,
                price=tenancy_service.electricity_price,
                start_date=tenancy.start_date,
                end_date=tenancy.end_date,
            ),
        ]
    )
    if tenancy.vehicle_plate_numbers:
        service_periods.append(
            TenancyServicePeriod(
                tenancy=tenancy,
                service=TenancyServicePeriod.Service.PARKING,
                price=tenancy_service.parking_price,
                start_date=tenancy.start_date,
                end_date=tenancy.end_date,
            )
        )

    other_services = [
        (
            TenancyServicePeriod.Service.INTERNET,
            tenancy_service.internet,
            tenancy_service.internet_price,
        ),
        (
            TenancyServicePeriod.Service.CLEANER,
            tenancy_service.cleaner,
            tenancy_service.cleaner_price,
        ),
        (
            TenancyServicePeriod.Service.LAUNDRY,
            tenancy_service.laundry,
            tenancy_service.laundry_price,
        ),
    ]
    for service, is_enabled, price in other_services:
        if is_enabled:
            service_periods.append(
                TenancyServicePeriod(
                    tenancy=tenancy,
                    service=service,
                    price=price,
                    start_date=tenancy.start_date,
                    end_date=tenancy.end_date,
                )
            )

    TenancyServicePeriod.objects.bulk_create(service_periods)


def create_tenancy_vehicle_periods(tenancy):
    if tenancy.vehicle_plate_numbers:
        vehicle_periods = [
            TenancyVehiclePeriod(
                tenancy=tenancy,
                license_plate=plate_number,
                start_date=tenancy.start_date,
                end_date=tenancy.end_date,
            )
            for plate_number in tenancy.vehicle_plate_numbers
        ]
        TenancyVehiclePeriod.objects.bulk_create(vehicle_periods)


def create_tenancy_tenant_periods(tenancy, tenancy_tenants):
    tenant_periods = []
    for item in tenancy_tenants:
        tenant_periods.append(
            TenancyTenantPeriod(
                tenancy=tenancy,
                tenant=item.tenant,
                role=item.role,
                start_date=tenancy.start_date,
                end_date=tenancy.end_date,
            )
        )
    TenancyTenantPeriod.objects.bulk_create(tenant_periods)


@transaction.atomic
def officialize_tenancy(tenancy_id):
    tenancy = Tenancy.objects.select_for_update().get(pk=tenancy_id)

    if tenancy.status != Tenancy.Status.DRAFT:
        raise ValueError("Only draft tenancies can be officialized.")

    tenancy_tenants = TenancyTenant.objects.filter(tenancy=tenancy)
    tenancy_service = TenancyService.objects.get(tenancy=tenancy)

    create_tenancy_service_periods(tenancy, tenancy_service)
    create_tenancy_vehicle_periods(tenancy)
    create_tenancy_tenant_periods(tenancy, tenancy_tenants)

    tenancy.status = Tenancy.Status.OFFICIAL
    tenancy.save()

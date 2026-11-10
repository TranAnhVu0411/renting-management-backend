from django.db import transaction
from contracts.models import Tenancy


@transaction.atomic
def officialize_tenancy(tenancy_id):
    tenancy = Tenancy.objects.select_for_update().get(pk=tenancy_id)

    if tenancy.status != Tenancy.Status.DRAFT:
        raise ValueError("Only draft tenancies can be officialized.")

    tenancy.status = Tenancy.Status.OFFICIAL
    tenancy.save()

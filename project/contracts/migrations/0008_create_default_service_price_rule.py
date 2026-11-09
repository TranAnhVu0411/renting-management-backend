from django.db import migrations


def create_default_service_price_rule(apps, schema_editor):
    ServicePriceRule = apps.get_model(
        "contracts",
        "ServicePriceRule",
    )

    db_alias = schema_editor.connection.alias

    ServicePriceRule.objects.using(db_alias).get_or_create(
        pk=1,
        defaults={
            "electric_price": 0,
            "water_price": 0,
            "water_flat_fee": 0,
            "parking_price": 0,
            "laundry_price": 0,
            "internet_price": 0,
            "cleaner_price": 0,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0007_servicepricerule"),
    ]

    operations = [
        migrations.RunPython(
            create_default_service_price_rule,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
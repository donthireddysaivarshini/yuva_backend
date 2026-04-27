from django.db import migrations

def seed_store_locations(apps, schema_editor):
    StoreLocation = apps.get_model("content", "StoreLocation")

    stores = [
        ("Yuva Computers – Dilshuknagar", "Telangana", "9709888456", "https://maps.app.goo.gl/BM9uzhNAxJZ3ePAm8", 1, True),
        ("Yuva Computers – KPHB", "Telangana", "6304234456", "https://maps.app.goo.gl/BiT7KUfJNGBwYKwMA", 2, False),
        ("Yuva Computers – Warangal", "Telangana", "8308356456", "https://maps.app.goo.gl/v4TinaEjkUiCn61d9", 3, False),
        ("Yuva Computers – Karimnagar", "Telangana", "7417999456", "https://maps.app.goo.gl/Wh58JBdgmmo4zZeW6", 4, False),
        ("Yuva Computers – Nizamabad", "Telangana", "8445611456", "https://maps.app.goo.gl/YjJz8VTp6iw3GkTm7", 5, False),
        ("Yuva Computers – Khammam", "Telangana", "8420234456", "https://maps.app.goo.gl/W7SxmnKGhxgPmZS28", 6, False),
        ("Yuva Computers – Vizag", "Andhra Pradesh", "8829977456", "https://maps.app.goo.gl/7cbdN2T8WCAYxYkg7", 7, False),
        ("Yuva Computers – Kakinada", "Andhra Pradesh", "7799339544", "https://maps.app.goo.gl/tkbdeN5XZFJ3fb6Y7", 8, False),
        ("Yuva Computers – Vijayawada", "Andhra Pradesh", "8439356456", "https://maps.app.goo.gl/ywdMViZ3k5u6hG2y8", 9, False),
        ("Yuva Computers – Kurnool", "Andhra Pradesh", "9391550456", "https://maps.app.goo.gl/cGHnRqMSfBH59gGA8", 10, False),
        ("Yuva Computers – Tirupathi", "Andhra Pradesh", "8309654456", "https://maps.app.goo.gl/9Z3fdQmmUuM9ggo8A", 11, False),
        ("Yuva Computers – Rajamahendravaram", "Andhra Pradesh", "7456017456", "https://maps.app.goo.gl/cx1z13q7ub3dw9fq8", 12, False),
    ]

    for name, state, phone, maps_url, order, is_main in stores:
        StoreLocation.objects.get_or_create(
            name=name,
            defaults={
                "state": state,
                "phone": phone,
                "maps_url": maps_url,
                "order": order,
                
                "is_active": True,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0003_bulkscalepoint_companycertification_companyinvestor_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_store_locations),
    ]
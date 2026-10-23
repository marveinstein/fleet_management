from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0006_alter_fuellog_total_amount"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rider",
            name="contact_number",
        ),
        migrations.RemoveField(
            model_name="rider",
            name="license_number",
        ),
    ]

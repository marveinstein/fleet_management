from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="vehicle",
            old_name="model_name",
            new_name="vehicle_model",
        ),
        migrations.AddField(
            model_name="vehicle",
            name="vehicle_make",
            field=models.CharField(
                choices=[
                    ("Yamaha", "Yamaha"),
                    ("Honda", "Honda"),
                    ("Toyota", "Toyota"),
                    ("Ford", "Ford"),
                    ("Chevrolet", "Chevrolet"),
                    ("Nissan", "Nissan"),
                    ("Mitsubishi", "Mitsubishi"),
                    ("Isuzu", "Isuzu"),
                    ("Hyundai", "Hyundai"),
                    ("Kia", "Kia"),
                ],
                default="Yamaha",
                max_length=50,
                verbose_name="Make",
            ),
        ),
        migrations.AlterField(
            model_name="vehicle",
            name="vehicle_model",
            field=models.CharField(
                choices=[
                    ("YZF-R3", "YZF-R3"),
                    ("CBR600RR", "CBR600RR"),
                    ("Camry", "Camry"),
                    ("F-150", "F-150"),
                    ("Silverado", "Silverado"),
                    ("Altima", "Altima"),
                    ("Outlander", "Outlander"),
                    ("D-Max", "D-Max"),
                    ("Elantra", "Elantra"),
                    ("Sorento", "Sorento"),
                ],
                default="YZF-R3",
                max_length=100,
                verbose_name="Model Name",
            ),
        ),
        migrations.AlterField(
            model_name="vehicle",
            name="vehicle_type",
            field=models.CharField(
                choices=[
                    ("Motorcycle", "Motorcycle"),
                    ("Car", "Car"),
                    ("Truck", "Truck"),
                    ("Van", "Van"),
                ],
                default="Van",
                max_length=50,
                verbose_name="Vehicle Type",
            ),
        ),
        migrations.AlterField(
            model_name="vehicle",
            name="fuel_type",
            field=models.CharField(
                choices=[
                    ("Gasoline", "Gasoline"),
                    ("Diesel", "Diesel"),
                    ("Electric", "Electric"),
                ],
                default="Diesel",
                max_length=50,
                verbose_name="Fuel Type",
            ),
        ),
    ]

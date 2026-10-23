from django.db import models


from django.db import models
from django.utils import timezone


class Vehicle(models.Model):
    VEHICLE_MAKE = [
        ("Yamaha", "Yamaha"),
        ("Honda", "Honda"),
        ("Toyota", "Toyota"),
        ("Ford", "Ford"),
        ("Suzuki", "Suzuki"),
        ("Nissan", "Nissan"),
        ("Mitsubishi", "Mitsubishi"),
        ("Isuzu", "Isuzu"),
        ("Hyundai", "Hyundai"),
        ("Kia", "Kia"),
    ]
    VEHICLE_MODEL = [
        ("NMAX", "NMAX"),
        ("Hilux", "Hilux"),
        ("Avanza", "Avanza"),
        ("F-150", "F-150"),
        ("Silverado", "Silverado"),
        ("Altima", "Altima"),
        ("Outlander", "Outlander"),
        ("D-Max", "D-Max"),
        ("Elantra", "Elantra"),
        ("Sorento", "Sorento"),
    ]
    VEHICLE_TYPE = [
        ("MTC", "Motorcycle"),
        ("SED", "Sedan"),
        ("SUV", "SUV"),
        ("TRK", "Truck"),
        ("VAN", "Van"),
    ]
    FUEL_TYPE = [
        ("GAS", "Gasoline"),
        ("DSL", "Diesel"),
        ("ELE", "Electric"),
        ("HYB", "Hybrid"),
    ]
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Maintenance", "Maintenance"),
        ("Inactive", "Inactive"),
    ]

    # --- Identity Fields ---
    plate_number = models.CharField(
        max_length=20, unique=True, verbose_name="Plate Number"
    )
    vehicle_make = models.CharField(
        max_length=50,
        choices=VEHICLE_MAKE,
        verbose_name="Make",
    )
    vehicle_model = models.CharField(
        max_length=100,
        choices=VEHICLE_MODEL,
        verbose_name="Model Name",
    )

    # --- Specifications ---
    vehicle_type = models.CharField(
        max_length=50,
        choices=VEHICLE_TYPE,
        verbose_name="Vehicle Type",
    )
    fuel_type = models.CharField(
        max_length=50,
        choices=FUEL_TYPE,
        verbose_name="Fuel Type",
    )

    # --- Live State Tracking ---
    mileage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name="Mileage (KM)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Status",
    )
    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vehicle_make", "vehicle_model"]
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"

    def __str__(self):
        # Human-readable representation used in Django Admin and shells
        return f"{self.vehicle_make} {self.vehicle_model} ({self.plate_number})"


class Rider(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("On Leave", "On Leave"),
        ("Inactive", "Inactive"),
    ]

    driver_name = models.CharField(max_length=150, verbose_name="Driver / Rider Name")
    assigned_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_riders",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Active", verbose_name="Status"
    )

    def __str__(self):
        return self.driver_name


class TripTicket(models.Model):
    ticket_number = models.CharField(
        max_length=50, unique=True, verbose_name="Trip Ticket Number"
    )
    date = models.DateField(default=timezone.now, verbose_name="Date")
    driver = models.ForeignKey(
        Rider, on_delete=models.CASCADE, related_name="trip_tickets"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="trip_tickets"
    )

    start_odometer = models.FloatField(verbose_name="Start Odometer (KM)")
    end_odometer = models.FloatField(verbose_name="End Odometer (KM)")

    class Meta:
        verbose_name = "Trip Ticket"
        verbose_name_plural = "Trip Tickets"

    @property
    def total_distance(self):
        if self.end_odometer and self.start_odometer:
            return max(0.0, self.end_odometer - self.start_odometer)
        return 0.0

    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.vehicle.plate_number}"


class FuelLog(models.Model):
    receipt_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Receipt / Invoice Number"
    )
    date = models.DateField(default=timezone.now)
    fuel_station = models.CharField(max_length=150, verbose_name="Gas Station / Vendor")
    driver = models.ForeignKey(
        Rider, on_delete=models.CASCADE, related_name="fuel_logs"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="fuel_logs"
    )
    liters = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Liters Pumped"
    )
    cost_per_liter = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Cost per Liter"
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Total Amount"
    )

    class Meta:
        verbose_name = "Fuel Log"
        verbose_name_plural = (
            "Fuel Logs"  # This changes what shows up in the admin list
        )

    @property
    def total_fuel(self):
        if self.liters and self.cost_per_liter:
            return max(0.0, self.liters * float(self.cost_per_liter))
        return 0.0

    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.vehicle.plate_number}"

    def save(self, *args, **kwargs):
        if not self.total_amount and self.liters and self.cost_per_liter:
            self.total_amount = round(
                float(self.liters) * float(self.cost_per_liter), 2
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fuel #{self.id} - {self.vehicle.plate_number} ({self.date})"

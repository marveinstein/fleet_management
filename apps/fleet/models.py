from django.db import models


from django.db import models
from django.utils import timezone


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('Truck', 'Truck'),
        ('Van', 'Van'),
        ('Motorcycle', 'Motorcycle'),
        ('Car', 'Car'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Maintenance', 'Maintenance'),
        ('Inactive', 'Inactive'),
    ]

    plate_number = models.CharField(max_length=20, unique=True, verbose_name="Plate Number")
    model_name = models.CharField(max_length=100, verbose_name="Model Name")
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_TYPES, default='Van', verbose_name="Vehicle Type")
    fuel_type = models.CharField(max_length=50, default='Diesel', verbose_name="Fuel Type")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plate_number} ({self.model_name})"


class Rider(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('On Leave', 'On Leave'),
        ('Inactive', 'Inactive'),
    ]

    driver_name = models.CharField(max_length=150, verbose_name="Driver / Rider Name")
    license_number = models.CharField(max_length=50, unique=True, verbose_name="License Number")
    contact_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Contact Number")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    assigned_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_riders')

    def __str__(self):
        return self.driver_name


class TripTicket(models.Model):
    ticket_number = models.CharField(max_length=50, unique=True, verbose_name="Trip Ticket Number")
    driver = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='trip_tickets')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trip_tickets')
    date = models.DateField(default=timezone.now)
    departure_time = models.TimeField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    start_odometer = models.FloatField(verbose_name="Start Odometer (KM)")
    end_odometer = models.FloatField(verbose_name="End Odometer (KM)")
    destination = models.CharField(max_length=255)
    purpose = models.TextField()
    passengers = models.CharField(max_length=255, blank=True, null=True)

    @property
    def total_distance(self):
        if self.end_odometer and self.start_odometer:
            return max(0.0, self.end_odometer - self.start_odometer)
        return 0.0

    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.vehicle.plate_number}"


class FuelLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    driver = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='fuel_logs')
    date = models.DateField(default=timezone.now)
    fuel_station = models.CharField(max_length=150, verbose_name="Gas Station / Vendor")
    liters = models.FloatField(verbose_name="Liters Pumped")
    cost_per_liter = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost per Liter")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total Amount")
    odometer_reading = models.FloatField(verbose_name="Odometer Reading (KM)")
    receipt_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Receipt / Invoice Number")

    def save(self, *args, **kwargs):
        if not self.total_amount and self.liters and self.cost_per_liter:
            self.total_amount = round(Decimal(str(self.liters)) * self.cost_per_liter, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fuel #{self.id} - {self.vehicle.plate_number} ({self.date})"


class MiscTrip(models.Model):
    trip_title = models.CharField(max_length=200, verbose_name="Misc Trip Title")
    driver = models.ForeignKey(Rider, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Expense Amount")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.trip_title} ({self.date})"


class ReceiptTracking(models.Model):
    receipt_number = models.CharField(max_length=100, unique=True, verbose_name="Receipt Number")
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    attached_to_type = models.CharField(max_length=50, choices=[('Fuel', 'Fuel'), ('Trip', 'Trip'), ('Maintenance', 'Maintenance'), ('Other', 'Other')])

    def __str__(self):
        return f"Receipt #{self.receipt_number} - ${self.amount}"

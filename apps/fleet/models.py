from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_MANAGER = "manager"
    ROLE_DRIVER = "driver"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_MANAGER, "Fleet Manager"),
        (ROLE_DRIVER, "Driver"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_DRIVER)
    phone_number = models.CharField(max_length=30, blank=True, default="")
    driver_profile = models.OneToOneField(
        "Rider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_account",
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


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
        default="Active",
        verbose_name="Status",
    )

    # --- Telemetry Cache (Latest GPS & Telemetry Snapshot) ---
    current_latitude = models.FloatField(default=14.5995, null=True, blank=True)
    current_longitude = models.FloatField(default=120.9842, null=True, blank=True)
    current_speed = models.FloatField(default=0.0)
    current_heading = models.FloatField(default=0.0)
    current_fuel_level = models.FloatField(default=100.0)  # Percentage 0-100
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    last_known_address = models.CharField(max_length=255, blank=True, default="")

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vehicle_make", "vehicle_model"]
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"

    def __str__(self):
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
    license_number = models.CharField(max_length=50, blank=True, default="")
    contact_number = models.CharField(max_length=30, blank=True, default="")
    safety_score = models.FloatField(default=95.0)
    total_trips = models.IntegerField(default=0)
    total_distance = models.FloatField(default=0.0)

    def __str__(self):
        return self.driver_name


class TripTicket(models.Model):
    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

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

    origin = models.CharField(max_length=200, default="Central Logistics Hub")
    destination = models.CharField(max_length=200, default="Regional Distribution Point")
    purpose = models.CharField(
        max_length=255, blank=True, default="Operational Deliveries & Routing"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Completed"
    )

    start_odometer = models.FloatField(verbose_name="Start Odometer (KM)")
    end_odometer = models.FloatField(verbose_name="End Odometer (KM)")
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    fuel_consumed_liters = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.0
    )

    class Meta:
        verbose_name = "Trip Ticket"
        verbose_name_plural = "Trip Tickets"
        ordering = ["-date", "-id"]

    @property
    def total_distance(self):
        if self.end_odometer and self.start_odometer:
            return max(0.0, round(self.end_odometer - self.start_odometer, 2))
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
    odometer_reading = models.FloatField(default=0.0)
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Fuel Log"
        verbose_name_plural = "Fuel Logs"
        ordering = ["-date", "-id"]

    @property
    def total_fuel(self):
        if self.liters and self.cost_per_liter:
            return max(0.0, float(self.liters) * float(self.cost_per_liter))
        return 0.0

    def save(self, *args, **kwargs):
        if not self.total_amount and self.liters and self.cost_per_liter:
            self.total_amount = round(
                float(self.liters) * float(self.cost_per_liter), 2
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fuel #{self.id} - {self.vehicle.plate_number} ({self.date})"


class VehicleTelemetry(models.Model):
    EVENT_CHOICES = [
        ("normal", "Normal Ping"),
        ("speeding", "Speeding Warning"),
        ("harsh_braking", "Harsh Braking"),
        ("rapid_acceleration", "Rapid Acceleration"),
        ("low_fuel", "Low Fuel Warning"),
        ("engine_fault", "Engine Fault"),
    ]
    ENGINE_STATUS = [
        ("running", "Running"),
        ("idle", "Idling"),
        ("stopped", "Stopped"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="telemetry_logs", db_index=True
    )
    driver = models.ForeignKey(
        Rider, on_delete=models.SET_NULL, null=True, blank=True, related_name="telemetry_logs"
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0.0, help_text="km/h")
    heading = models.FloatField(default=0.0, help_text="degrees 0-360")
    fuel_level = models.FloatField(default=100.0, help_text="percentage 0-100")
    engine_status = models.CharField(
        max_length=20, choices=ENGINE_STATUS, default="running"
    )
    odometer = models.FloatField(default=0.0)
    battery_voltage = models.FloatField(default=12.6)
    engine_temp = models.FloatField(default=85.0)
    event_type = models.CharField(
        max_length=30, choices=EVENT_CHOICES, default="normal"
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["vehicle", "-timestamp"]),
            models.Index(fields=["event_type", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.vehicle.plate_number} @ {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class MaintenanceSchedule(models.Model):
    SERVICE_CHOICES = [
        ("oil_change", "Engine Oil & Filter Change"),
        ("brake_service", "Brake Pad & Rotor Inspection"),
        ("tire_rotation", "Tire Rotation & Wheel Alignment"),
        ("battery_check", "Battery & Electrical System Check"),
        ("transmission", "Transmission Fluid & Drivetrain Flush"),
        ("annual_inspection", "Comprehensive Fleet Safety Inspection"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="maintenance_schedules"
    )
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    interval_km = models.IntegerField(default=5000, help_text="Mileage interval in KM")
    interval_days = models.IntegerField(default=180, help_text="Days interval")
    last_service_km = models.FloatField(default=0.0)
    last_service_date = models.DateField(default=timezone.now)
    next_due_km = models.FloatField(default=5000.0)
    next_due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["vehicle", "next_due_km"]

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.get_service_type_display()} (Due: {self.next_due_km} KM)"


class MaintenanceAlert(models.Model):
    SEVERITY_CHOICES = [
        ("critical", "Critical Overdue"),
        ("warning", "Due Soon"),
        ("info", "Routine Reminder"),
    ]
    STATUS_CHOICES = [
        ("open", "Open Alert"),
        ("scheduled", "Service Scheduled"),
        ("resolved", "Resolved"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="maintenance_alerts"
    )
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
    )
    service_type = models.CharField(max_length=100)
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default="warning"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open"
    )
    message = models.CharField(max_length=255)
    current_odometer = models.FloatField(default=0.0)
    due_odometer = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.vehicle.plate_number} - {self.service_type}"


class MaintenanceLog(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="maintenance_logs"
    )
    alert = models.ForeignKey(
        MaintenanceAlert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_record",
    )
    service_type = models.CharField(max_length=100)
    service_date = models.DateField(default=timezone.now)
    odometer_at_service = models.FloatField(default=0.0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    service_provider = models.CharField(
        max_length=150, blank=True, default="Authorized Fleet Center"
    )
    technician = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-service_date", "-id"]

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.service_type} (${self.cost})"


class DriverPerformance(models.Model):
    driver = models.ForeignKey(
        Rider, on_delete=models.CASCADE, related_name="performance_history"
    )
    month = models.DateField(help_text="First day of the month")
    total_distance_km = models.FloatField(default=0.0)
    trips_completed = models.IntegerField(default=0)
    fuel_consumed_liters = models.FloatField(default=0.0)
    efficiency_km_per_liter = models.FloatField(default=0.0)
    safety_score = models.FloatField(default=95.0)  # 0 to 100
    harsh_braking_count = models.IntegerField(default=0)
    rapid_accel_count = models.IntegerField(default=0)
    speeding_count = models.IntegerField(default=0)
    idling_hours = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-month", "driver"]
        unique_together = ["driver", "month"]

    def __str__(self):
        return f"{self.driver.driver_name} - {self.month.strftime('%B %Y')} (Score: {self.safety_score})"


class VehicleTelemetry(models.Model):
    EVENT_CHOICES = [
        ("normal", "Normal Ping"),
        ("speeding", "Speeding Warning"),
        ("harsh_braking", "Harsh Braking"),
        ("rapid_acceleration", "Rapid Acceleration"),
        ("low_fuel", "Low Fuel Warning"),
        ("engine_fault", "Engine Fault"),
    ]
    ENGINE_STATUS = [
        ("running", "Running"),
        ("idle", "Idling"),
        ("stopped", "Stopped"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="telemetry_logs", db_index=True
    )
    driver = models.ForeignKey(
        Rider, on_delete=models.SET_NULL, null=True, blank=True, related_name="telemetry_logs"
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0.0, help_text="km/h")
    heading = models.FloatField(default=0.0, help_text="degrees 0-360")
    fuel_level = models.FloatField(default=100.0, help_text="percentage 0-100")
    engine_status = models.CharField(
        max_length=20, choices=ENGINE_STATUS, default="running"
    )
    odometer = models.FloatField(default=0.0)
    battery_voltage = models.FloatField(default=12.6)
    engine_temp = models.FloatField(default=85.0)
    event_type = models.CharField(
        max_length=30, choices=EVENT_CHOICES, default="normal"
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["vehicle", "-timestamp"]),
            models.Index(fields=["event_type", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.vehicle.plate_number} @ {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class MaintenanceSchedule(models.Model):
    SERVICE_CHOICES = [
        ("oil_change", "Engine Oil & Filter Change"),
        ("brake_service", "Brake Pad & Rotor Inspection"),
        ("tire_rotation", "Tire Rotation & Wheel Alignment"),
        ("battery_check", "Battery & Electrical System Check"),
        ("transmission", "Transmission Fluid & Drivetrain Flush"),
        ("annual_inspection", "Comprehensive Fleet Safety Inspection"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="maintenance_schedules"
    )
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    interval_km = models.IntegerField(default=5000, help_text="Mileage interval in KM")
    interval_days = models.IntegerField(default=180, help_text="Days interval")
    last_service_km = models.FloatField(default=0.0)
    last_service_date = models.DateField(default=timezone.now)
    next_due_km = models.FloatField(default=5000.0)
    next_due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["vehicle", "next_due_km"]

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.get_service_type_display()} (Due: {self.next_due_km} KM)"


class MaintenanceAlert(models.Model):
    SEVERITY_CHOICES = [
        ("critical", "Critical Overdue"),
        ("warning", "Due Soon"),
        ("info", "Routine Reminder"),
    ]
    STATUS_CHOICES = [
        ("open", "Open Alert"),
        ("scheduled", "Service Scheduled"),
        ("resolved", "Resolved"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="maintenance_alerts"
    )
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
    )
    service_type = models.CharField(max_length=100)
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default="warning"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open"
    )
    message = models.CharField(max_length=255)
    current_odometer = models.FloatField(default=0.0)
    due_odometer = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.vehicle.plate_number} - {self.service_type}"


class MaintenanceLog(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="maintenance_logs"
    )
    alert = models.ForeignKey(
        MaintenanceAlert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_record",
    )
    service_type = models.CharField(max_length=100)
    service_date = models.DateField(default=timezone.now)
    odometer_at_service = models.FloatField(default=0.0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    service_provider = models.CharField(
        max_length=150, blank=True, default="Authorized Fleet Center"
    )
    technician = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-service_date", "-id"]

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.service_type} (${self.cost})"


class DriverPerformance(models.Model):
    driver = models.ForeignKey(
        Rider, on_delete=models.CASCADE, related_name="performance_history"
    )
    month = models.DateField(help_text="First day of the month")
    total_distance_km = models.FloatField(default=0.0)
    trips_completed = models.IntegerField(default=0)
    fuel_consumed_liters = models.FloatField(default=0.0)
    efficiency_km_per_liter = models.FloatField(default=0.0)
    safety_score = models.FloatField(default=95.0)  # 0 to 100
    harsh_braking_count = models.IntegerField(default=0)
    rapid_accel_count = models.IntegerField(default=0)
    speeding_count = models.IntegerField(default=0)
    idling_hours = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-month", "driver"]
        unique_together = ["driver", "month"]

    def __str__(self):
        return f"{self.driver.driver_name} - {self.month.strftime('%B %Y')} (Score: {self.safety_score})"


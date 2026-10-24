from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Vehicle, Rider, TripTicket, FuelLog, VehicleTelemetry,
    MaintenanceSchedule, MaintenanceAlert, MaintenanceLog,
    DriverPerformance, UserProfile
)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role", "phone_number", "driver_profile"]


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    driver_profile_id = serializers.IntegerField(
        source="profile.driver_profile.id", read_only=True
    )
    driver_name = serializers.CharField(
        source="profile.driver_profile.driver_name", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "role", "driver_profile_id", "driver_name", "is_staff", "is_superuser"
        ]


class VehicleSerializer(serializers.ModelSerializer):
    open_alerts_count = serializers.SerializerMethodField()
    assigned_driver = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = "__all__"

    def get_open_alerts_count(self, obj):
        return obj.maintenance_alerts.filter(status__in=["open", "scheduled"]).count()

    def get_assigned_driver(self, obj):
        rider = obj.assigned_riders.filter(status="Active").first()
        if rider:
            return {"id": rider.id, "name": rider.driver_name, "license": rider.license_number}
        return None


class RiderSerializer(serializers.ModelSerializer):
    assigned_vehicle_detail = VehicleSerializer(
        source="assigned_vehicle", read_only=True
    )

    class Meta:
        model = Rider
        fields = "__all__"


class TripTicketSerializer(serializers.ModelSerializer):
    driver_detail = RiderSerializer(source="driver", read_only=True)
    vehicle_detail = VehicleSerializer(source="vehicle", read_only=True)
    total_distance = serializers.FloatField(read_only=True)

    class Meta:
        model = TripTicket
        fields = "__all__"


class FuelLogSerializer(serializers.ModelSerializer):
    driver_detail = RiderSerializer(source="driver", read_only=True)
    vehicle_detail = VehicleSerializer(source="vehicle", read_only=True)
    total_fuel = serializers.FloatField(read_only=True)

    class Meta:
        model = FuelLog
        fields = "__all__"


class VehicleTelemetrySerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)
    driver_name = serializers.CharField(source="driver.driver_name", read_only=True)

    class Meta:
        model = VehicleTelemetry
        fields = "__all__"


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)
    vehicle_make_model = serializers.CharField(
        source="vehicle.__str__", read_only=True
    )

    class Meta:
        model = MaintenanceSchedule
        fields = "__all__"


class MaintenanceAlertSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)
    vehicle_make_model = serializers.CharField(
        source="vehicle.__str__", read_only=True
    )
    current_odometer = serializers.FloatField(
        source="vehicle.mileage", read_only=True
    )

    class Meta:
        model = MaintenanceAlert
        fields = "__all__"


class MaintenanceLogSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)

    class Meta:
        model = MaintenanceLog
        fields = "__all__"


class DriverPerformanceSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source="driver.driver_name", read_only=True)
    assigned_vehicle = serializers.CharField(
        source="driver.assigned_vehicle.plate_number", read_only=True
    )

    class Meta:
        model = DriverPerformance
        fields = "__all__"

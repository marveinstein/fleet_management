from rest_framework import serializers
from .models import Vehicle, Rider, TripTicket, FuelLog


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"


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

    class Meta:
        model = FuelLog
        fields = "__all__"


# class ReceiptTrackingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReceiptTracking
#         fields = "__all__"

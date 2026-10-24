import csv
import random
from datetime import datetime, timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, Avg, F, Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token

from .models import (
    Vehicle, Rider, TripTicket, FuelLog, VehicleTelemetry,
    MaintenanceSchedule, MaintenanceAlert, MaintenanceLog,
    DriverPerformance, UserProfile
)
from .serializers import (
    VehicleSerializer, RiderSerializer, TripTicketSerializer, FuelLogSerializer,
    VehicleTelemetrySerializer, MaintenanceScheduleSerializer, MaintenanceAlertSerializer,
    MaintenanceLogSerializer, DriverPerformanceSerializer, UserSerializer
)
from .permissions import IsAdminUserRole, IsFleetManagerOrAdmin, IsDriverOwnerOrManager
from .forms import VehicleForm, RiderForm, TripTicketForm, FuelLogForm


# ==========================================
# React SPA Host View
# ==========================================
def react_app_view(request):
    """
    Renders the modern React SPA application container.
    """
    return render(request, "fleet/react_app.html")


# ==========================================
# Authentication & Role Endpoints
# ==========================================
class AuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()

        if not username or not password:
            return Response(
                {"error": "Please provide both username and password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        profile, _ = UserProfile.objects.get_or_create(user=user)

        driver_info = None
        if profile.driver_profile:
            driver_info = {
                "id": profile.driver_profile.id,
                "name": profile.driver_profile.driver_name,
                "vehicle_id": profile.driver_profile.assigned_vehicle_id,
                "vehicle_plate": (
                    profile.driver_profile.assigned_vehicle.plate_number
                    if profile.driver_profile.assigned_vehicle else None
                ),
                "safety_score": profile.driver_profile.safety_score,
            }

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": profile.role,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "driver": driver_info,
            }
        })


class AuthMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        driver_info = None
        if profile.driver_profile:
            driver_info = {
                "id": profile.driver_profile.id,
                "name": profile.driver_profile.driver_name,
                "vehicle_id": profile.driver_profile.assigned_vehicle_id,
                "vehicle_plate": (
                    profile.driver_profile.assigned_vehicle.plate_number
                    if profile.driver_profile.assigned_vehicle else None
                ),
                "safety_score": profile.driver_profile.safety_score,
            }

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": profile.role,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "driver": driver_info,
        })


class AuthLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, "auth_token"):
            request.user.auth_token.delete()
        logout(request)
        return Response({"message": "Successfully logged out."})


# ==========================================
# User Accounts ViewSet (Admin Only)
# ==========================================
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related("profile", "profile__driver_profile").order_by("id")
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsFleetManagerOrAdmin()]
        return [IsAdminUserRole()]

    @action(detail=True, methods=["post"])
    def update_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get("role")
        if new_role not in [UserProfile.ROLE_ADMIN, UserProfile.ROLE_MANAGER, UserProfile.ROLE_DRIVER]:
            return Response({"error": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = new_role
        profile.save()

        if new_role == UserProfile.ROLE_ADMIN:
            user.is_staff = True
            user.is_superuser = True
        elif new_role == UserProfile.ROLE_MANAGER:
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False
        user.save()

        return Response({"message": f"Updated {user.username} role to {new_role}."})


# ==========================================
# Core Fleet ViewSets
# ==========================================
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().order_by("vehicle_make", "vehicle_model")
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "telemetry_history"]:
            return [permissions.IsAuthenticated()]
        return [IsFleetManagerOrAdmin()]

    @action(detail=True, methods=["get"])
    def telemetry_history(self, request, pk=None):
        vehicle = self.get_object()
        limit = int(request.query_params.get("limit", 60))
        logs = vehicle.telemetry_logs.order_by("-timestamp")[:limit]
        serializer = VehicleTelemetrySerializer(reversed(list(logs)), many=True)
        return Response(serializer.data)


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.all().select_related("assigned_vehicle").order_by("driver_name")
    serializer_class = RiderSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [IsFleetManagerOrAdmin()]


class TripTicketViewSet(viewsets.ModelViewSet):
    queryset = TripTicket.objects.all().select_related("driver", "vehicle").order_by("-date", "-id")
    serializer_class = TripTicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsDriverOwnerOrManager]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        profile = getattr(user, "profile", None)
        # RBAC: Drivers only see their own trips
        if profile and profile.role == UserProfile.ROLE_DRIVER and profile.driver_profile:
            qs = qs.filter(driver=profile.driver_profile)

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        vehicle_param = self.request.query_params.get("vehicle")
        if vehicle_param:
            qs = qs.filter(vehicle_id=vehicle_param)
        driver_param = self.request.query_params.get("driver")
        if driver_param:
            qs = qs.filter(driver_id=driver_param)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, "profile", None)
        # If created by driver, ensure driver is attached
        if profile and profile.role == UserProfile.ROLE_DRIVER and profile.driver_profile:
            trip = serializer.save(driver=profile.driver_profile)
        else:
            trip = serializer.save()

        # Update vehicle mileage if trip ended with higher odometer
        if trip.end_odometer and trip.end_odometer > float(trip.vehicle.mileage):
            trip.vehicle.mileage = trip.end_odometer
            trip.vehicle.save(update_fields=["mileage", "updated_at"])
            # Check maintenance alert trigger
            _check_maintenance_alerts_for_vehicle(trip.vehicle)


class FuelLogViewSet(viewsets.ModelViewSet):
    queryset = FuelLog.objects.all().select_related("driver", "vehicle").order_by("-date", "-id")
    serializer_class = FuelLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsDriverOwnerOrManager]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        profile = getattr(user, "profile", None)
        # RBAC: Drivers only see their own fuel logs
        if profile and profile.role == UserProfile.ROLE_DRIVER and profile.driver_profile:
            qs = qs.filter(driver=profile.driver_profile)

        vehicle_param = self.request.query_params.get("vehicle")
        if vehicle_param:
            qs = qs.filter(vehicle_id=vehicle_param)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if profile and profile.role == UserProfile.ROLE_DRIVER and profile.driver_profile:
            fuel_log = serializer.save(driver=profile.driver_profile)
        else:
            fuel_log = serializer.save()

        if fuel_log.odometer_reading and fuel_log.odometer_reading > float(fuel_log.vehicle.mileage):
            fuel_log.vehicle.mileage = fuel_log.odometer_reading
            fuel_log.vehicle.save(update_fields=["mileage", "updated_at"])
            _check_maintenance_alerts_for_vehicle(fuel_log.vehicle)


# ==========================================
# Real-Time Telemetry & Live Location
# ==========================================
class TelemetryLiveView(APIView):
    """
    Returns the real-time position, speed, heading, status, and alerts
    for all active vehicles.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vehicles = Vehicle.objects.filter(status="Active").prefetch_related("assigned_riders")
        data = []
        for v in vehicles:
            rider = v.assigned_riders.filter(status="Active").first()
            data.append({
                "id": v.id,
                "plate_number": v.plate_number,
                "vehicle_make": v.vehicle_make,
                "vehicle_model": v.vehicle_model,
                "vehicle_type": v.vehicle_type,
                "fuel_type": v.fuel_type,
                "mileage": float(v.mileage),
                "latitude": v.current_latitude or 14.5995,
                "longitude": v.current_longitude or 120.9842,
                "speed": v.current_speed,
                "heading": v.current_heading,
                "fuel_level": v.current_fuel_level,
                "last_heartbeat": v.last_heartbeat.isoformat() if v.last_heartbeat else None,
                "last_address": v.last_known_address or "Transit Corridor",
                "driver_name": rider.driver_name if rider else "Unassigned",
                "open_alerts": v.maintenance_alerts.filter(status__in=["open", "scheduled"]).count(),
            })
        return Response(data)


class TelemetryIngestView(APIView):
    """
    High-throughput telemetry ingestion endpoint.
    Accepts single ping or bulk pings, updates vehicle state atomically in SQLite.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.data
        if not isinstance(payload, list):
            payload = [payload]

        created_logs = []
        updated_vehicles = {}

        with transaction.atomic():
            for item in payload:
                vehicle_id = item.get("vehicle_id")
                plate_number = item.get("plate_number")

                vehicle = None
                if vehicle_id:
                    vehicle = Vehicle.objects.filter(id=vehicle_id).first()
                elif plate_number:
                    vehicle = Vehicle.objects.filter(plate_number=plate_number).first()

                if not vehicle:
                    continue

                lat = float(item.get("latitude", vehicle.current_latitude or 14.5995))
                lng = float(item.get("longitude", vehicle.current_longitude or 120.9842))
                speed = float(item.get("speed", 0.0))
                heading = float(item.get("heading", 0.0))
                fuel_level = float(item.get("fuel_level", vehicle.current_fuel_level))
                odometer = float(item.get("odometer", vehicle.mileage))
                engine_status = item.get("engine_status", "running" if speed > 0 else "idle")
                event_type = item.get("event_type", "normal")
                ts_str = item.get("timestamp")
                ts = timezone.now() if not ts_str else timezone.datetime.fromisoformat(ts_str)

                if speed > 85.0 and event_type == "normal":
                    event_type = "speeding"

                rider = vehicle.assigned_riders.filter(status="Active").first()

                telemetry = VehicleTelemetry(
                    vehicle=vehicle,
                    driver=rider,
                    latitude=lat,
                    longitude=lng,
                    speed=speed,
                    heading=heading,
                    fuel_level=fuel_level,
                    engine_status=engine_status,
                    odometer=odometer,
                    battery_voltage=float(item.get("battery_voltage", 12.8)),
                    engine_temp=float(item.get("engine_temp", 88.0)),
                    event_type=event_type,
                    timestamp=ts,
                )
                created_logs.append(telemetry)

                vehicle.current_latitude = lat
                vehicle.current_longitude = lng
                vehicle.current_speed = speed
                vehicle.current_heading = heading
                vehicle.current_fuel_level = fuel_level
                vehicle.last_heartbeat = ts
                if odometer > float(vehicle.mileage):
                    vehicle.mileage = odometer
                updated_vehicles[vehicle.id] = vehicle

            VehicleTelemetry.objects.bulk_create(created_logs)

            for v in updated_vehicles.values():
                v.save(update_fields=[
                    "current_latitude", "current_longitude", "current_speed",
                    "current_heading", "current_fuel_level", "last_heartbeat",
                    "mileage", "updated_at"
                ])
                _check_maintenance_alerts_for_vehicle(v)

        return Response({
            "status": "success",
            "ingested_count": len(created_logs),
            "updated_vehicles": len(updated_vehicles),
        }, status=status.HTTP_201_CREATED)


class TelemetrySimulateStepView(APIView):
    """
    Simulates real-time vehicle movement tick across active vehicles.
    Powers the interactive live tracking demo simulation in the React frontend.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        vehicles = Vehicle.objects.filter(status="Active")
        updated_list = []

        with transaction.atomic():
            for v in vehicles:
                lat = v.current_latitude or 14.5995
                lng = v.current_longitude or 120.9842

                speed_state = random.choices(["moving", "cruising", "traffic", "idle"], weights=[40, 30, 20, 10])[0]
                if speed_state == "cruising":
                    current_spd = random.uniform(45.0, 72.0)
                elif speed_state == "moving":
                    current_spd = random.uniform(25.0, 44.0)
                elif speed_state == "traffic":
                    current_spd = random.uniform(5.0, 18.0)
                else:
                    current_spd = 0.0

                dist_km = (current_spd / 3600.0) * 4.0
                delta_deg = dist_km / 111.0

                heading = v.current_heading + random.uniform(-15.0, 15.0)
                if heading < 0:
                    heading += 360
                elif heading >= 360:
                    heading -= 360

                import math
                rad = math.radians(heading)
                d_lat = delta_deg * math.cos(rad)
                d_lng = delta_deg * math.sin(rad)

                new_lat = lat + d_lat
                new_lng = lng + d_lng

                if not (14.20 <= new_lat <= 14.85):
                    new_lat = 14.5995 + random.uniform(-0.05, 0.05)
                if not (120.80 <= new_lng <= 121.20):
                    new_lng = 120.9842 + random.uniform(-0.05, 0.05)

                new_fuel = max(5.0, round(v.current_fuel_level - (dist_km * 0.08), 2))
                new_mileage = round(float(v.mileage) + dist_km, 2)

                event = "normal"
                if current_spd > 70.0 and random.random() < 0.08:
                    event = "speeding"
                elif random.random() < 0.04:
                    event = random.choice(["harsh_braking", "rapid_acceleration"])

                v.current_latitude = round(new_lat, 6)
                v.current_longitude = round(new_lng, 6)
                v.current_speed = round(current_spd, 1)
                v.current_heading = round(heading, 1)
                v.current_fuel_level = new_fuel
                v.mileage = new_mileage
                v.last_heartbeat = timezone.now()
                v.save(update_fields=[
                    "current_latitude", "current_longitude", "current_speed",
                    "current_heading", "current_fuel_level", "mileage",
                    "last_heartbeat", "updated_at"
                ])

                rider = v.assigned_riders.filter(status="Active").first()
                VehicleTelemetry.objects.create(
                    vehicle=v,
                    driver=rider,
                    latitude=v.current_latitude,
                    longitude=v.current_longitude,
                    speed=v.current_speed,
                    heading=v.current_heading,
                    fuel_level=v.current_fuel_level,
                    engine_status="running" if current_spd > 0 else "idle",
                    odometer=new_mileage,
                    event_type=event,
                    timestamp=timezone.now(),
                )

                _check_maintenance_alerts_for_vehicle(v)

                updated_list.append({
                    "id": v.id,
                    "plate_number": v.plate_number,
                    "latitude": v.current_latitude,
                    "longitude": v.current_longitude,
                    "speed": v.current_speed,
                    "heading": v.current_heading,
                    "fuel_level": v.current_fuel_level,
                    "mileage": float(v.mileage),
                    "event_type": event,
                })

        return Response({"status": "success", "updated_vehicles": updated_list})


# ==========================================
# Automated Maintenance Engine & Alerts
# ==========================================
def _check_maintenance_alerts_for_vehicle(vehicle):
    curr_km = float(vehicle.mileage)
    schedules = vehicle.maintenance_schedules.filter(is_active=True)

    for sched in schedules:
        if curr_km >= sched.next_due_km:
            alert, created = MaintenanceAlert.objects.get_or_create(
                vehicle=vehicle,
                schedule=sched,
                status__in=["open", "scheduled"],
                defaults={
                    "service_type": sched.get_service_type_display(),
                    "severity": "critical",
                    "status": "open",
                    "message": f"{sched.get_service_type_display()} is overdue by {int(curr_km - sched.next_due_km)} KM on {vehicle.plate_number}!",
                    "current_odometer": curr_km,
                    "due_odometer": sched.next_due_km,
                    "notes": "Automated trigger: Mileage crossed service threshold.",
                }
            )
            if not created and alert.severity != "critical":
                alert.severity = "critical"
                alert.message = f"{sched.get_service_type_display()} is overdue by {int(curr_km - sched.next_due_km)} KM on {vehicle.plate_number}!"
                alert.current_odometer = curr_km
                alert.save()

        elif curr_km >= sched.next_due_km - 500:
            MaintenanceAlert.objects.get_or_create(
                vehicle=vehicle,
                schedule=sched,
                status__in=["open", "scheduled"],
                defaults={
                    "service_type": sched.get_service_type_display(),
                    "severity": "warning",
                    "status": "open",
                    "message": f"{sched.get_service_type_display()} is due in {int(sched.next_due_km - curr_km)} KM on {vehicle.plate_number}.",
                    "current_odometer": curr_km,
                    "due_odometer": sched.next_due_km,
                    "notes": "Automated warning: Service interval approaching within 500 KM.",
                }
            )


class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceSchedule.objects.all().select_related("vehicle").order_by("next_due_km")
    serializer_class = MaintenanceScheduleSerializer
    permission_classes = [IsFleetManagerOrAdmin]


class MaintenanceAlertViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceAlert.objects.all().select_related("vehicle", "schedule").order_by("-created_at")
    serializer_class = MaintenanceAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        severity_filter = self.request.query_params.get("severity")
        vehicle_id = self.request.query_params.get("vehicle")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if severity_filter:
            qs = qs.filter(severity=severity_filter)
        if vehicle_id:
            qs = qs.filter(vehicle_id=vehicle_id)
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsFleetManagerOrAdmin])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        cost = float(request.data.get("cost", 0.0))
        technician = request.data.get("technician", "Authorized Technician")
        service_provider = request.data.get("service_provider", "Fleet Service Center")
        notes = request.data.get("notes", "Routine service completed and verified.")

        with transaction.atomic():
            alert.status = "resolved"
            alert.resolved_at = timezone.now()
            alert.notes = f"{alert.notes}\nResolved: {notes}".strip()
            alert.save()

            curr_km = float(alert.vehicle.mileage)

            MaintenanceLog.objects.create(
                vehicle=alert.vehicle,
                alert=alert,
                service_type=alert.service_type,
                service_date=timezone.now().date(),
                odometer_at_service=curr_km,
                cost=cost,
                service_provider=service_provider,
                technician=technician,
                notes=notes,
            )

            if alert.schedule:
                sched = alert.schedule
                sched.last_service_km = curr_km
                sched.last_service_date = timezone.now().date()
                sched.next_due_km = curr_km + sched.interval_km
                sched.next_due_date = timezone.now().date() + timedelta(days=sched.interval_days)
                sched.save()

        return Response({"message": f"Alert #{alert.id} resolved successfully and schedule updated."})


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceLog.objects.all().select_related("vehicle", "alert").order_by("-service_date", "-id")
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsFleetManagerOrAdmin]


# ==========================================
# Driver Performance Analytics View
# ==========================================
class DriverPerformanceAnalyticsView(APIView):
    """
    Driver performance analytics, leaderboard, safety scores, and violation stats.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        riders = Rider.objects.all().select_related("assigned_vehicle").order_by("-safety_score")
        results = []

        for r in riders:
            trips = TripTicket.objects.filter(driver=r)
            fuel = FuelLog.objects.filter(driver=r)
            telemetry = VehicleTelemetry.objects.filter(driver=r)

            total_trips = trips.count()
            total_dist = sum(t.total_distance for t in trips)
            total_fuel = float(fuel.aggregate(total=Sum("liters"))["total"] or 0.0)
            avg_efficiency = round(total_dist / total_fuel, 2) if total_fuel > 0 else 0.0

            harsh_brakes = telemetry.filter(event_type="harsh_braking").count()
            rapid_accels = telemetry.filter(event_type="rapid_acceleration").count()
            speeding_evts = telemetry.filter(event_type="speeding").count()

            results.append({
                "id": r.id,
                "name": r.driver_name,
                "license_number": r.license_number,
                "status": r.status,
                "assigned_vehicle": r.assigned_vehicle.plate_number if r.assigned_vehicle else "None",
                "vehicle_model": f"{r.assigned_vehicle.vehicle_make} {r.assigned_vehicle.vehicle_model}" if r.assigned_vehicle else "",
                "safety_score": r.safety_score,
                "total_trips": total_trips,
                "total_distance_km": round(total_dist, 1),
                "total_fuel_liters": round(total_fuel, 1),
                "fuel_efficiency_km_l": avg_efficiency,
                "harsh_braking_events": harsh_brakes,
                "rapid_acceleration_events": rapid_accels,
                "speeding_events": speeding_evts,
            })

        return Response(results)


# ==========================================
# Comprehensive Monthly Efficiency Reports
# ==========================================
class MonthlyEfficiencyReportView(APIView):
    """
    Comprehensive monthly efficiency analytics aggregating:
    - Total fuel consumption and cost
    - Total mileage and cost-per-km
    - Fleet average fuel economy (km/L)
    - Maintenance expenditure
    - Vehicle efficiency breakdown
    - Supports JSON and CSV export
    """
    permission_classes = [permissions.IsAuthenticated]

    def perform_content_negotiation(self, request, force=False):
        if request.query_params.get('format') == 'csv' or request.query_params.get('export') == 'csv':
            from rest_framework.renderers import BaseRenderer
            class PassthroughRenderer(BaseRenderer):
                media_type = 'text/csv'
                format = 'csv'
                def render(self, data, accepted_media_type=None, renderer_context=None):
                    return data
            return (PassthroughRenderer(), 'text/csv')
        return super().perform_content_negotiation(request, force=force)

    def get(self, request):
        export_csv = (
            request.query_params.get("format") == "csv"
            or request.query_params.get("export") == "csv"
            or request.GET.get("format") == "csv"
            or request.GET.get("export") == "csv"
        )
        months_count = int(request.query_params.get("months", 6))

        today = timezone.now().date()
        report_data = []

        for m in range(months_count - 1, -1, -1):
            ref_date = today - timedelta(days=m * 30)
            start_date = ref_date.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=1)

            month_label = start_date.strftime("%B %Y")
            month_key = start_date.strftime("%Y-%m")

            trips = TripTicket.objects.filter(date__gte=start_date, date__lt=end_date)
            trips_count = trips.count()
            total_km = sum(t.total_distance for t in trips)

            fuel_logs = FuelLog.objects.filter(date__gte=start_date, date__lt=end_date)
            fuel_stats = fuel_logs.aggregate(
                total_liters=Sum("liters"),
                total_cost=Sum("total_amount")
            )
            total_liters = float(fuel_stats["total_liters"] or 0.0)
            total_fuel_cost = float(fuel_stats["total_cost"] or 0.0)

            maint_logs = MaintenanceLog.objects.filter(service_date__gte=start_date, service_date__lt=end_date)
            total_maint_cost = float(maint_logs.aggregate(total=Sum("cost"))["total"] or 0.0)
            maint_count = maint_logs.count()

            avg_km_per_liter = round(total_km / total_liters, 2) if total_liters > 0 else 0.0
            total_operating_cost = round(total_fuel_cost + total_maint_cost, 2)
            cost_per_km = round(total_operating_cost / total_km, 2) if total_km > 0 else 0.0

            report_data.append({
                "month_key": month_key,
                "month_label": month_label,
                "trips_count": trips_count,
                "total_distance_km": round(total_km, 1),
                "total_fuel_liters": round(total_liters, 1),
                "total_fuel_cost": round(total_fuel_cost, 2),
                "maintenance_events": maint_count,
                "total_maintenance_cost": round(total_maint_cost, 2),
                "total_operating_cost": total_operating_cost,
                "fleet_km_per_liter": avg_km_per_liter,
                "cost_per_km": cost_per_km,
            })

        if export_csv:
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="fleet_monthly_efficiency_{today.strftime("%Y%m%d")}.csv"'
            writer = csv.writer(response)
            writer.writerow([
                "Month", "Trips Count", "Total Distance (KM)", "Fuel (Liters)",
                "Fuel Cost ($)", "Maintenance Cost ($)", "Total Cost ($)",
                "Fleet Economy (KM/L)", "Cost per KM ($/KM)"
            ])
            for r in report_data:
                writer.writerow([
                    r["month_label"], r["trips_count"], r["total_distance_km"],
                    r["total_fuel_liters"], r["total_fuel_cost"], r["total_maintenance_cost"],
                    r["total_operating_cost"], r["fleet_km_per_liter"], r["cost_per_km"]
                ])
            return response

        total_period_dist = sum(r["total_distance_km"] for r in report_data)
        total_period_fuel = sum(r["total_fuel_liters"] for r in report_data)
        total_period_cost = sum(r["total_operating_cost"] for r in report_data)
        avg_fleet_economy = round(total_period_dist / total_period_fuel, 2) if total_period_fuel > 0 else 0.0

        return Response({
            "summary": {
                "period_distance_km": round(total_period_dist, 1),
                "period_fuel_liters": round(total_period_fuel, 1),
                "period_total_spend": round(total_period_cost, 2),
                "avg_fleet_economy_km_l": avg_fleet_economy,
                "avg_cost_per_km": round(total_period_cost / total_period_dist, 2) if total_period_dist > 0 else 0.0,
            },
            "monthly_breakdown": report_data,
        })


# ==========================================
# Legacy Views (Preserved for compatibility)
# ==========================================
def dashboard_view(request):
    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status="Active").count()
    total_riders = Rider.objects.count()
    total_trips = TripTicket.objects.count()
    fuel_stats = FuelLog.objects.aggregate(
        total_liters=Sum("liters"), total_cost=Sum("total_amount")
    )
    recent_trips = TripTicket.objects.select_related("driver", "vehicle").order_by("-date", "-id")[:5]
    recent_fuel = FuelLog.objects.select_related("driver", "vehicle").order_by("-date", "-id")[:5]

    context = {
        "total_vehicles": total_vehicles,
        "active_vehicles": active_vehicles,
        "total_riders": total_riders,
        "total_trips": total_trips,
        "total_fuel_liters": fuel_stats["total_liters"] or 0,
        "total_fuel_cost": fuel_stats["total_cost"] or 0,
        "recent_trips": recent_trips,
        "recent_fuel": recent_fuel,
    }
    return render(request, "fleet/dashboard.html", context)


def entry_forms_view(request):
    return redirect("fuel_entry")


def fuel_entry_view(request):
    fuel_form = FuelLogForm(request.POST or None, prefix="fuel")
    if request.method == "POST":
        if fuel_form.is_valid():
            fuel_form.save()
            messages.success(request, "Fuel Log logged successfully!")
            return redirect("fuel_entry")
        messages.error(request, "Please fix errors in the submitted form.")

    recent_fuel = FuelLog.objects.select_related("driver", "vehicle").order_by("-date", "-id")[:10]
    return render(
        request, "fleet/fuel_entry_form.html",
        {"fuel_form": fuel_form, "recent_fuel": recent_fuel}
    )


def trip_entry_view(request):
    trip_form = TripTicketForm(request.POST or None, prefix="trip")
    if request.method == "POST":
        if trip_form.is_valid():
            trip_form.save()
            messages.success(request, "Trip Ticket created successfully!")
            return redirect("trip_entry")
        messages.error(request, "Please fix errors in the submitted form.")

    recent_trips = TripTicket.objects.select_related("driver", "vehicle").order_by("-date", "-id")[:10]
    return render(
        request, "fleet/trip_entry_form.html",
        {"trip_form": trip_form, "recent_trips": recent_trips}
    )


def manage_riders_vehicles_view(request):
    vehicles = Vehicle.objects.all().order_by("-id")
    riders = Rider.objects.select_related("assigned_vehicle").all().order_by("-id")

    vehicle_form = VehicleForm(prefix="vehicle")
    rider_form = RiderForm(prefix="rider")
    open_form = None

    if request.method == "POST":
        if "submit_vehicle" in request.POST:
            vehicle_form = VehicleForm(request.POST, prefix="vehicle")
            open_form = "vehicle"
            if vehicle_form.is_valid():
                vehicle_form.save()
                messages.success(request, "Vehicle saved successfully!")
                return redirect("manage_riders_vehicles")
            messages.error(request, "Please fix the errors in the vehicle form.")
        elif "submit_rider" in request.POST:
            rider_form = RiderForm(request.POST, prefix="rider")
            open_form = "rider"
            if rider_form.is_valid():
                rider_form.save()
                messages.success(request, "Rider / Driver saved successfully!")
                return redirect("manage_riders_vehicles")
            messages.error(request, "Please fix the errors in the rider form.")

    context = {
        "vehicles": vehicles,
        "riders": riders,
        "vehicle_form": vehicle_form,
        "rider_form": rider_form,
        "open_form": open_form,
    }
    return render(request, "fleet/management.html", context)

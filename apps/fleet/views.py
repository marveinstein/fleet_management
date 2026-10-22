from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, Avg
from django.contrib import messages
from rest_framework import viewsets
from .models import Vehicle, Rider, TripTicket, FuelLog, ReceiptTracking
from .forms import VehicleForm, RiderForm, TripTicketForm, FuelLogForm
from .serializers import (
    VehicleSerializer,
    RiderSerializer,
    TripTicketSerializer,
    FuelLogSerializer,
)


def dashboard_view(request):
    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status="Active").count()
    total_riders = Rider.objects.count()
    total_trips = TripTicket.objects.count()

    fuel_stats = FuelLog.objects.aggregate(
        total_liters=Sum("liters"), total_cost=Sum("total_amount")
    )

    recent_trips = TripTicket.objects.select_related("driver", "vehicle").order_by(
        "-date", "-id"
    )[:5]
    recent_fuel = FuelLog.objects.select_related("driver", "vehicle").order_by(
        "-date", "-id"
    )[:5]

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

    recent_fuel = FuelLog.objects.select_related("driver", "vehicle").order_by(
        "-date", "-id"
    )[:10]
    return render(
        request,
        "fleet/fuel_entry_form.html",
        {"fuel_form": fuel_form, "recent_fuel": recent_fuel},
    )


def trip_entry_view(request):
    trip_form = TripTicketForm(request.POST or None, prefix="trip")
    if request.method == "POST":
        if trip_form.is_valid():
            trip_form.save()
            messages.success(request, "Trip Ticket created successfully!")
            return redirect("trip_entry")
        messages.error(request, "Please fix errors in the submitted form.")

    recent_trips = TripTicket.objects.select_related("driver", "vehicle").order_by(
        "-date", "-id"
    )[:10]
    return render(
        request,
        "fleet/trip_entry_form.html",
        {"trip_form": trip_form, "recent_trips": recent_trips},
    )


def manage_riders_vehicles_view(request):
    vehicles = Vehicle.objects.all().order_by("-id")
    riders = Rider.objects.select_related("assigned_vehicle").all().order_by("-id")

    vehicle_form = VehicleForm(prefix="vehicle")
    rider_form = RiderForm(prefix="rider")

    if request.method == "POST":
        if "submit_vehicle" in request.POST:
            v_form = VehicleForm(request.POST, prefix="vehicle")
            if v_form.is_valid():
                v_form.save()
                messages.success(request, "Vehicle saved successfully!")
                return redirect("manage_riders_vehicles")
        elif "submit_rider" in request.POST:
            r_form = RiderForm(request.POST, prefix="rider")
            if r_form.is_valid():
                r_form.save()
                messages.success(request, "Rider / Driver saved successfully!")
                return redirect("manage_riders_vehicles")

    context = {
        "vehicles": vehicles,
        "riders": riders,
        "vehicle_form": vehicle_form,
        "rider_form": rider_form,
    }
    return render(request, "fleet/management.html", context)


# API ViewSets
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer


class TripTicketViewSet(viewsets.ModelViewSet):
    queryset = TripTicket.objects.all()
    serializer_class = TripTicketSerializer


class FuelLogViewSet(viewsets.ModelViewSet):
    queryset = FuelLog.objects.all()
    serializer_class = FuelLogSerializer

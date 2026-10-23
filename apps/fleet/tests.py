from django.test import TestCase

from django.urls import reverse

from .models import FuelLog, Rider, TripTicket, Vehicle


class TripEntrySubmissionTests(TestCase):
    def test_submits_trip_without_unrendered_destination_and_purpose(self):
        vehicle = Vehicle.objects.create(plate_number="TEST-001")
        rider = Rider.objects.create(
            driver_name="Test Driver",
        )

        response = self.client.post(
            reverse("trip_entry"),
            {
                "trip-ticket_number": "TEST-TICKET-001",
                "trip-date": "2026-10-21",
                "trip-driver": rider.pk,
                "trip-vehicle": vehicle.pk,
                "trip-start_odometer": "100",
                "trip-end_odometer": "120",
                "action_type": "save_trip",
            },
        )

        self.assertRedirects(response, reverse("trip_entry"))
        trip = TripTicket.objects.get(ticket_number="TEST-TICKET-001")
        self.assertEqual(trip.destination, "")
        self.assertEqual(trip.purpose, "")


class FuelEntrySubmissionTests(TestCase):
    def test_submits_fuel_without_unrendered_station_and_odometer(self):
        vehicle = Vehicle.objects.create(plate_number="TEST-002")
        rider = Rider.objects.create(
            driver_name="Test Fuel Driver",
        )

        response = self.client.post(
            reverse("fuel_entry"),
            {
                "fuel-date": "2026-10-21",
                "fuel-driver": rider.pk,
                "fuel-vehicle": vehicle.pk,
                "fuel-liters": "10",
                "fuel-cost_per_liter": "2.50",
                "fuel-total_amount": "25.00",
            },
        )

        self.assertRedirects(response, reverse("fuel_entry"))
        fuel_log = FuelLog.objects.get(vehicle=vehicle)
        self.assertEqual(fuel_log.fuel_station, "")
        self.assertEqual(fuel_log.odometer_reading, 0)


class ManagementFormTests(TestCase):
    def test_invalid_rider_form_is_returned_for_the_rider_dialog(self):
        response = self.client.post(
            reverse("manage_riders_vehicles"),
            {
                "submit_rider": "Add Rider",
                "rider-driver_name": "",
                "rider-status": "Active",
                "rider-assigned_vehicle": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["rider_form"].errors)
        self.assertEqual(response.context["open_form"], "rider")

    def test_invalid_vehicle_form_is_returned_for_the_vehicle_dialog(self):
        response = self.client.post(
            reverse("manage_riders_vehicles"),
            {
                "submit_vehicle": "Add Vehicle",
                "vehicle-plate_number": "",
                "vehicle-vehicle_make": "Toyota",
                "vehicle-vehicle_model": "Hilux",
                "vehicle-vehicle_type": "SED",
                "vehicle-fuel_type": "GAS",
                "vehicle-status": "Active",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["vehicle_form"].errors)
        self.assertEqual(response.context["open_form"], "vehicle")

    def test_submits_rider_from_the_management_page(self):
        response = self.client.post(
            reverse("manage_riders_vehicles"),
            {
                "submit_rider": "Add Rider",
                "rider-driver_name": "Test Management Rider",
                "rider-status": "Active",
                "rider-assigned_vehicle": "",
            },
        )

        self.assertRedirects(response, reverse("manage_riders_vehicles"))
        self.assertTrue(
            Rider.objects.filter(driver_name="Test Management Rider").exists()
        )

    def test_submits_vehicle_from_the_management_page(self):
        response = self.client.post(
            reverse("manage_riders_vehicles"),
            {
                "submit_vehicle": "Add Vehicle",
                "vehicle-plate_number": "TEST-MANAGEMENT-001",
                "vehicle-vehicle_make": "Toyota",
                "vehicle-vehicle_model": "Hilux",
                "vehicle-vehicle_type": "SED",
                "vehicle-fuel_type": "GAS",
                "vehicle-status": "Active",
            },
        )

        self.assertRedirects(response, reverse("manage_riders_vehicles"))
        self.assertTrue(
            Vehicle.objects.filter(plate_number="TEST-MANAGEMENT-001").exists()
        )

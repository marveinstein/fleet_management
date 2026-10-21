from django.test import TestCase

from django.urls import reverse

from .models import FuelLog, Rider, TripTicket, Vehicle


class TripEntrySubmissionTests(TestCase):
    def test_submits_trip_without_unrendered_destination_and_purpose(self):
        vehicle = Vehicle.objects.create(plate_number="TEST-001")
        rider = Rider.objects.create(
            driver_name="Test Driver",
            license_number="TEST-LICENSE-001",
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
            license_number="TEST-LICENSE-002",
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

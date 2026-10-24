from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

from apps.fleet.models import (
    Vehicle,
    Rider,
    TripTicket,
    FuelLog,
    VehicleTelemetry,
    MaintenanceSchedule,
    MaintenanceAlert,
    MaintenanceLog,
    DriverPerformance,
    UserProfile,
)


class FleetSystemComprehensiveTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Admin
        self.admin_user = User.objects.create_superuser(
            username="testadmin", email="admin@test.com", password="adminpassword"
        )
        self.admin_profile, _ = UserProfile.objects.get_or_create(
            user=self.admin_user, defaults={"role": UserProfile.ROLE_ADMIN}
        )

        # Create Manager
        self.manager_user = User.objects.create_user(
            username="testmanager", email="manager@test.com", password="managerpassword"
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user, role=UserProfile.ROLE_MANAGER
        )

        # Create Driver 1 & Rider 1
        self.vehicle1 = Vehicle.objects.create(
            plate_number="FLEET-101",
            vehicle_make="Toyota",
            vehicle_model="Hilux",
            vehicle_type="TRK",
            fuel_type="DSL",
            mileage=20000.0,
            status="Active",
            current_latitude=14.5995,
            current_longitude=120.9842,
        )
        self.rider1 = Rider.objects.create(
            driver_name="Juan Dela Cruz",
            assigned_vehicle=self.vehicle1,
            status="Active",
            safety_score=96.5,
        )
        self.driver_user = User.objects.create_user(
            username="testdriver", email="driver@test.com", password="driverpassword"
        )
        self.driver_profile = UserProfile.objects.create(
            user=self.driver_user,
            role=UserProfile.ROLE_DRIVER,
            driver_profile=self.rider1,
        )

        # Create Driver 2 & Rider 2
        self.vehicle2 = Vehicle.objects.create(
            plate_number="FLEET-202",
            vehicle_make="Yamaha",
            vehicle_model="NMAX",
            vehicle_type="MTC",
            fuel_type="GAS",
            mileage=12000.0,
            status="Active",
            current_latitude=14.5800,
            current_longitude=121.0500,
        )
        self.rider2 = Rider.objects.create(
            driver_name="Pedro Santos",
            assigned_vehicle=self.vehicle2,
            status="Active",
            safety_score=92.0,
        )
        self.driver2_user = User.objects.create_user(
            username="testdriver2", email="driver2@test.com", password="driverpassword"
        )
        self.driver2_profile = UserProfile.objects.create(
            user=self.driver2_user,
            role=UserProfile.ROLE_DRIVER,
            driver_profile=self.rider2,
        )

    # 1. RBAC Authentication Tests
    def test_auth_login_admin(self):
        res = self.client.post(
            reverse("api_auth_login"),
            data=json.dumps({"username": "testadmin", "password": "adminpassword"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "admin")

    def test_auth_login_driver_returns_driver_profile(self):
        res = self.client.post(
            reverse("api_auth_login"),
            data=json.dumps({"username": "testdriver", "password": "driverpassword"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["role"], "driver")
        self.assertIsNotNone(data["user"]["driver"])
        self.assertEqual(data["user"]["driver"]["name"], "Juan Dela Cruz")
        self.assertEqual(data["user"]["driver"]["vehicle_plate"], "FLEET-101")

    # 2. RBAC Data Isolation: Driver sees only their own trips
    def test_driver_sees_only_own_trips(self):
        # Trip for Rider 1
        TripTicket.objects.create(
            ticket_number="TRIP-001",
            date=timezone.now().date(),
            driver=self.rider1,
            vehicle=self.vehicle1,
            start_odometer=20000,
            end_odometer=20050,
        )
        # Trip for Rider 2
        TripTicket.objects.create(
            ticket_number="TRIP-002",
            date=timezone.now().date(),
            driver=self.rider2,
            vehicle=self.vehicle2,
            start_odometer=12000,
            end_odometer=12080,
        )

        # Login as Driver 1
        login_res = self.client.post(
            reverse("api_auth_login"),
            data=json.dumps({"username": "testdriver", "password": "driverpassword"}),
            content_type="application/json",
        )
        token = login_res.json()["token"]

        # Request trips list
        res = self.client.get("/api/trip-tickets/", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(res.status_code, 200)
        trips = res.json().get("results", res.json())
        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0]["ticket_number"], "TRIP-001")

    # 3. High-throughput Telemetry Ingest & SQLite State Update
    def test_telemetry_ingestion_updates_vehicle(self):
        payload = [
            {
                "vehicle_id": self.vehicle1.id,
                "latitude": 14.6200,
                "longitude": 121.0300,
                "speed": 62.5,
                "heading": 180.0,
                "fuel_level": 82.5,
                "odometer": 20120.0,
                "event_type": "normal",
            }
        ]

        res = self.client.post(
            reverse("api_telemetry_ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["ingested_count"], 1)

        self.vehicle1.refresh_from_db()
        self.assertEqual(self.vehicle1.current_speed, 62.5)
        self.assertEqual(self.vehicle1.current_latitude, 14.6200)
        self.assertEqual(float(self.vehicle1.mileage), 20120.0)

    # 4. Automated Maintenance Alert Triggering
    def test_automated_maintenance_alert_trigger(self):
        schedule = MaintenanceSchedule.objects.create(
            vehicle=self.vehicle1,
            service_type="oil_change",
            interval_km=5000,
            last_service_km=20000.0,
            next_due_km=25000.0,
            is_active=True,
        )

        # Ingest telemetry pushing odometer past threshold (25050 KM)
        self.client.post(
            reverse("api_telemetry_ingest"),
            data=json.dumps(
                [
                    {
                        "vehicle_id": self.vehicle1.id,
                        "odometer": 25050.0,
                        "speed": 40.0,
                    }
                ]
            ),
            content_type="application/json",
        )

        # Verify automated critical alert created
        alert = MaintenanceAlert.objects.filter(
            vehicle=self.vehicle1, schedule=schedule
        ).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "critical")
        self.assertIn("overdue by 50 KM", alert.message)

    # 5. Alert Resolution & Maintenance Log Creation
    def test_resolve_maintenance_alert(self):
        schedule = MaintenanceSchedule.objects.create(
            vehicle=self.vehicle1,
            service_type="brake_service",
            interval_km=10000,
            last_service_km=15000.0,
            next_due_km=20000.0,
        )
        alert = MaintenanceAlert.objects.create(
            vehicle=self.vehicle1,
            schedule=schedule,
            service_type="Brake Pad & Rotor Inspection",
            severity="critical",
            status="open",
            message="Brake service overdue",
            due_odometer=20000.0,
        )

        # Admin login
        login_res = self.client.post(
            reverse("api_auth_login"),
            data=json.dumps({"username": "testadmin", "password": "adminpassword"}),
            content_type="application/json",
        )
        token = login_res.json()["token"]

        # Resolve alert
        res = self.client.post(
            f"/api/maintenance/alerts/{alert.id}/resolve/",
            data=json.dumps(
                {
                    "cost": 4500.0,
                    "technician": "Master Mechanic Santos",
                    "service_provider": "Fleet Pro Center",
                    "notes": "Replaced front and rear ceramic brake pads.",
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        self.assertEqual(res.status_code, 200)

        alert.refresh_from_db()
        self.assertEqual(alert.status, "resolved")
        self.assertIsNotNone(alert.resolved_at)

        # Check maintenance log created
        log = MaintenanceLog.objects.filter(alert=alert).first()
        self.assertIsNotNone(log)
        self.assertEqual(float(log.cost), 4500.0)

        # Check schedule updated
        schedule.refresh_from_db()
        self.assertEqual(
            schedule.next_due_km, float(self.vehicle1.mileage) + schedule.interval_km
        )

    # 6. Monthly Efficiency Reports & CSV Export
    def test_monthly_efficiency_reports_json_and_csv(self):
        # Create trip and fuel records for current month
        TripTicket.objects.create(
            ticket_number="TRIP-M01",
            date=timezone.now().date(),
            driver=self.rider1,
            vehicle=self.vehicle1,
            start_odometer=20000,
            end_odometer=20150,  # 150 KM
        )
        FuelLog.objects.create(
            receipt_number="RCP-M01",
            date=timezone.now().date(),
            fuel_station="Shell BGC",
            driver=self.rider1,
            vehicle=self.vehicle1,
            liters=15.0,
            cost_per_liter=60.0,
            total_amount=900.0,
        )

        login_res = self.client.post(
            reverse("api_auth_login"),
            data=json.dumps({"username": "testadmin", "password": "adminpassword"}),
            content_type="application/json",
        )
        token = login_res.json()["token"]

        # JSON response
        res = self.client.get(
            "/api/reports/monthly/?months=1",
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("summary", data)
        self.assertIn("monthly_breakdown", data)
        self.assertGreater(data["summary"]["period_distance_km"], 0)

        # CSV Export
        csv_res = self.client.get(
            "/api/reports/monthly/?format=csv&months=1",
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res["Content-Type"], "text/csv")
        self.assertIn("Fleet Economy (KM/L)", csv_res.content.decode("utf-8"))

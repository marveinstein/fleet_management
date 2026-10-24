import random
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
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


class Command(BaseCommand):
    help = "Seed comprehensive fleet management demonstration data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting fleet data seeding..."))

        # 1. Setup Users & Roles
        users_data = [
            ("admin", "admin123", UserProfile.ROLE_ADMIN, None, "Admin Officer"),
            (
                "manager",
                "manager123",
                UserProfile.ROLE_MANAGER,
                None,
                "Fleet Supervisor",
            ),
            (
                "driver1",
                "driver123",
                UserProfile.ROLE_DRIVER,
                "Diosdado Apa",
                "Lead Delivery Driver",
            ),
            (
                "driver2",
                "driver123",
                UserProfile.ROLE_DRIVER,
                "Dino Bargamento",
                "Senior Courier Driver",
            ),
        ]

        for username, password, role, rider_name, full_name in users_data:
            user, created = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.first_name = full_name.split()[0]
            user.last_name = " ".join(full_name.split()[1:])
            user.email = f"{username}@fleetops.com"
            if role == UserProfile.ROLE_ADMIN:
                user.is_staff = True
                user.is_superuser = True
            elif role == UserProfile.ROLE_MANAGER:
                user.is_staff = True
                user.is_superuser = False
            else:
                user.is_staff = False
                user.is_superuser = False
            user.save()

            rider_profile = None
            if rider_name:
                rider_profile = Rider.objects.filter(
                    driver_name__icontains=rider_name.split()[0]
                ).first()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.phone_number = f"+63 917 555 {random.randint(1000, 9999)}"
            profile.driver_profile = rider_profile
            profile.save()

            self.stdout.write(f"[OK] Setup User: {username} [{role}]")

        # 2. Update existing vehicles with realistic telemetry / mileage
        # Base coordinates: Metro Manila Logistics Corridor
        base_coords = [
            (14.5547, 121.0244, "Makati Logistics Hub"),
            (14.5839, 121.0593, "Ortigas Central Terminal"),
            (14.6507, 121.0345, "Quezon City Transit Depot"),
            (14.5378, 121.0014, "Pasay Port Facility"),
            (14.5176, 121.0509, "Taguig Distribution Center"),
            (14.6091, 120.9899, "Manila North Pier"),
            (14.4445, 121.0453, "Alabang South Gate"),
            (14.5764, 121.0851, "Pasig Industrial Zone"),
            (14.6760, 121.0437, "North Fairview Waypoint"),
            (14.5583, 121.0188, "Buendia Transit Hub"),
        ]

        vehicles = list(Vehicle.objects.all())
        if not vehicles:
            # Create sample vehicles if none exist
            makes_models = [
                ("Toyota", "Hilux", "TRK", "DSL"),
                ("Yamaha", "NMAX", "MTC", "GAS"),
                ("Isuzu", "D-Max", "TRK", "DSL"),
                ("Toyota", "Avanza", "VAN", "GAS"),
                ("Ford", "F-150", "TRK", "DSL"),
                ("Mitsubishi", "Outlander", "SUV", "HYB"),
            ]
            for i, (make, model, vtype, ftype) in enumerate(makes_models):
                v = Vehicle.objects.create(
                    plate_number=f"ABC-{1000 + i}",
                    vehicle_make=make,
                    vehicle_model=model,
                    vehicle_type=vtype,
                    fuel_type=ftype,
                    mileage=random.randint(12000, 48000),
                    status="Active",
                )
                vehicles.append(v)

        for i, vehicle in enumerate(vehicles):
            coord = base_coords[i % len(base_coords)]
            jitter_lat = coord[0] + random.uniform(-0.02, 0.02)
            jitter_lng = coord[1] + random.uniform(-0.02, 0.02)

            speed = random.choice([0.0, 0.0, 24.5, 42.0, 58.3, 65.0])
            vehicle.current_latitude = jitter_lat
            vehicle.current_longitude = jitter_lng
            vehicle.current_speed = speed
            vehicle.current_heading = random.uniform(0, 360)
            vehicle.current_fuel_level = round(random.uniform(40.0, 95.0), 1)
            vehicle.last_heartbeat = timezone.now() - timedelta(
                minutes=random.randint(1, 15)
            )
            vehicle.last_known_address = f"Near {coord[2]}"
            if float(vehicle.mileage) < 1000:
                vehicle.mileage = random.randint(15000, 52000)
            vehicle.save()

            # Seed telemetry historical points (breadcrumbs)
            prev_lat, prev_lng = jitter_lat, jitter_lng
            now = timezone.now()
            telemetry_records = []
            for step in range(15):
                ts = now - timedelta(minutes=(15 - step) * 2)
                prev_lat += random.uniform(-0.003, 0.003)
                prev_lng += random.uniform(-0.003, 0.003)
                spd = random.uniform(15.0, 68.0) if speed > 0 else 0.0
                event = "normal"
                if random.random() < 0.1:
                    event = random.choice(
                        ["harsh_braking", "rapid_acceleration", "speeding"]
                    )

                telemetry_records.append(
                    VehicleTelemetry(
                        vehicle=vehicle,
                        latitude=prev_lat,
                        longitude=prev_lng,
                        speed=round(spd, 1),
                        heading=round(random.uniform(0, 360), 1),
                        fuel_level=round(
                            max(10.0, vehicle.current_fuel_level - (15 - step) * 0.2), 1
                        ),
                        engine_status="running" if spd > 0 else "idle",
                        odometer=float(vehicle.mileage) - (15 - step) * 1.5,
                        battery_voltage=round(random.uniform(12.4, 14.2), 2),
                        engine_temp=round(random.uniform(82.0, 93.0), 1),
                        event_type=event,
                        timestamp=ts,
                    )
                )
            VehicleTelemetry.objects.bulk_create(telemetry_records)

        self.stdout.write(
            f"[OK] Updated {len(vehicles)} vehicles with live telemetry & breadcrumbs."
        )

        # 3. Setup Riders & Performance Scores
        riders = list(Rider.objects.all())
        for idx, rider in enumerate(riders):
            if not rider.license_number:
                rider.license_number = f"N01-20-{random.randint(100000, 999999)}"
            if not rider.contact_number:
                rider.contact_number = f"+63 928 412 {random.randint(1000, 9999)}"
            rider.safety_score = round(random.uniform(88.0, 99.0), 1)
            rider.total_trips = random.randint(45, 160)
            rider.total_distance = round(random.uniform(2800.0, 8900.0), 1)
            rider.save()

        # 4. Maintenance Schedules and Automated Alerts
        service_types = [
            ("oil_change", "Engine Oil & Filter Change", 5000, 180),
            ("brake_service", "Brake Pad & Rotor Inspection", 10000, 360),
            ("tire_rotation", "Tire Rotation & Wheel Alignment", 8000, 180),
            ("annual_inspection", "Comprehensive Fleet Safety Inspection", 20000, 365),
        ]

        MaintenanceSchedule.objects.all().delete()
        MaintenanceAlert.objects.all().delete()
        MaintenanceLog.objects.all().delete()

        for v_idx, vehicle in enumerate(vehicles[:8]):
            curr_km = float(vehicle.mileage)
            for stype, sname, int_km, int_days in service_types:
                # Alternate some due soon, some overdue
                if v_idx == 0 and stype == "oil_change":
                    last_km = curr_km - (int_km + 450)  # Overdue!
                    next_km = curr_km - 450
                elif v_idx == 1 and stype == "brake_service":
                    last_km = curr_km - (int_km - 200)  # Due soon
                    next_km = curr_km + 200
                else:
                    last_km = curr_km - random.randint(500, int_km - 1000)
                    next_km = last_km + int_km

                sched = MaintenanceSchedule.objects.create(
                    vehicle=vehicle,
                    service_type=stype,
                    interval_km=int_km,
                    interval_days=int_days,
                    last_service_km=last_km,
                    last_service_date=timezone.now().date()
                    - timedelta(days=random.randint(30, 120)),
                    next_due_km=next_km,
                    next_due_date=timezone.now().date()
                    + timedelta(days=random.randint(10, 90)),
                    is_active=True,
                )

                # Generate automated alerts
                if curr_km >= next_km:
                    MaintenanceAlert.objects.create(
                        vehicle=vehicle,
                        schedule=sched,
                        service_type=sname,
                        severity="critical",
                        status="open",
                        message=f"{sname} is overdue by {int(curr_km - next_km)} KM on {vehicle.plate_number}!",
                        current_odometer=curr_km,
                        due_odometer=next_km,
                        notes="Automated system trigger: Vehicle exceeded recommended service mileage threshold.",
                    )
                elif curr_km >= next_km - 500:
                    MaintenanceAlert.objects.create(
                        vehicle=vehicle,
                        schedule=sched,
                        service_type=sname,
                        severity="warning",
                        status="open",
                        message=f"{sname} is due in {int(next_km - curr_km)} KM on {vehicle.plate_number}.",
                        current_odometer=curr_km,
                        due_odometer=next_km,
                        notes="Automated system warning: Service mileage interval approaching.",
                    )

            # Add completed historical maintenance log
            MaintenanceLog.objects.create(
                vehicle=vehicle,
                service_type="Routine Scheduled Oil Service & Filter",
                service_date=timezone.now().date()
                - timedelta(days=random.randint(40, 160)),
                odometer_at_service=curr_km - 4800,
                cost=round(random.uniform(2200.0, 5800.0), 2),
                service_provider="Shell Helix Auto Center",
                technician="Engr. J. Santos",
                notes="Standard 10W-40 synthetic oil replaced, genuine OEM oil filter installed.",
            )

        self.stdout.write(
            "[OK] Seeded maintenance schedules, alerts, and service logs."
        )

        # 5. Seed Historical Trip Tickets and Fuel Logs for past 6 months
        routes = [
            (
                "Manila North Harbor",
                "BGC Taguig Logistics Center",
                "Commercial Goods Transit",
            ),
            (
                "Quezon City Hub",
                "Ortigas Business District",
                "Parcel & Freight Dispatch",
            ),
            (
                "Pasay Cold Storage",
                "Makati Commercial Strip",
                "Perishable Groceries Courier",
            ),
            (
                "Alabang Warehouse",
                "Pasig Industrial Park",
                "Hardware & Equipment Supply",
            ),
            (
                "Navotas Port Terminal",
                "Cainta Distribution Depot",
                "General Fleet Logistics",
            ),
        ]
        stations = [
            "Shell Express Buendia",
            "Petron Fleetway BGC",
            "Caltex Highway Hub",
            "Total Mega Station",
        ]

        today = timezone.now().date()
        months_back = 6

        # Wipe old trips and logs to keep clean demo history
        TripTicket.objects.all().delete()
        FuelLog.objects.all().delete()

        ticket_counter = 1001
        receipt_counter = 5001

        for m in range(months_back, -1, -1):
            month_date = today - timedelta(days=m * 30)
            trips_in_month = random.randint(15, 25)

            for _ in range(trips_in_month):
                trip_date = month_date + timedelta(days=random.randint(0, 27))
                if trip_date > today:
                    continue

                veh = random.choice(vehicles)
                driver = random.choice(riders) if riders else None
                if not driver:
                    continue

                origin, dest, purpose = random.choice(routes)
                dist = random.uniform(18.0, 95.0)
                start_odo = float(veh.mileage) - (m * 1200) + random.uniform(10, 400)
                end_odo = start_odo + dist
                fuel_cons = round(dist / random.uniform(9.5, 14.5), 2)

                TripTicket.objects.create(
                    ticket_number=f"TRIP-{ticket_counter}",
                    date=trip_date,
                    driver=driver,
                    vehicle=veh,
                    origin=origin,
                    destination=dest,
                    purpose=purpose,
                    status="Completed",
                    start_odometer=round(start_odo, 1),
                    end_odometer=round(end_odo, 1),
                    fuel_consumed_liters=fuel_cons,
                )
                ticket_counter += 1

            # Seed 8-14 fuel logs per month
            fuels_in_month = random.randint(8, 14)
            for _ in range(fuels_in_month):
                f_date = month_date + timedelta(days=random.randint(0, 27))
                if f_date > today:
                    continue

                veh = random.choice(vehicles)
                driver = random.choice(riders) if riders else None
                if not driver:
                    continue

                liters = round(random.uniform(20.0, 65.0), 2)
                price_per_l = round(random.uniform(58.50, 68.20), 2)
                total_amt = round(liters * price_per_l, 2)

                FuelLog.objects.create(
                    receipt_number=f"RCP-{receipt_counter}",
                    date=f_date,
                    fuel_station=random.choice(stations),
                    driver=driver,
                    vehicle=veh,
                    liters=liters,
                    cost_per_liter=price_per_l,
                    total_amount=total_amt,
                    odometer_reading=round(float(veh.mileage) - (m * 1100), 1),
                    notes="Full tank refill authorized under fleet fuel card.",
                )
                receipt_counter += 1

        self.stdout.write(
            f"[OK] Seeded {TripTicket.objects.count()} trips and {FuelLog.objects.count()} fuel logs."
        )

        # 6. Monthly Driver Performance records
        DriverPerformance.objects.all().delete()
        for rider in riders:
            for m in range(4, -1, -1):
                month_start = (today - timedelta(days=m * 30)).replace(day=1)
                dist = random.uniform(800.0, 2400.0)
                trips = random.randint(18, 48)
                fuel = dist / random.uniform(10.0, 14.0)
                DriverPerformance.objects.create(
                    driver=rider,
                    month=month_start,
                    total_distance_km=round(dist, 1),
                    trips_completed=trips,
                    fuel_consumed_liters=round(fuel, 1),
                    efficiency_km_per_liter=round(dist / fuel, 2),
                    safety_score=round(random.uniform(87.0, 99.0), 1),
                    harsh_braking_count=random.randint(0, 4),
                    rapid_accel_count=random.randint(0, 5),
                    speeding_count=random.randint(0, 2),
                    idling_hours=round(random.uniform(1.2, 8.5), 1),
                )

        self.stdout.write(
            self.style.SUCCESS(
                "[OK] Fleet Management demonstration dataset successfully seeded!"
            )
        )

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vehicles', views.VehicleViewSet, basename='vehicle')
router.register(r'riders', views.RiderViewSet, basename='rider')
router.register(r'trip-tickets', views.TripTicketViewSet, basename='tripticket')
router.register(r'fuel-logs', views.FuelLogViewSet, basename='fuellog')
router.register(r'maintenance/schedules', views.MaintenanceScheduleViewSet, basename='maintenanceschedule')
router.register(r'maintenance/alerts', views.MaintenanceAlertViewSet, basename='maintenancealert')
router.register(r'maintenance/logs', views.MaintenanceLogViewSet, basename='maintenancelog')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # Modern React Application Single Page App Entrypoint
    path('', views.react_app_view, name='react_app'),
    path('app/', views.react_app_view, name='react_app_sub'),
    
    # API Endpoints
    path('api/auth/login/', views.AuthLoginView.as_view(), name='api_auth_login'),
    path('api/auth/logout/', views.AuthLogoutView.as_view(), name='api_auth_logout'),
    path('api/auth/me/', views.AuthMeView.as_view(), name='api_auth_me'),
    path('api/telemetry/live/', views.TelemetryLiveView.as_view(), name='api_telemetry_live'),
    path('api/telemetry/ingest/', views.TelemetryIngestView.as_view(), name='api_telemetry_ingest'),
    path('api/telemetry/simulate-step/', views.TelemetrySimulateStepView.as_view(), name='api_telemetry_simulate'),
    path('api/analytics/driver-performance/', views.DriverPerformanceAnalyticsView.as_view(), name='api_driver_performance'),
    path('api/reports/monthly/', views.MonthlyEfficiencyReportView.as_view(), name='api_monthly_reports'),
    path('api/', include(router.urls)),

    # Legacy Server-rendered Views (Preserved)
    path('legacy/', views.dashboard_view, name='dashboard'),
    path('legacy/entries/', views.entry_forms_view, name='entry_forms'),
    path('legacy/entries/fuel/', views.fuel_entry_view, name='fuel_entry'),
    path('legacy/entries/trip/', views.trip_entry_view, name='trip_entry'),
    path('legacy/manage/', views.manage_riders_vehicles_view, name='manage_riders_vehicles'),
]

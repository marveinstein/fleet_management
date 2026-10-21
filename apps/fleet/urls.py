from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vehicles', views.VehicleViewSet)
router.register(r'riders', views.RiderViewSet)
router.register(r'trip-tickets', views.TripTicketViewSet)
router.register(r'fuel-logs', views.FuelLogViewSet)

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('entries/', views.entry_forms_view, name='entry_forms'),
    path('entries/fuel/', views.fuel_entry_view, name='fuel_entry'),
    path('entries/trip/', views.trip_entry_view, name='trip_entry'),
    path('manage/', views.manage_riders_vehicles_view, name='manage_riders_vehicles'),
    path('api/', include(router.urls)),
]

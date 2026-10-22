from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import FuelLog, Rider, TripTicket, Vehicle  # Import your model

# Register the model with default options
admin.site.register(Vehicle),
admin.site.register(Rider),
admin.site.register(TripTicket),
admin.site.register(FuelLog),

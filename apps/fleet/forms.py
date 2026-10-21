from django import forms
from .models import Vehicle, Rider, TripTicket, FuelLog


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "plate_number",
            "vehicle_make",
            "vehicle_model",
            "vehicle_type",
            "fuel_type",
            "status",
        ]
        widgets = {
            "plate_number": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "vehicle_make": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "vehicle_model": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "vehicle_type": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "fuel_type": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
        }


class RiderForm(forms.ModelForm):
    class Meta:
        model = Rider
        fields = [
            "driver_name",
            "license_number",
            "contact_number",
            "status",
            "assigned_vehicle",
        ]
        widgets = {
            "driver_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "assigned_vehicle": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
        }


class TripTicketForm(forms.ModelForm):
    class Meta:
        model = TripTicket
        fields = [
            "ticket_number",
            "driver",
            "vehicle",
            "date",
            "departure_time",
            "arrival_time",
            "start_odometer",
            "end_odometer",
            "destination",
            "purpose",
            "passengers",
        ]
        widgets = {
            "ticket_number": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none",
                }
            ),
            "driver": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "vehicle": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "vehicle_make": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "vehicle_model": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "start_odometer": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "end_odometer": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "total_distance": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["destination"].required = False
        self.fields["purpose"].required = False


class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = [
            "vehicle",
            "driver",
            "date",
            "fuel_station",
            "liters",
            "cost_per_liter",
            "total_amount",
            "odometer_reading",
            "receipt_number",
        ]
        widgets = {
            "receipt_number": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none",
                }
            ),
            "vehicle": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "driver": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
            "liters": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none",
                }
            ),
            "cost_per_liter": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none",
                }
            ),
            "total_amount": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none",
                }
            ),
            "odometer_reading": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fuel_station"].required = False
        self.fields["odometer_reading"].required = False

    def clean_odometer_reading(self):
        return self.cleaned_data["odometer_reading"] or 0

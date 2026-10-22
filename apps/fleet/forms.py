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
            "start_odometer",
            "end_odometer",
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


class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = [
            "vehicle",
            "date",
            "receipt_number",
            "driver",
            "liters",
            "cost_per_liter",
        ]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none",
                }
            ),
            "receipt_number": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
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
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["total_amount"].required = False

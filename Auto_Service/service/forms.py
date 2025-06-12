from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Appointment, Vehicle, ServiceType

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'address', 'password1', 'password2')

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['service_type', 'vehicle', 'scheduled_date', 'scheduled_time', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={
                'type': 'date',
                'min': timezone.now().date().isoformat(),
            }),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active services
        self.fields['service_type'].queryset = ServiceType.objects.all()
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['make', 'model', 'year', 'color', 'license_plate', 'vin', 'registration_date', 'mileage', 'image']
        widgets = {
            'year': forms.NumberInput(attrs={
                'min': 1900,
                'max': timezone.now().year + 1,
                'class': 'form-control'
            }),
            'registration_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'mileage': forms.NumberInput(attrs={
                'min': 0,
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'id': 'imageInput'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields:
            if not isinstance(self.fields[field].widget, forms.NumberInput):
                self.fields[field].widget.attrs['class'] = 'form-control'
        # Ensure predictable IDs for JS selectors
        id_map = {
            'vin': 'vin',
            'year': 'year',
            'license_plate': 'license_plate',
            'mileage': 'mileage',
        }
        for field, element_id in id_map.items():
            if field in self.fields:
                self.fields[field].widget.attrs['id'] = element_id 
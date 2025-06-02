from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

class BaseUser(models.Model):
    USER_TYPES = [
        ('ADMIN', 'Administrator'),
        ('OWNER', 'Owner'),
        ('MANAGER', 'Manager'),
        ('CUSTOMER', 'Customer'),
        ('SUPERVISOR', 'Supervisor'),
        ('SECRETARY', 'Secretary'),
        ('TECHNICIAN', 'Technician'),
        ('STAFF', 'Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_user_type_display()}"

class Employee(models.Model):
    base_user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                 limit_choices_to={'base_user__user_type': 'SUPERVISOR'})
    facility = models.ForeignKey('Facility', on_delete=models.SET_NULL, null=True)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.base_user.user.get_full_name()} - {self.base_user.get_user_type_display()}"

class Customer(models.Model):
    base_user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[('EMAIL', 'Email'), ('PHONE', 'Phone')],
        default='EMAIL'
    )

    def __str__(self):
        return f"{self.base_user.user.get_full_name()}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('MAINTENANCE_DUE', 'Maintenance Due'),
        ('APPOINTMENT_REMINDER', 'Appointment Reminder'),
        ('STATUS_UPDATE', 'Status Update'),
        ('REVIEW_REQUEST', 'Review Request'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} for {self.user}"

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    PAYMENT_METHODS = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]

    appointment = models.OneToOneField('Appointment', on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for {self.appointment} - {self.status}"

class Schedule(models.Model):
    facility = models.OneToOneField('Facility', on_delete=models.CASCADE, related_name='schedule')
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open_weekends = models.BooleanField(default=False)
    max_daily_appointments = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Schedule for {self.facility}"

class Vehicle(models.Model):
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    vin = models.CharField(max_length=17, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year + 1)
        ]
    )
    color = models.CharField(max_length=30)
    license_plate = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.license_plate})"

class Facility(models.Model):
    FACILITY_TYPES = [
        ('OFFICE', 'Office'),
        ('TUNING', 'Tuning Facility'),
        ('MAINTENANCE', 'Maintenance Shop'),
        ('ALIGNMENT', 'Alignment Facility'),
        ('DIAGNOSTIC', 'Diagnostic Facility'),
        ('TIRE', 'Tire Shop'),
        ('PAINT', 'Paint Shop'),
        ('CARWASH', 'Car Wash'),
    ]

    name = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPES)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    repair_shop = models.ForeignKey('RepairShop', on_delete=models.CASCADE, related_name='facilities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Facilities"

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"

class RepairShop(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    tax_id = models.CharField(max_length=50)
    owner = models.ForeignKey(BaseUser, on_delete=models.PROTECT, 
                            limit_choices_to={'user_type': 'OWNER'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and RepairShop.objects.exists():
            # If you try to create a new instance and one already exists
            raise ValidationError('Only one repair shop instance can exist.')
        return super(RepairShop, self).save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """
        Get the single repair shop instance or create it if it doesn't exist.
        """
        instance = cls.objects.first()
        if instance is None:
            raise ValidationError('No repair shop instance exists. Please create one through the admin interface.')
        return instance

    def delete(self, *args, **kwargs):
        if self.pk == RepairShop.objects.first().pk:
            raise ValidationError('Cannot delete the only repair shop instance.')
        return super(RepairShop, self).delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Repair Shop'
        verbose_name_plural = 'Repair Shop'  # Singular since there should be only one

    def __str__(self):
        return self.name

class Analytics(models.Model):
    repair_shop = models.OneToOneField(RepairShop, on_delete=models.CASCADE, related_name='analytics')
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_appointments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Analytics"

    def __str__(self):
        return f"Analytics for {self.repair_shop}"

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='service_types')
    maintenance_interval_months = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} at {self.facility.name}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='appointments')
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='appointments')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']

    def __str__(self):
        return f"{self.service_type} for {self.vehicle} on {self.scheduled_date}"

class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.appointment}"

class EventLog(models.Model):
    EVENT_TYPES = [
        ('APPOINTMENT_CREATED', 'Appointment Created'),
        ('APPOINTMENT_UPDATED', 'Appointment Updated'),
        ('APPOINTMENT_COMPLETED', 'Appointment Completed'),
        ('REVIEW_SUBMITTED', 'Review Submitted'),
        ('MAINTENANCE_DUE', 'Maintenance Due'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='events')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='events', null=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='events', null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.customer} - {self.created_at.date()}"

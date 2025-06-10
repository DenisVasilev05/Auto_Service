from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import uuid
from datetime import datetime, timedelta, date

class BaseModel(models.Model):
    """Abstract base model with UUID primary key"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class BaseUser(BaseModel):
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

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_user_type_display()}"

class Employee(BaseModel):
    base_user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                 limit_choices_to={'base_user__user_type': 'SUPERVISOR'})
    facility = models.ForeignKey('Facility', on_delete=models.SET_NULL, null=True)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    specializations = models.ManyToManyField('ServiceType', blank=True, related_name='specialists')
    working_hours = models.ForeignKey('Schedule', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.base_user.user.get_full_name()} - {self.base_user.get_user_type_display()}"

    @property
    def average_rating(self):
        return self.assigned_appointments.filter(
            review__isnull=False
        ).aggregate(avg_rating=models.Avg('review__rating'))['avg_rating'] or 0

    @property
    def completion_rate(self):
        total = self.assigned_appointments.count()
        if total == 0:
            return 0
        completed = self.assigned_appointments.filter(status='COMPLETED').count()
        return (completed / total) * 100

class Customer(BaseModel):
    base_user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[('EMAIL', 'Email'), ('PHONE', 'Phone')],
        default='EMAIL'
    )

    def __str__(self):
        return f"{self.base_user.user.get_full_name()}"

class Notification(BaseModel):
    NOTIFICATION_TYPES = [
        ('MAINTENANCE_DUE', 'Maintenance Due'),
        ('APPOINTMENT_REMINDER', 'Appointment Reminder'),
        ('STATUS_UPDATE', 'Status Update'),
        ('REVIEW_REQUEST', 'Review Request'),
        ('ASSIGNMENT', 'Service Assignment'),
        ('SCHEDULE_CHANGE', 'Schedule Change'),
    ]

    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_appointment = models.ForeignKey('Appointment', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} for {self.user}"

class Payment(BaseModel):
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
    payment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for {self.appointment} - {self.status}"

class Schedule(BaseModel):
    facility = models.OneToOneField('Facility', on_delete=models.CASCADE, related_name='schedule')
    opening_time = models.TimeField(default='09:00')
    closing_time = models.TimeField(default='17:00')
    is_open_weekends = models.BooleanField(default=False)
    max_daily_appointments = models.PositiveIntegerField(default=10)
    
    def clean(self):
        if self.opening_time and self.closing_time and self.opening_time >= self.closing_time:
            raise ValidationError({
                'closing_time': 'Closing time must be later than opening time.'
            })

    def save(self, *args, **kwargs):
        # Validate working hours
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Schedule for {self.facility}"

class Vehicle(BaseModel):
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
    next_maintenance_date = models.DateField(null=True, blank=True)
    mileage = models.PositiveIntegerField(default=0)
    last_service_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.license_plate})"

class Facility(BaseModel):
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
    capacity = models.PositiveIntegerField(default=1)
    equipment = models.ManyToManyField('Equipment', blank=True)

    def save(self, *args, **kwargs):
        if not self.repair_shop_id:
            self.repair_shop = RepairShop.get_instance()
        super(Facility, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Facilities"

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"

class Equipment(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    purchase_date = models.DateField()
    last_maintenance = models.DateField()
    next_maintenance = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('OPERATIONAL', 'Operational'),
            ('MAINTENANCE', 'Under Maintenance'),
            ('REPAIR', 'Needs Repair'),
            ('RETIRED', 'Retired'),
        ],
        default='OPERATIONAL'
    )

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

def get_default_founded_date():
    return date(2010, 1, 1)

class RepairShop(BaseModel):
    """Model representing the auto repair shop business - implemented as a singleton"""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, default="+43 1 234 5678")
    email = models.EmailField()
    website = models.URLField(blank=True)
    description = models.TextField(default="Your trusted auto service partner.")
    business_hours = models.JSONField(default=dict)
    tax_id = models.CharField(max_length=50)
    registration_number = models.CharField(max_length=50, default="FN123456a")
    founded_date = models.DateField(default=get_default_founded_date)
    logo = models.ImageField(upload_to='shop_logos/', null=True, blank=True)
    owner = models.ForeignKey('BaseUser', on_delete=models.PROTECT, limit_choices_to={'user_type': 'OWNER'})

    def save(self, *args, **kwargs):
        """Ensure only one instance of RepairShop exists"""
        if not self.pk and RepairShop.objects.exists():
            raise ValidationError('Only one repair shop instance can exist.')
        return super(RepairShop, self).save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Get the single repair shop instance or raise an error if it doesn't exist"""
        instance = cls.objects.first()
        if instance is None:
            raise ValidationError('No repair shop instance exists. Create one through the admin interface.')
        return instance

    def delete(self, *args, **kwargs):
        """Prevent deletion of the only repair shop instance"""
        if self.pk == RepairShop.objects.first().pk:
            raise ValidationError('Cannot delete the only repair shop instance.')
        return super(RepairShop, self).delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Repair Shop'
        verbose_name_plural = 'Repair Shop'  # Singular since there should be only one

    def __str__(self):
        return self.name

class Analytics(BaseModel):
    repair_shop = models.OneToOneField(RepairShop, on_delete=models.CASCADE, related_name='analytics')
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_appointments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    customer_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_customers = models.PositiveIntegerField(default=0)
    total_vehicles = models.PositiveIntegerField(default=0)
    facility_utilization = models.JSONField(default=dict)  # Store per-facility stats
    technician_performance = models.JSONField(default=dict)  # Store per-technician stats
    revenue_by_service = models.JSONField(default=dict)  # Store per-service revenue
    peak_hours = models.JSONField(default=dict)  # Store busy hours data
    customer_demographics = models.JSONField(default=dict)  # Store customer statistics
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.repair_shop_id:
            self.repair_shop = RepairShop.get_instance()
        super(Analytics, self).save(*args, **kwargs)

    def update_statistics(self):
        """Update all analytics fields based on current data"""
        from django.db.models import Avg, Count
        from django.utils import timezone

        # Update basic counts
        self.total_customers = Customer.objects.count()
        self.total_vehicles = Vehicle.objects.count()

        # Calculate customer satisfaction
        reviews = Review.objects.all()
        self.customer_satisfaction = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        # Calculate facility utilization
        facilities = Facility.objects.all()
        self.facility_utilization = {
            str(facility.id): {
                'name': facility.name,
                'total_appointments': facility.service_types.filter(
                    appointments__scheduled_date__gte=timezone.now() - timezone.timedelta(days=30)
                ).count(),
                'utilization_rate': facility.service_types.filter(
                    appointments__status='COMPLETED'
                ).count() / facility.capacity if facility.capacity > 0 else 0
            }
            for facility in facilities
        }

        # Calculate technician performance
        technicians = Employee.objects.filter(base_user__user_type='TECHNICIAN')
        self.technician_performance = {
            str(tech.id): {
                'name': tech.base_user.user.get_full_name(),
                'completed_appointments': tech.assigned_appointments.filter(status='COMPLETED').count(),
                'average_rating': tech.average_rating,
                'completion_rate': tech.completion_rate
            }
            for tech in technicians
        }

        # Calculate revenue by service
        services = ServiceType.objects.all()
        self.revenue_by_service = {
            str(service.id): {
                'name': service.name,
                'total_revenue': sum(
                    appointment.final_cost or 0
                    for appointment in service.appointments.filter(status='COMPLETED')
                )
            }
            for service in services
        }

        self.save()

    class Meta:
        verbose_name_plural = "Analytics"

    def __str__(self):
        return f"Analytics for {self.repair_shop}"

@receiver(post_save, sender=RepairShop)
def create_repair_shop_analytics(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create Analytics instance when RepairShop is created
    """
    if created:
        Analytics.objects.create(repair_shop=instance)

class ServiceType(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='service_types')
    maintenance_interval_months = models.PositiveIntegerField(null=True, blank=True)
    required_certifications = models.ManyToManyField('Certification', blank=True)
    required_equipment = models.ManyToManyField('Equipment', blank=True)

    def __str__(self):
        return f"{self.name} at {self.facility.name}"

class Certification(BaseModel):
    name = models.CharField(max_length=100)
    issuing_authority = models.CharField(max_length=100)
    description = models.TextField()
    validity_years = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Appointment(BaseModel):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='appointments')
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='appointments')
    assigned_technician = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                          related_name='assigned_appointments',
                                          limit_choices_to={'base_user__user_type': 'TECHNICIAN'})
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']

    def __str__(self):
        return f"{self.service_type} for {self.vehicle} on {self.scheduled_date}"

    @property
    def is_on_time(self):
        if not self.actual_end_time or not self.scheduled_time:
            return None
        scheduled_datetime = timezone.make_aware(
            datetime.combine(self.scheduled_date, self.scheduled_time)
        )
        return self.actual_end_time <= scheduled_datetime + timedelta(minutes=self.service_type.duration_minutes)

class Review(BaseModel):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    technician_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    technician_comment = models.TextField(blank=True)

    def __str__(self):
        return f"Review for {self.appointment}"

class Message(BaseModel):
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    sender = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='received_messages',
                                limit_choices_to={'user_type': 'SECRETARY'})
    subject = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    is_read = models.BooleanField(default=False)
    reply = models.TextField(blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}: {self.subject}"

class EventLog(BaseModel):
    EVENT_TYPES = [
        ('APPOINTMENT_SCHEDULED', 'Appointment Scheduled'),
        ('APPOINTMENT_CANCELLED', 'Appointment Cancelled'),
        ('APPOINTMENT_COMPLETED', 'Appointment Completed'),
        ('FACILITY_CLOSED', 'Facility Closed'),
        ('FACILITY_REOPENED', 'Facility Reopened'),
        ('VEHICLE_REGISTERED', 'Vehicle Registered'),
        ('USER_REGISTERED', 'User Registered'),
        ('REVIEW_SUBMITTED', 'Review Submitted'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField()
    user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, related_name='events')
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, related_name='events')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, related_name='events')
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.created_at}"

# Extend Facility model with closure information
class FacilityClosure(BaseModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='closures')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    is_emergency = models.BooleanField(default=False)
    announced_by = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True,
                                   limit_choices_to={'user_type': 'MANAGER'})

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': 'End date must be later than start date.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.facility.name} closure from {self.start_date} to {self.end_date}"

# Extend Employee model with availability tracking
class TechnicianAvailability(BaseModel):
    technician = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='availability_records',
                                 limit_choices_to={'base_user__user_type': 'TECHNICIAN'})
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name_plural = 'Technician Availabilities'

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'End time must be later than start time.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.technician} - {self.date} ({self.start_time}-{self.end_time})"

@receiver(post_save, sender=Facility)
def create_facility_schedule(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create Schedule instance when Facility is created
    """
    if created:
        Schedule.objects.create(facility=instance)
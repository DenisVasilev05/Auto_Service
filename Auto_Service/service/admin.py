from django.contrib import admin
from .models import (
    BaseUser, Employee, Customer, Vehicle, 
    Facility, ServiceType, Appointment, Review,
    Payment, Schedule, RepairShop, Analytics,
    Notification, EventLog
)

class BaseModelAdmin(admin.ModelAdmin):
    """Base admin class for models with UUID primary keys"""
    def get_queryset(self, request):
        # Ensure proper UUID handling in querysets
        return super().get_queryset(request).order_by('-created_at')

@admin.register(BaseUser)
class BaseUserAdmin(BaseModelAdmin):
    list_display = ('user', 'user_type', 'phone_number', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    date_hierarchy = 'created_at'

@admin.register(Employee)
class EmployeeAdmin(BaseModelAdmin):
    list_display = ('base_user', 'supervisor', 'facility', 'hire_date')
    list_filter = ('facility', 'hire_date')
    search_fields = ('base_user__user__username', 'base_user__phone_number')

@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    list_display = ('base_user', 'preferred_contact_method')
    list_filter = ('preferred_contact_method',)
    search_fields = ('base_user__user__username', 'base_user__phone_number')

@admin.register(Vehicle)
class VehicleAdmin(BaseModelAdmin):
    list_display = ('owner', 'make', 'model', 'year', 'license_plate')
    list_filter = ('make', 'year')
    search_fields = ('vin', 'license_plate', 'owner__base_user__user__username')

@admin.register(Facility)
class FacilityAdmin(BaseModelAdmin):
    list_display = ('name', 'facility_type', 'is_active')
    list_filter = ('facility_type', 'is_active')
    search_fields = ('name', 'description')

@admin.register(ServiceType)
class ServiceTypeAdmin(BaseModelAdmin):
    list_display = ('name', 'facility', 'duration_minutes', 'price')
    list_filter = ('facility', 'duration_minutes')
    search_fields = ('name', 'description')

@admin.register(Appointment)
class AppointmentAdmin(BaseModelAdmin):
    list_display = ('customer', 'vehicle', 'service_type', 'scheduled_date', 'status')
    list_filter = ('status', 'scheduled_date', 'service_type')
    search_fields = ('customer__base_user__user__username', 'vehicle__license_plate')
    date_hierarchy = 'scheduled_date'

@admin.register(Review)
class ReviewAdmin(BaseModelAdmin):
    list_display = ('appointment', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment', 'appointment__customer__base_user__user__username')

@admin.register(Payment)
class PaymentAdmin(BaseModelAdmin):
    list_display = ('appointment', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('transaction_id', 'appointment__customer__base_user__user__username')

@admin.register(Schedule)
class ScheduleAdmin(BaseModelAdmin):
    list_display = ('facility', 'opening_time', 'closing_time', 'is_open_weekends', 'max_daily_appointments')
    list_filter = ('is_open_weekends',)
    search_fields = ('facility__name',)

@admin.register(RepairShop)
class RepairShopAdmin(BaseModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'owner')
    search_fields = ('name', 'phone_number', 'email')

    # Add only if the shop does not exist
    def has_add_permission(self, request):
        return not RepairShop.objects.exists()

    # Delete only if the shop already exists
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Analytics)
class AnalyticsAdmin(BaseModelAdmin):
    list_display = ('repair_shop', 'total_revenue', 'total_appointments', 'average_rating', 'last_updated')
    readonly_fields = ('repair_shop', 'last_updated')

@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__user__username')

@admin.register(EventLog)
class EventLogAdmin(BaseModelAdmin):
    list_display = ('event_type', 'customer', 'vehicle', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('description', 'customer__base_user__user__username')
    date_hierarchy = 'created_at'

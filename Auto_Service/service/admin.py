from django.contrib import admin
from .models import (
    BaseUser, Employee, Customer, Vehicle, 
    Facility, ServiceType, Appointment, Review,
    Schedule, RepairShop, Analytics, Notification,
    EventLog, Message, FacilityClosure, TechnicianAvailability
)

class BaseModelAdmin(admin.ModelAdmin):
    """Base admin class for models with UUID primary keys"""
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

    def get_queryset(self, request):
        # Ensure proper UUID handling in querysets
        return super().get_queryset(request).order_by('-created_at')

@admin.register(BaseUser)
class BaseUserAdmin(BaseModelAdmin):
    list_display = ('user', 'user_type', 'phone_number')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    raw_id_fields = ('user',)

@admin.register(Employee)
class EmployeeAdmin(BaseModelAdmin):
    list_display = ('get_full_name', 'get_user_type', 'facility', 'supervisor', 'is_active')
    list_filter = ('is_active', 'facility', 'base_user__user_type')
    search_fields = ('base_user__user__username', 'base_user__user__email')
    raw_id_fields = ('base_user', 'supervisor', 'facility')
    filter_horizontal = ('specializations',)

    def get_full_name(self, obj):
        return obj.base_user.user.get_full_name()
    get_full_name.short_description = 'Name'

    def get_user_type(self, obj):
        return obj.base_user.get_user_type_display()
    get_user_type.short_description = 'Role'

@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    list_display = ('get_full_name', 'get_email', 'preferred_contact_method')
    list_filter = ('preferred_contact_method', 'created_at')
    search_fields = ('base_user__user__username', 'base_user__user__email')
    raw_id_fields = ('base_user',)

    def get_full_name(self, obj):
        return obj.base_user.user.get_full_name()
    get_full_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.base_user.user.email
    get_email.short_description = 'Email'

@admin.register(Vehicle)
class VehicleAdmin(BaseModelAdmin):
    list_display = ('vin', 'make', 'model', 'year', 'registration_date', 'owner', 'license_plate')
    list_filter = ('make', 'year', 'registration_date')
    search_fields = ('vin', 'license_plate', 'owner__base_user__user__username')
    raw_id_fields = ('owner',)

@admin.register(Facility)
class FacilityAdmin(BaseModelAdmin):
    list_display = ('name', 'facility_type', 'is_active', 'capacity')
    list_filter = ('facility_type', 'is_active')
    search_fields = ('name', 'description')
    filter_horizontal = ('equipment',)

@admin.register(ServiceType)
class ServiceTypeAdmin(BaseModelAdmin):
    list_display = ('name', 'facility', 'duration_minutes', 'price')
    list_filter = ('facility', 'duration_minutes')
    search_fields = ('name', 'description')
    raw_id_fields = ('facility',)
    filter_horizontal = ('required_certifications', 'required_equipment')

@admin.register(Appointment)
class AppointmentAdmin(BaseModelAdmin):
    list_display = ('customer', 'vehicle', 'service_type', 'scheduled_date', 'status')
    list_filter = ('status', 'scheduled_date')
    search_fields = ('customer__base_user__user__username', 'vehicle__vin')
    raw_id_fields = ('customer', 'vehicle', 'service_type', 'assigned_technician')
    readonly_fields = ('created_at', 'updated_at', 'is_on_time')

@admin.register(Review)
class ReviewAdmin(BaseModelAdmin):
    list_display = ('appointment', 'rating', 'technician_rating')
    list_filter = ('rating', 'technician_rating')
    search_fields = ('appointment__customer__base_user__user__username', 'comment')
    raw_id_fields = ('appointment',)

@admin.register(Schedule)
class ScheduleAdmin(BaseModelAdmin):
    list_display = ('facility', 'opening_time', 'closing_time', 'is_open_weekends')
    list_filter = ('is_open_weekends',)
    raw_id_fields = ('facility',)

@admin.register(RepairShop)
class RepairShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'website')
    search_fields = ('name', 'phone', 'email', 'address')
    list_filter = ('founded_date',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'logo')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email', 'website')
        }),
        ('Business Details', {
            'fields': ('business_hours', 'tax_id', 'registration_number', 'founded_date')
        })
    )

    def has_add_permission(self, request):
        """Only allow adding if no RepairShop exists"""
        return not RepairShop.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Never allow deletion through admin"""
        return False

@admin.register(Analytics)
class AnalyticsAdmin(BaseModelAdmin):
    list_display = ('repair_shop', 'total_revenue', 'total_appointments', 'average_rating', 'last_updated')
    readonly_fields = ('created_at', 'updated_at', 'last_updated')
    actions = ['update_statistics']

    def update_statistics(self, request, queryset):
        for analytics in queryset:
            analytics.update_statistics()
        self.message_user(request, "Statistics updated successfully.")
    update_statistics.short_description = "Update statistics for selected analytics"

@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__user__username', 'title', 'message')
    raw_id_fields = ('user', 'related_appointment')

@admin.register(EventLog)
class EventLogAdmin(BaseModelAdmin):
    list_display = ('event_type', 'user', 'facility', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('description', 'user__user__username')
    raw_id_fields = ('user', 'facility', 'appointment')

@admin.register(Message)
class MessageAdmin(BaseModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'priority', 'is_read', 'created_at')
    list_filter = ('priority', 'is_read')
    search_fields = ('sender__user__username', 'recipient__user__username', 'subject', 'content')
    raw_id_fields = ('sender', 'recipient')
    readonly_fields = ('created_at', 'updated_at', 'replied_at')

@admin.register(FacilityClosure)
class FacilityClosureAdmin(BaseModelAdmin):
    list_display = ('facility', 'start_date', 'end_date', 'is_emergency', 'announced_by')
    list_filter = ('is_emergency', 'start_date', 'end_date')
    search_fields = ('facility__name', 'reason')
    raw_id_fields = ('facility', 'announced_by')

@admin.register(TechnicianAvailability)
class TechnicianAvailabilityAdmin(BaseModelAdmin):
    list_display = ('technician', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date')
    search_fields = ('technician__base_user__user__username', 'reason')
    raw_id_fields = ('technician',)

from django.urls import path
from . import views

app_name = 'service'

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing_page'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    
    # Facilities
    path('facilities/', views.facility_list, name='facility_list'),
    path('facilities/<uuid:facility_id>/', views.facility_detail, name='facility_detail'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/notifications/', views.notifications, name='notifications'),
    path('dashboard/appointments/', views.appointments, name='appointments'),
    path('dashboard/messages/', views.messages_view, name='messages'),
    
    # Vehicle Management
    path('vehicles/register/', views.vehicle_register, name='vehicle_register'),
    path('vehicles/<uuid:vehicle_id>/', views.vehicle_detail, name='vehicle_detail'),
    
    # Appointments
    path('appointments/create/', views.create_appointment, name='create_appointment'),
    path('appointments/<uuid:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<uuid:appointment_id>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    
    # Reviews
    path('reviews/create/<uuid:appointment_id>/', views.review_create, name='review_create'),
    
    # Admin/Manager specific
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/facilities/manage/', views.admin_facilities, name='admin_facilities'),
    
    # API endpoints for AJAX requests
    path('api/facility-schedule/<uuid:facility_id>/', views.api_facility_schedule, name='api_facility_schedule'),
    path('api/technician-schedule/<uuid:technician_id>/', views.api_technician_schedule, name='api_technician_schedule'),
    path('api/mark-notification-read/<uuid:notification_id>/', views.api_mark_notification_read, name='api_mark_notification_read'),
] 
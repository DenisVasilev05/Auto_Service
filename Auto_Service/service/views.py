from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (
    Facility, ServiceType, Employee, Customer, Appointment, Vehicle,
    Review, BaseUser, TechnicianAvailability, RepairShop, Notification
)
from .forms import UserRegistrationForm, LoginForm, AppointmentForm, VehicleForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.db import models

def get_base_context(request):
    """Get base context data for all views"""
    context = {}
    try:
        context['repair_shop'] = RepairShop.objects.first()
    except RepairShop.DoesNotExist:
        context['repair_shop'] = None
        
    if request.user.is_authenticated:
        context['unread_notifications_count'] = request.user.baseuser.notifications.filter(is_read=False).count()
    return context

def landing_page(request):
    """
    View for the landing page of the auto service application.
    Displays featured services, facilities, and reviews.
    """
    facilities = Facility.objects.filter(is_active=True)[:3]  # Get first 3 active facilities
    featured_services = ServiceType.objects.all()[:6]  # Get first 6 services
    featured_reviews = Review.objects.select_related(
        'appointment__customer__base_user__user',
        'appointment__service_type'
    ).filter(
        rating__gte=4  # Only show reviews with 4 or 5 stars
    ).order_by('-created_at')[:3]  # Get latest 3 high-rated reviews
    
    try:
        repair_shop = RepairShop.objects.first()
    except RepairShop.DoesNotExist:
        repair_shop = None
    
    context = {
        'facilities': facilities,
        'featured_services': featured_services,
        'featured_reviews': featured_reviews,
        'repair_shop': repair_shop,
    }
    context.update(get_base_context(request))
    return render(request, 'service/landing_page.html', context)

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('service:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    context = {'form': form}
    context.update(get_base_context(request))
    return render(request, 'service/login.html', context)

def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('service:landing_page')

def signup_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            base_user = BaseUser.objects.create(
                user=user,
                user_type='CUSTOMER',
                phone_number=form.cleaned_data['phone'],
                address=form.cleaned_data.get('address', '')
            )
            Customer.objects.create(base_user=base_user)
            login(request, user)
            return redirect('service:dashboard')
    else:
        form = UserRegistrationForm()
    
    context = {'form': form}
    context.update(get_base_context(request))
    return render(request, 'service/signup.html', context)

@login_required
def dashboard(request):
    """User dashboard view"""
    base_user = request.user.baseuser
    today = timezone.now().date()

    context = {}

    if base_user.user_type == 'CUSTOMER':
        customer = get_object_or_404(Customer, base_user=base_user)
        vehicles = customer.vehicles.all()
        # Back-fill last_service_date for any vehicle that still has null (legacy data)
        for v in vehicles:
            if v.last_service_date is None:
                last_completed = v.appointments.filter(status='COMPLETED').aggregate(
                    last_date=models.Max('scheduled_date')
                )['last_date']
                if last_completed:
                    v.last_service_date = last_completed
                    v.save(update_fields=['last_service_date'])
        appointments = Appointment.objects.filter(vehicle__owner=customer)
        # Include both scheduled appointments in the future as well as services that have already started but
        # are not yet completed so the customer always sees every upcoming service slot.
        active_appointments_count = appointments.filter(
            status__in=['SCHEDULED', 'IN_PROGRESS'],
            scheduled_date__gte=today
        ).distinct().count()
        vehicles_count = vehicles.count()
        total_services_count = appointments.count()
        # Fetch **all** upcoming appointments (future scheduled + currently in-progress) across every vehicle
        # owned by the customer.
        upcoming_appointments = appointments.filter(
            status__in=['SCHEDULED', 'IN_PROGRESS'],
            scheduled_date__gte=today
        ).order_by('scheduled_date', 'scheduled_time').distinct()
        recent_reviews = Review.objects.filter(appointment__customer=customer).order_by('-created_at')[:5]

        context.update({
            'vehicles': vehicles,
            'appointments': appointments,
            'active_appointments_count': active_appointments_count,
            'vehicles_count': vehicles_count,
            'total_services_count': total_services_count,
            'upcoming_appointments': upcoming_appointments,
            'recent_reviews': recent_reviews,
        })

    elif base_user.user_type == 'TECHNICIAN':
        employee = get_object_or_404(Employee, base_user=base_user)
        appointments = Appointment.objects.filter(assigned_technician=employee)
        today_appointments = appointments.filter(scheduled_date=today).exclude(status='CANCELLED')
        upcoming_appointments = appointments.filter(status='SCHEDULED', scheduled_date__gt=today)
        context.update({
            'appointments': appointments,
            'today_appointments': today_appointments,
            'today_appointments_count': today_appointments.count(),
            'upcoming_appointments': upcoming_appointments,
        })

    elif base_user.user_type == 'SECRETARY':
        context['messages'] = request.user.baseuser.received_messages.all()

    elif base_user.user_type in ['MANAGER', 'SUPERVISOR', 'STAFF', 'ADMIN', 'OWNER']:
        context['appointments_count'] = Appointment.objects.count()
        context['technicians_count'] = Employee.objects.filter(base_user__user_type='TECHNICIAN').count()

    # Always include notifications list for the logged-in user
    context['notifications'] = request.user.baseuser.notifications.all().order_by('-created_at')[:10]

    context.update(get_base_context(request))

    return render(request, 'service/dashboard.html', context)

def facility_list(request):
    """Display list of all facilities"""
    facilities = Facility.objects.filter(is_active=True)
    context = {
        'facilities': facilities,
    }
    context.update(get_base_context(request))
    return render(request, 'service/facility_list.html', context)

def facility_detail(request, facility_id):
    """Display detailed information about a specific facility"""
    facility = get_object_or_404(Facility, id=facility_id)
    services = ServiceType.objects.filter(facility=facility)
    technicians = Employee.objects.filter(
        facility=facility,
        base_user__user_type='TECHNICIAN',
        is_active=True
    )
    
    context = {
        'facility': facility,
        'services': services,
        'technicians': technicians,
    }
    context.update(get_base_context(request))
    return render(request, 'service/facility_detail.html', context)

@login_required
def create_appointment(request):
    """Create a new appointment"""
    # Restrict to customers only
    if request.user.baseuser.user_type != 'CUSTOMER':
        messages.error(request, 'Only customers can book appointments.')
        return redirect('service:dashboard')

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            customer = get_object_or_404(Customer, base_user=request.user.baseuser)
            appointment.customer = customer
            appointment.save()
            messages.success(request, 'Appointment scheduled successfully!')
            return redirect('service:dashboard')
    else:
        form = AppointmentForm()

        # Pre-filter / pre-select service & facility if provided via query string
        service_id  = request.GET.get('service_id') or request.GET.get('service')
        facility_id = request.GET.get('facility_id') or request.GET.get('facility')

        if facility_id:
            # Limit the service dropdown to this facility's services only
            form.fields['service_type'].queryset = ServiceType.objects.filter(facility_id=facility_id)

        if service_id and ServiceType.objects.filter(id=service_id).exists():
            form.initial['service_type'] = service_id

        # Only show vehicles owned by the current customer
        form.fields['vehicle'].queryset = Vehicle.objects.filter(owner__base_user=request.user.baseuser)
    
    context = {'form': form}
    context.update(get_base_context(request))
    return render(request, 'service/create_appointment.html', context)

@login_required
def vehicle_register(request):
    """Register a new vehicle"""
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save(commit=False)
            customer = get_object_or_404(Customer, base_user=request.user.baseuser)
            vehicle.owner = customer
            vehicle.save()
            return redirect('service:dashboard')
    else:
        form = VehicleForm()
    context = {'form': form}
    context.update(get_base_context(request))
    return render(request, 'service/vehicle_register.html', context)

@login_required
def notifications(request):
    """Display user notifications"""
    user_notifications = request.user.baseuser.notifications.all()
    context = {
        'notifications': user_notifications,
    }
    context.update(get_base_context(request))
    return render(request, 'service/notifications.html', context)

@login_required
def appointments(request):
    """Display appointments list for the current user.
    For technicians: shows their non-cancelled appointments ordered by date.
    For customers: separates upcoming vs past services.
    """
    base_user = request.user.baseuser

    if base_user.user_type == 'TECHNICIAN':
        employee = get_object_or_404(Employee, base_user=base_user)
        today = timezone.localdate()
        upcoming = Appointment.objects.filter(
            assigned_technician=employee,
            status__in=['SCHEDULED', 'IN_PROGRESS'],
            scheduled_date__gte=today
        ).order_by('scheduled_date', 'scheduled_time')

        past = Appointment.objects.filter(
            assigned_technician=employee,
            status='COMPLETED'
        ).order_by('-scheduled_date', '-scheduled_time')

        context = {
            'upcoming_appointments': upcoming,
            'past_appointments': past,
            'is_technician': True,
        }

    else:
        customer = get_object_or_404(Customer, base_user=base_user)
        today = timezone.localdate()
        all_qs = Appointment.objects.filter(vehicle__owner=customer).select_related('service_type', 'vehicle')

        # Same logic as for the dashboard – show both scheduled and in-progress future services.
        upcoming = all_qs.filter(
            status__in=['SCHEDULED', 'IN_PROGRESS'],
            scheduled_date__gte=today
        ).order_by('scheduled_date', 'scheduled_time').distinct()
        # Any appointment that is not a future scheduled / in-progress service is considered past (completed, cancelled, or overdue).
        past = all_qs.exclude(
            status__in=['SCHEDULED', 'IN_PROGRESS'],
            scheduled_date__gte=today
        ).order_by('-scheduled_date', '-scheduled_time').distinct()

        context = {
            'upcoming_appointments': upcoming,
            'past_appointments': past,
            'is_technician': False,
        }

    context.update(get_base_context(request))
    return render(request, 'service/appointments.html', context)

@login_required
def messages_view(request):
    """Display user messages"""
    messages_qs = request.user.baseuser.received_messages.all()
    context = {
        'messages': messages_qs,
    }
    context.update(get_base_context(request))
    return render(request, 'service/messages.html', context)

@login_required
def vehicle_detail(request, vehicle_id):
    """Display detailed information about a vehicle"""
    customer = get_object_or_404(Customer, base_user=request.user.baseuser)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=customer)
    service_history = Appointment.objects.filter(vehicle=vehicle).order_by('-scheduled_date')
    context = {
        'vehicle': vehicle,
        'service_history': service_history,
    }
    context.update(get_base_context(request))
    return render(request, 'service/vehicle_detail.html', context)

@login_required
def appointment_detail(request, appointment_id):
    """Display appointment details"""
    customer = get_object_or_404(Customer, base_user=request.user.baseuser)
    appointment = get_object_or_404(Appointment, id=appointment_id, customer=customer)
    context = {'appointment': appointment}
    context.update(get_base_context(request))
    return render(request, 'service/appointment_detail.html', context)

@login_required
def appointment_cancel(request, appointment_id):
    """Cancel an appointment"""
    customer = get_object_or_404(Customer, base_user=request.user.baseuser)
    appointment = get_object_or_404(Appointment, id=appointment_id, customer=customer)
    
    if appointment.status != 'SCHEDULED':
        messages.error(request, 'Only scheduled appointments can be cancelled.')
    else:
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    
    return redirect('service:dashboard')

@login_required
def review_create(request, appointment_id):
    """Create a review for a completed appointment"""
    customer = get_object_or_404(Customer, base_user=request.user.baseuser)
    appointment = get_object_or_404(Appointment, id=appointment_id, customer=customer)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        technician_rating = request.POST.get('technician_rating')
        technician_comment = request.POST.get('technician_comment')
        
        if rating and comment:
            Review.objects.create(
                appointment=appointment,
                rating=rating,
                comment=comment,
                technician_rating=technician_rating,
                technician_comment=technician_comment
            )
            messages.success(request, 'Thank you for your review!')
            return redirect('service:appointment_detail', appointment_id=appointment_id)
        else:
            messages.error(request, 'Please provide both rating and comment.')
    
    context = {'appointment': appointment}
    context.update(get_base_context(request))
    return render(request, 'service/review_create.html', context)

@login_required
def admin_analytics(request):
    """Display analytics dashboard for administrators"""
    if request.user.baseuser.user_type not in ['ADMIN', 'OWNER', 'MANAGER']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('service:dashboard')
    
    analytics = Analytics.objects.first()
    context = {'analytics': analytics}
    context.update(get_base_context(request))
    return render(request, 'service/admin/analytics.html', context)

@login_required
def admin_users(request):
    """Manage users for administrators"""
    if request.user.baseuser.user_type not in ['ADMIN', 'OWNER', 'MANAGER']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('service:dashboard')
    
    users = BaseUser.objects.all().select_related('user')
    context = {'users': users}
    context.update(get_base_context(request))
    return render(request, 'service/admin/users.html', context)

@login_required
def admin_facilities(request):
    """Manage facilities for administrators"""
    if request.user.baseuser.user_type not in ['ADMIN', 'OWNER', 'MANAGER']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('service:dashboard')
    
    facilities = Facility.objects.all()
    context = {'facilities': facilities}
    context.update(get_base_context(request))
    return render(request, 'service/admin/facilities.html', context)

@login_required
def api_facility_schedule(request, facility_id):
    """API endpoint for facility schedule"""
    facility = get_object_or_404(Facility, id=facility_id)
    schedule = facility.schedule
    return JsonResponse({
        'opening_time': schedule.opening_time.strftime('%H:%M'),
        'closing_time': schedule.closing_time.strftime('%H:%M'),
        'is_open_weekends': schedule.is_open_weekends,
    })

@login_required
def api_technician_schedule(request, technician_id):
    """API endpoint for technician schedule"""
    technician = get_object_or_404(Employee, id=technician_id, base_user__user_type='TECHNICIAN')
    availability = TechnicianAvailability.objects.filter(
        technician=technician,
        date__gte=timezone.now().date()
    )
    data = [{
        'date': av.date.isoformat(),
        'start_time': av.start_time.strftime('%H:%M'),
        'end_time': av.end_time.strftime('%H:%M'),
        'is_available': av.is_available,
    } for av in availability]
    return JsonResponse({'availability': data})

@login_required
def api_mark_notification_read(request, notification_id):
    """API endpoint to mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user.baseuser)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def api_notification_dismiss(request, notification_id):
    """API endpoint to allow the logged-in user to permanently dismiss (delete) a notification."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user.baseuser)
    notification.delete()
    return JsonResponse({
        'success': True
    })

# ---------------------- Appointment state change APIs ----------------------

@login_required
@require_POST
def api_appointment_start(request, appointment_id):
    """Technician starts an appointment (moves to IN_PROGRESS)"""
    if request.user.baseuser.user_type != 'TECHNICIAN':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    appt = get_object_or_404(Appointment, id=appointment_id,
                             assigned_technician__base_user=request.user.baseuser)

    if appt.status != 'SCHEDULED':
        return JsonResponse({'error': 'Only scheduled appointments can be started.'}, status=400)

    appt.status = 'IN_PROGRESS'
    appt.actual_start_time = timezone.now()
    appt.save()
    return JsonResponse({'success': True})

@login_required
@require_POST
def api_appointment_complete(request, appointment_id):
    """Technician completes an appointment (moves to COMPLETED)"""
    if request.user.baseuser.user_type != 'TECHNICIAN':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    appt = get_object_or_404(Appointment, id=appointment_id,
                             assigned_technician__base_user=request.user.baseuser)

    if appt.status != 'IN_PROGRESS':
        return JsonResponse({'error': 'Only in-progress appointments can be completed.'}, status=400)

    appt.status = 'COMPLETED'
    appt.actual_end_time = timezone.now()

    # Parse optional comment from request body
    try:
        payload = json.loads(request.body.decode()) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    comment = payload.get('comment', '').strip()
    if comment:
        appt.notes = comment  # reuse notes field for technician comment
    appt.save()

    # Send notification to customer
    Notification.objects.create(
        user=appt.customer.base_user,
        type='STATUS_UPDATE',
        title='Service Completed',
        message=f'Your appointment "{appt.service_type.name}" has been completed. {"Technician note: " + comment if comment else ""}',
        related_appointment=appt
    )

    return JsonResponse({'success': True})

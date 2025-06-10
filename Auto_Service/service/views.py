from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (
    Facility, ServiceType, Employee, Customer, Appointment, Vehicle,
    Review, BaseUser, TechnicianAvailability, RepairShop
)
from .forms import UserRegistrationForm, LoginForm, AppointmentForm, VehicleForm
from django.http import JsonResponse

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
            # Create BaseUser and Customer records
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

    if base_user.user_type == 'TECHNICIAN':
        # Employee dashboard
        employee = get_object_or_404(Employee, base_user=base_user)
        appointments = Appointment.objects.filter(assigned_technician=employee)
        today_appointments_count = appointments.filter(scheduled_date=today).count()
        completed_today = appointments.filter(scheduled_date=today, status='COMPLETED').count()
        pending_count = appointments.filter(status='SCHEDULED').count()
        upcoming_count = appointments.filter(scheduled_date__gt=today).count()

        context = {
            'appointments': appointments,
            'today': today,
            'today_appointments_count': today_appointments_count,
            'completed_today': completed_today,
            'pending_count': pending_count,
            'upcoming_count': upcoming_count,
        }
        template = 'service/dashboard_employee.html'
    else:
        # Customer dashboard
        customer = get_object_or_404(Customer, base_user=base_user)
        appointments = Appointment.objects.filter(customer=customer)
        context = {
            'appointments': appointments,
        }
        template = 'service/dashboard_customer.html'
    
    return render(request, template, context)

def facility_list(request):
    """Display list of all facilities"""
    facilities = Facility.objects.filter(is_active=True)
    return render(request, 'service/facility_list.html', {'facilities': facilities})

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
    return render(request, 'service/facility_detail.html', context)

@login_required
def create_appointment(request):
    """Create a new appointment"""
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
        # Only show vehicles owned by the current customer
        form.fields['vehicle'].queryset = Vehicle.objects.filter(owner__base_user=request.user.baseuser)
    
    context = {'form': form}
    context.update(get_base_context(request))
    return render(request, 'service/create_appointment.html', context)

@login_required
def vehicle_register(request):
    """Register a new vehicle"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            customer = get_object_or_404(Customer, base_user=request.user.baseuser)
            vehicle.owner = customer
            vehicle.save()
            return redirect('service:dashboard')
    else:
        form = VehicleForm()
    return render(request, 'service/vehicle_register.html', {'form': form})

@login_required
def notifications(request):
    """Display user notifications"""
    notifications = request.user.baseuser.notifications.all()
    return render(request, 'service/notifications.html', {'notifications': notifications})

@login_required
def appointments(request):
    """Display user appointments"""
    base_user = request.user.baseuser
    if base_user.user_type == 'TECHNICIAN':
        employee = get_object_or_404(Employee, base_user=base_user)
        appointments = Appointment.objects.filter(assigned_technician=employee)
    else:
        customer = get_object_or_404(Customer, base_user=base_user)
        appointments = Appointment.objects.filter(customer=customer)
    return render(request, 'service/appointments.html', {'appointments': appointments})

@login_required
def messages_view(request):
    """Display user messages"""
    messages = request.user.baseuser.received_messages.all()
    return render(request, 'service/messages.html', {'messages': messages})

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
    
    return render(request, 'service/review_create.html', {'appointment': appointment})

@login_required
def admin_analytics(request):
    """Display analytics dashboard for administrators"""
    if request.user.baseuser.user_type not in ['ADMIN', 'OWNER', 'MANAGER']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('service:dashboard')
    
    analytics = Analytics.objects.first()
    return render(request, 'service/admin/analytics.html', {'analytics': analytics})

@login_required
def admin_users(request):
    """Manage users for administrators"""
    if request.user.baseuser.user_type not in ['ADMIN', 'OWNER', 'MANAGER']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('service:dashboard')
    
    users = BaseUser.objects.all().select_related('user')
    return render(request, 'service/admin/users.html', {'users': users})

@login_required
def admin_facilities(request):
    """Manage facilities for administrators"""
    if request.user.baseuser.user_type not in ['ADMIN', 'OWNER', 'MANAGER']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('service:dashboard')
    
    facilities = Facility.objects.all()
    return render(request, 'service/admin/facilities.html', {'facilities': facilities})

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

# Other views will be implemented here

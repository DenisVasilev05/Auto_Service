// Main JavaScript file for Auto Service Management System

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Handle notification marking as read
    document.querySelectorAll('.notification-item').forEach(function(notification) {
        notification.addEventListener('click', function() {
            const notificationId = this.dataset.notificationId;
            if (notificationId && !this.classList.contains('read')) {
                markNotificationAsRead(notificationId);
            }
        });
    });

    // Handle facility schedule loading
    const facilitySelect = document.getElementById('facility-select');
    if (facilitySelect) {
        facilitySelect.addEventListener('change', function() {
            loadFacilitySchedule(this.value);
        });
    }

    // Handle appointment scheduling
    const appointmentForm = document.getElementById('appointment-form');
    if (appointmentForm) {
        appointmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            validateAndSubmitAppointment(this);
        });
    }

    // Handle vehicle registration form
    const vehicleForm = document.getElementById('vehicle-form');
    if (vehicleForm) {
        vehicleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            validateAndSubmitVehicle(this);
        });
    }

    // Handle review submission
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            validateAndSubmitReview(this);
        });
    }

    // Handle message sending
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            validateAndSubmitMessage(this);
        });
    }

    // Handle notification dismissal buttons
    document.querySelectorAll('.dismiss-notification').forEach(function(btn){
        btn.addEventListener('click', function(e){
            e.stopPropagation(); // prevent parent click (mark read)
            const id = this.dataset.notificationId;
            if(id){
                dismissNotification(id);
            }
        });
    });
});

// Utility Functions

function markNotificationAsRead(notificationId) {
    fetch(`/service/api/mark-notification-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const notification = document.querySelector(`[data-notification-id="${notificationId}"]`);
            notification.classList.add('read');
            updateNotificationCount();
        }
    })
    .catch(error => console.error('Error:', error));
}

function loadFacilitySchedule(facilityId) {
    fetch(`/service/api/facility-schedule/${facilityId}/`)
    .then(response => response.json())
    .then(data => {
        updateCalendar(data.schedule);
        updateServiceList(data.services);
        updateTechnicianList(data.technicians);
    })
    .catch(error => console.error('Error:', error));
}

function validateAndSubmitAppointment(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Basic validation
    if (!data.facility_id || !data.service_type || !data.scheduled_date || !data.scheduled_time) {
        showAlert('Please fill in all required fields.', 'danger');
        return;
    }

    // Submit form
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Appointment scheduled successfully!', 'success');
            window.location.href = data.redirect_url;
        } else {
            showAlert(data.error || 'An error occurred.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while scheduling the appointment.', 'danger');
    });
}

function validateAndSubmitVehicle(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Basic validation
    if (!data.vin || !data.make || !data.model || !data.year || !data.license_plate) {
        showAlert('Please fill in all required fields.', 'danger');
        return;
    }

    // Submit form
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Vehicle registered successfully!', 'success');
            window.location.href = data.redirect_url;
        } else {
            showAlert(data.error || 'An error occurred.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while registering the vehicle.', 'danger');
    });
}

function validateAndSubmitReview(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Basic validation
    if (!data.rating || !data.comment) {
        showAlert('Please provide both a rating and a comment.', 'danger');
        return;
    }

    // Submit form
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Review submitted successfully!', 'success');
            window.location.href = data.redirect_url;
        } else {
            showAlert(data.error || 'An error occurred.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while submitting the review.', 'danger');
    });
}

function validateAndSubmitMessage(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Basic validation
    if (!data.subject || !data.content) {
        showAlert('Please provide both a subject and message content.', 'danger');
        return;
    }

    // Submit form
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Message sent successfully!', 'success');
            form.reset();
        } else {
            showAlert(data.error || 'An error occurred.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while sending the message.', 'danger');
    });
}

// Helper Functions

function updateCalendar(schedule) {
    const calendar = document.getElementById('appointment-calendar');
    if (!calendar) return;

    // Clear existing calendar
    calendar.innerHTML = '';

    // Create calendar grid
    schedule.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = `calendar-day ${day.available ? 'available' : 'unavailable'}`;
        dayElement.dataset.date = day.date;
        dayElement.innerHTML = `
            <div class="date">${day.dayOfMonth}</div>
            <div class="slots">${day.availableSlots} slots</div>
        `;
        if (day.available) {
            dayElement.addEventListener('click', () => selectDate(day.date));
        }
        calendar.appendChild(dayElement);
    });
}

function updateServiceList(services) {
    const serviceSelect = document.getElementById('service-select');
    if (!serviceSelect) return;

    // Clear existing options
    serviceSelect.innerHTML = '<option value="">Select a service...</option>';

    // Add new options
    services.forEach(service => {
        const option = document.createElement('option');
        option.value = service.id;
        option.textContent = `${service.name} - $${service.price} (${service.duration_minutes} mins)`;
        serviceSelect.appendChild(option);
    });
}

function updateTechnicianList(technicians) {
    const technicianList = document.getElementById('technician-list');
    if (!technicianList) return;

    // Clear existing list
    technicianList.innerHTML = '';

    // Add technicians
    technicians.forEach(tech => {
        const techElement = document.createElement('div');
        techElement.className = 'technician-card card mb-3';
        techElement.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${tech.name}</h5>
                <div class="star-rating">${'★'.repeat(tech.rating)}${'☆'.repeat(5-tech.rating)}</div>
                <p class="card-text">
                    <small class="text-muted">
                        ${tech.completed_services} services completed
                        <br>
                        ${tech.availability_status}
                    </small>
                </p>
            </div>
        `;
        technicianList.appendChild(techElement);
    });
}

function updateNotificationCount() {
    const badge = document.getElementById('notification-count');
    if (badge) {
        const count = document.querySelectorAll('.notification-item:not(.read)').length;
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline' : 'none';
    }
}

function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertsContainer.appendChild(alert);

    // Auto-dismiss after 5 seconds for non-danger alerts
    if (type !== 'danger') {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function dismissNotification(notificationId){
    fetch(`/service/api/notification/${notificationId}/dismiss/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if(data.success){
            const elem = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if(elem){
                elem.remove();
            }
            updateNotificationCount();
        }
    })
    .catch(error => console.error('Error:', error));
}

// Analytics Charts (if Chart.js is included)
function initializeAnalyticsCharts() {
    if (typeof Chart === 'undefined') return;

    // Revenue Chart
    const revenueCtx = document.getElementById('revenue-chart');
    if (revenueCtx) {
        new Chart(revenueCtx, {
            type: 'line',
            data: {
                labels: [], // Will be populated with dates
                datasets: [{
                    label: 'Revenue',
                    data: [], // Will be populated with revenue data
                    borderColor: '#0d6efd',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // Appointments Chart
    const appointmentsCtx = document.getElementById('appointments-chart');
    if (appointmentsCtx) {
        new Chart(appointmentsCtx, {
            type: 'bar',
            data: {
                labels: [], // Will be populated with dates
                datasets: [{
                    label: 'Appointments',
                    data: [], // Will be populated with appointment counts
                    backgroundColor: '#0d6efd'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
} 
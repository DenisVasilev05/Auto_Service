from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone
import random
import uuid
from faker import Faker
import os
from django.core.files.base import File
from django.conf import settings

from service.models import (
    BaseUser, Employee, Customer, Vehicle, Facility, ServiceType, Appointment, Review,
    Schedule, RepairShop, Notification, Message
)

fake = Faker()

# ------------------------------------------------------------------------------
# Car make/model pools (realistic combinations)
# ------------------------------------------------------------------------------
CAR_MAKE_MODELS = {
    'Audi': ['A3', 'A4', 'A6', 'Q5', 'Q7', 'A1', 'Q3'],
    'BMW': ['1 Series', '3 Series', '5 Series', 'X1', 'X3', 'X5'],
    'Mercedes': ['A-Class', 'C-Class', 'E-Class', 'GLC', 'GLE', 'CLA'],
    'Volkswagen': ['Golf', 'Passat', 'Tiguan', 'Polo', 'Arteon', 'T-Roc'],
    'Opel': ['Corsa', 'Astra', 'Insignia', 'Mokka', 'Grandland'],
    'Toyota': ['Yaris', 'Corolla', 'Camry', 'RAV4', 'Highlander'],
    'Ford': ['Fiesta', 'Focus', 'Mondeo', 'Kuga', 'Mustang'],
    'Skoda': ['Fabia', 'Octavia', 'Superb', 'Kamiq', 'Kodiaq'],
    'Hyundai': ['i20', 'i30', 'Elantra', 'Tucson', 'Santa Fe'],
    'Kia': ['Rio', 'Ceed', 'Picanto', 'Sportage', 'Sorento'],
}

def random_make_model():
    """Return a tuple (make, model) that are consistent with each other."""
    make = random.choice(list(CAR_MAKE_MODELS.keys()))
    model = random.choice(CAR_MAKE_MODELS[make])
    return make, model

# ------------------------------
# Predefined text pools
# ------------------------------

TECH_COMMENTS = [
    "Oil and filter change completed; no leaks detected.",
    "Brake pads replaced and rotors resurfaced.",
    "Performed diagnostic scan - cleared all fault codes.",
    "Replaced worn-out serpentine belt.",
    "Battery tested and replaced due to low voltage.",
    "Adjusted wheel alignment to factory specs.",
    "Recharged AC system and verified cooling performance.",
    "Replaced spark plugs and cleaned ignition coils.",
    "Tuned engine for optimal fuel efficiency.",
    "Transmission fluid flushed and replaced.",
    "Replaced faulty alternator and tested charging system.",
    "Fixed minor coolant leak at the radiator hose.",
    "Installed new air filter and cabin filter.",
    "Updated software on the vehicle's ECU.",
    "Power steering fluid topped up and leak inspected.",
    "Exhaust system checked; minor rust spots treated.",
    "Balanced all four wheels and rotated tires.",
    "Performed thorough safety inspection – all systems normal.",
    "Corrected tire pressure and replaced one valve stem.",
    "Resolved check engine light issue – sensor replaced.",
    "Lubricated suspension components and inspected bushings.",
    "Repaired damaged wiring in the fuse box.",
    "Cleared air intake blockage and cleaned throttle body.",
    "Repaired a small dent on the rear fender.",
    "Paint touch-up completed on affected panels.",
    "Interior detailing done post-service.",
    "Replaced leaking gasket on oil pan.",
    "Brake fluid flushed and replaced.",
    "Calibrated ADAS system after windshield replacement.",
    "Verified proper operation of all lights and signals."
]

REVIEW_COMMENTS = [
    "Excellent service - my car drives like new!",
    "Technicians were knowledgeable and friendly.",
    "Fast turnaround and transparent pricing.",
    "Appreciated the detailed explanation of the issue.",
    "Clean shop and professional staff.",
    "My car was ready ahead of schedule.",
    "Would definitely return for future maintenance.",
    "Great communication throughout the service.",
    "Issue was fixed on the first visit.",
    "Felt very confident in their recommendations.",
    "Fair pricing and no surprise charges.",
    "They even washed my car after the service!",
    "Very organized and efficient.",
    "Receptionist was helpful and courteous.",
    "They offered a courtesy shuttle which was convenient.",
    "Happy with the paint job - looks flawless.",
    "Tires were installed and balanced perfectly.",
    "Their diagnostic skills saved me time and money.",
    "It was easy to book an appointment online.",
    "Alignment is perfect - no more pulling.",
    "They found a hidden issue others missed.",
    "Smooth ride after the suspension fix.",
    "My AC is working like new again.",
    "No pressure upselling - very honest.",
    "I trust them completely with my car.",
    "Detailed invoice and explanation - very helpful.",
    "The staff really went the extra mile.",
    "I recommend this shop to everyone I know.",
    "The waiting area is comfortable and clean.",
    "They kept me informed every step of the way."
]

MESSAGE_SUBJECTS = [
    "Appointment Confirmation", "Schedule Change Request", "Customer Concern Follow-Up",
    "Parts Order Status", "Invoice Request", "Service Completion Notice",
    "Late Arrival Notification", "Car Drop-Off Update", "Courtesy Vehicle Request",
    "Diagnostic Results Inquiry", "Shift Change Notification", "Estimate Clarification",
    "Extra Service Request", "Missing Item Report", "Tool Request",
    "Vehicle Pickup Coordination", "Warranty Coverage Check", "Payment Confirmation",
    "Paint Service Addition", "Alignment Time Adjustment"
]

MESSAGE_CONTENTS = [
    "Can you confirm my appointment time for Friday?",
    "Please let the technician know I'll be late by 15 minutes.",
    "The customer wants to reschedule for next Tuesday.",
    "I need the part ordered for the Corolla ASAP.",
    "Let me know when the diagnostic results are ready.",
    "Customer called and mentioned a noise after pickup.",
    "Please send me the service invoice via email.",
    "Technician requested a callback regarding a missing tool.",
    "Is the courtesy car available tomorrow morning?",
    "I dropped the car off early - keys are in the drop box.",
    "Need to verify the cost for the brake job estimate.",
    "I'll be out sick today - please inform the team.",
    "Please notify the customer that their car is ready.",
    "Can we move the alignment booking to the afternoon?",
    "The client requested touch-up paint to be added to the service.",
    "Let me know when the lift bay is free.",
    "A package arrived for the technician - where should it go?",
    "Customer mentioned leaving their wallet in the vehicle.",
    "I need a printed receipt for my records.",
    "The technician said the issue is under warranty - please confirm."
]

FACILITY_DESCRIPTIONS = {
    "OFFICE": "The office serves as the central hub for customer service, scheduling, and administrative coordination.",
    "TUNING": "Our tuning facility is equipped with precision tools and software to optimize vehicle performance and engine responsiveness.",
    "MAINTENANCE": "The maintenance shop handles routine services such as oil changes, fluid replacements, and safety inspections.",
    "ALIGNMENT": "The alignment facility uses laser-guided equipment to ensure precise wheel alignment for improved handling and tire longevity.",
    "DIAGNOSTIC": "Our diagnostic facility features advanced scanning tools to quickly identify and troubleshoot engine and electrical issues.",
    "TIRE": "The tire shop stocks a wide selection of brands and performs tire fitting, balancing, and rotations.",
    "PAINT": "The paint shop includes a dust-free spray booth and color-matching technology for flawless refinishing work.",
    "CARWASH": "The car wash area offers a full exterior and interior detailing service to leave your vehicle spotless."
}

SERVICE_DESCRIPTIONS = {
    "OFFICE": [
        "Organizes service appointments and coordinates technician availability to ensure timely repairs.",
        "Handles customer questions regarding services, pricing, timelines, and policies.",
        "Processes payments and generates detailed service invoices for customer records."
    ],
    "TUNING": [
        "Adjusts engine control parameters for improved performance and fuel efficiency.",
        "Optimizes turbocharger performance to increase horsepower and responsiveness.",
        "Measures and verifies vehicle output on a dynamometer for performance tuning."
    ],
    "MAINTENANCE": [
        "Replaces engine oil and filter to maintain proper engine lubrication and performance.",
        "Checks and refills essential fluids such as brake, coolant, and power steering fluids.",
        "Comprehensive check of brakes, lights, belts, hoses, and more to ensure roadworthiness."
    ],
    "ALIGNMENT": [
        "Ensures all wheels are aligned according to factory specifications for even tire wear and handling.",
        "Custom adjustment of camber and caster angles for optimal performance or tire longevity.",
        "Checks suspension components for wear or damage that may affect alignment and ride comfort."
    ],
    "DIAGNOSTIC": [
        "Connects to onboard diagnostics to retrieve and interpret fault codes.",
        "Diagnoses issues in the battery, alternator, and wiring for reliable electrical performance.",
        "Monitors engine behavior to detect misfires, vacuum leaks, or timing issues."
    ],
    "TIRE": [
        "Fits new tires and ensures correct sizing, load rating, and speed rating.",
        "Evenly distributes tire weight to prevent vibration and extend tire life.",
        "Seals minor tire punctures from nails, screws, or sharp debris safely and efficiently."
    ],
    "PAINT": [
        "Buffs or repaints scratched surfaces to restore original appearance.",
        "Resprays a specific body panel using factory color match for consistency.",
        "Applies a fresh coat of paint to the entire vehicle, ideal for restoration or color change."
    ],
    "CARWASH": [
        "Removes dirt, grime, and road salt with pressure washing and hand drying.",
        "Cleans and sanitizes seats, carpets, and dashboard with specialized equipment.",
        "Applies protective wax and polish for enhanced shine and paint protection."
    ],
}

# Precise service names per facility type for more realistic demo data
SERVICE_NAMES = {
    "OFFICE": [
        "Appointment Scheduling",
        "Customer Support Handling",
        "Billing and Invoicing",
        "Service History Lookup",
        "Warranty Verification",
        "Work Order Processing",
    ],
    "TUNING": [
        "ECU Remapping",
        "Turbocharger Tuning",
        "Dyno Performance Testing",
        "Cold Air Intake Installation",
        "Throttle Response Tuning",
        "Fuel System Optimization",
    ],
    "MAINTENANCE": [
        "Oil and Filter Change",
        "Fluid Top-Up Service",
        "Multi-Point Vehicle Inspection",
        "Battery Replacement",
        "Belt and Hose Check",
        "Wiper Blade Replacement",
    ],
    "ALIGNMENT": [
        "Four-Wheel Alignment",
        "Camber and Caster Adjustment",
        "Suspension System Check",
        "Steering System Inspection",
        "Toe-In/Toe-Out Correction",
        "Tire Wear Pattern Analysis",
    ],
    "DIAGNOSTIC": [
        "OBD-II Fault Scan",
        "Electrical System Diagnosis",
        "Engine Performance Analysis",
        "Sensor Function Test",
        "Check Engine Light Inspection",
        "Cooling System Diagnosis",
    ],
    "TIRE": [
        "Tire Installation",
        "Wheel Balancing",
        "Tire Puncture Repair",
        "Seasonal Tire Changeover",
        "Tire Pressure Monitoring System (TPMS) Check",
        "Tire Rotation Service",
    ],
    "PAINT": [
        "Scratch and Chip Repair",
        "Panel Repainting",
        "Full Vehicle Repaint",
        "Clear Coat Restoration",
        "Bumper Respray",
        "Paintless Dent Removal",
    ],
    "CARWASH": [
        "Exterior Hand Wash",
        "Interior Detailing",
        "Wax and Polish Service",
        "Engine Bay Cleaning",
        "Undercarriage Wash",
        "Headlight Restoration",
    ],
}

SERVICE_DEFINITIONS = {
    "OFFICE": [
        {"name": "Appointment Scheduling", "description": "Organizes and manages service appointments based on technician availability and customer preferences."},
        {"name": "Customer Support Handling", "description": "Assists customers with inquiries about service options, shop policies, and repair status updates."},
        {"name": "Billing and Invoicing", "description": "Generates detailed invoices and processes payments for services rendered."},
        {"name": "Service History Lookup", "description": "Retrieves and reviews a customer's vehicle service history to inform future repairs or maintenance."},
        {"name": "Warranty Verification", "description": "Confirms manufacturer or shop warranty coverage for eligible parts and services."},
        {"name": "Work Order Processing", "description": "Creates and updates internal work orders to track technician tasks and service completion status."},
    ],
    "TUNING": [
        {"name": "ECU Remapping", "description": "Reprograms the engine control unit to enhance vehicle performance, fuel efficiency, and throttle response."},
        {"name": "Turbocharger Tuning", "description": "Fine-tunes turbo systems to increase power output while maintaining safe operating limits."},
        {"name": "Dyno Performance Testing", "description": "Tests the vehicle's power and torque output under load conditions using a dynamometer."},
        {"name": "Cold Air Intake Installation", "description": "Replaces the stock air intake system with a high-performance cold air intake to improve airflow."},
        {"name": "Throttle Response Tuning", "description": "Adjusts electronic throttle settings to deliver sharper or smoother pedal response."},
        {"name": "Fuel System Optimization", "description": "Calibrates the fuel delivery system for improved combustion and engine efficiency."},
    ],
    "MAINTENANCE": [
        {"name": "Oil and Filter Change", "description": "Replaces engine oil and filters to keep the engine clean and running smoothly."},
        {"name": "Fluid Top-Up Service", "description": "Checks and refills essential fluids such as brake, coolant, windshield, and power steering fluids."},
        {"name": "Multi-Point Vehicle Inspection", "description": "Performs a comprehensive check of critical vehicle systems and components for wear or damage."},
        {"name": "Battery Replacement", "description": "Tests and replaces weak or dead vehicle batteries to restore electrical reliability."},
        {"name": "Belt and Hose Check", "description": "Inspects drive belts and radiator hoses for signs of cracking, wear, or leaks."},
        {"name": "Wiper Blade Replacement", "description": "Installs new wiper blades to improve visibility during rain and snow conditions."},
    ],
    "ALIGNMENT": [
        {"name": "Four-Wheel Alignment", "description": "Aligns all four wheels to factory specifications to ensure even tire wear and proper handling."},
        {"name": "Camber and Caster Adjustment", "description": "Adjusts camber and caster angles to correct vehicle drift or uneven tire wear."},
        {"name": "Suspension System Check", "description": "Examines shocks, struts, and other suspension parts for issues affecting alignment and stability."},
        {"name": "Steering System Inspection", "description": "Inspects steering components for play or damage that may affect alignment accuracy."},
        {"name": "Toe-In/Toe-Out Correction", "description": "Fine-tunes the toe settings to correct tracking and ensure smooth driving."},
        {"name": "Tire Wear Pattern Analysis", "description": "Analyzes tire wear patterns to diagnose alignment and suspension issues."},
    ],
    "DIAGNOSTIC": [
        {"name": "OBD-II Fault Scan", "description": "Scans the onboard diagnostic system to retrieve and interpret fault codes for various systems."},
        {"name": "Electrical System Diagnosis", "description": "Checks alternator, battery, and wiring for issues that cause electrical faults or intermittent problems."},
        {"name": "Engine Performance Analysis", "description": "Uses sensors and scan data to analyze misfires, fuel trims, and engine response."},
        {"name": "Sensor Function Test", "description": "Verifies operation of oxygen sensors, mass airflow sensors, and other critical components."},
        {"name": "Check Engine Light Inspection", "description": "Investigates reasons behind the check engine light and recommends corrective action."},
        {"name": "Cooling System Diagnosis", "description": "Assesses radiator, thermostat, and water pump performance to detect overheating causes."},
    ],
    "TIRE": [
        {"name": "Tire Installation", "description": "Installs new tires onto wheels and ensures proper inflation and torque specs."},
        {"name": "Wheel Balancing", "description": "Balances tires to eliminate vibrations and promote even tread wear."},
        {"name": "Tire Puncture Repair", "description": "Seals small punctures or holes in the tire tread caused by road debris."},
        {"name": "Seasonal Tire Changeover", "description": "Swaps summer and winter tires to match driving conditions for the season."},
        {"name": "Tire Pressure Monitoring System (TPMS) Check", "description": "Inspects and resets TPMS sensors for proper function and dashboard alert accuracy."},
        {"name": "Tire Rotation Service", "description": "Rotates tires between positions to even out wear and extend tire life."},
    ],
    "PAINT": [
        {"name": "Scratch and Chip Repair", "description": "Fills and repaints minor surface scratches and paint chips to restore finish."},
        {"name": "Panel Repainting", "description": "Repaints individual body panels using color-matched paint and clear coat."},
        {"name": "Full Vehicle Repaint", "description": "Strips and resprays the entire vehicle with fresh, high-quality automotive paint."},
        {"name": "Clear Coat Restoration", "description": "Polishes and seals the clear coat to enhance gloss and protect against UV damage."},
        {"name": "Bumper Respray", "description": "Repairs and repaints front or rear bumpers that have scuffs, chips, or scratches."},
        {"name": "Paintless Dent Removal", "description": "Removes minor dents and dings without the need for sanding or repainting."},
    ],
    "CARWASH": [
        {"name": "Exterior Hand Wash", "description": "Cleans the exterior using soft mitts, pH-balanced soap, and a spotless rinse."},
        {"name": "Interior Detailing", "description": "Vacuuming, stain removal, and surface cleaning to refresh the interior cabin."},
        {"name": "Wax and Polish Service", "description": "Applies wax and polish to add shine and create a protective barrier on the paint."},
        {"name": "Engine Bay Cleaning", "description": "Degreases and washes the engine compartment for a clean, professional finish."},
        {"name": "Undercarriage Wash", "description": "Rinses salt and grime from the vehicle's undercarriage to prevent rust and corrosion."},
        {"name": "Headlight Restoration", "description": "Polishes cloudy headlights to restore clarity and improve nighttime visibility."},
    ],
}

# Helper to get static image path
def static_image_path(filename):
    return os.path.join(settings.BASE_DIR, 'Auto_Service', 'service', 'static', 'images', filename)

class Command(BaseCommand):
    help = "Generate demo data (users, facilities, appointments, etc.) and optionally dump to a fixture."

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='service/fixtures/populate.json',
                            help='Path where dumpdata should be saved (default: service/fixtures/populate.json)')
        parser.add_argument('--reset', action='store_true', help='Flush existing domain data before seeding')

    @transaction.atomic
    def handle(self, *args, **options):
        output_path = options['output']
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        reset = options['reset']

        if reset:
            self.stdout.write(self.style.WARNING('Reset flag provided – existing objects will be deleted'))
            # Delete in reverse dependency order
            Review.objects.all().delete()
            Appointment.objects.all().delete()
            Vehicle.objects.all().delete()
            Employee.objects.all().delete()
            Customer.objects.all().delete()
            Message.objects.all().delete()
            Notification.objects.all().delete()
            ServiceType.objects.all().delete()
            Facility.objects.all().delete()
            Schedule.objects.all().delete()
            RepairShop.objects.all().delete()
            BaseUser.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()

        # ------------------------------------------------------------------
        # 1. Core users & repair shop
        # ------------------------------------------------------------------
        plain_pw = 'pass@1234'
        admin_user = self._create_user('admin', 'Admin', 'User', 'admin@example.com', plain_pw, is_staff=True, is_superuser=True)
        admin_base = BaseUser.objects.create(user=admin_user, user_type='ADMIN', phone_number=fake.phone_number(), address=fake.address())

        owner_user = self._create_user('owner', 'Owner', 'One', 'owner@example.com', plain_pw)
        owner_base = BaseUser.objects.create(user=owner_user, user_type='OWNER', phone_number=fake.phone_number(), address=fake.address())

        # Repair shop (singleton)
        shop, _ = RepairShop.objects.get_or_create(
            name='Auto Service',
            defaults={
                'address': fake.address(),
                'phone': fake.phone_number(),
                'email': 'info@autoservice.at',
                'website': 'https://autoservice.at',
                'description': 'Your trusted auto service partner.',
                'business_hours': {
                    'Monday': '09:00 - 18:00',
                    'Tuesday': '09:00 - 18:00',
                    'Wednesday': '09:00 - 18:00',
                    'Thursday': '09:00 - 18:00',
                    'Friday': '09:00 - 16:00',
                    'Saturday': '10:00 - 14:00',
                    'Sunday': 'Closed',
                },
                'tax_id': 'AT123456789',
                'registration_number': 'FN123456a',
                'owner': owner_base,
            }
        )

        # ------------------------------------------------------------------
        # 2. Facilities & schedules
        # ------------------------------------------------------------------
        facility_types = [choice[0] for choice in Facility.FACILITY_TYPES]
        facilities = []
        for ft in facility_types:
            fac_name = "Office" if ft == "OFFICE" else f"{ft.capitalize()} Facility"
            facility = Facility.objects.create(
                name=fac_name,
                facility_type=ft,
                description=FACILITY_DESCRIPTIONS.get(ft, fake.paragraph()),
                is_active=True,
                repair_shop=shop,
                capacity=random.randint(2, 8)
            )
            # Attach facility image if a matching static image exists
            fac_img_name = f"{ft.upper()}.jpg"
            fac_img_path = static_image_path(fac_img_name)
            if os.path.exists(fac_img_path):
                with open(fac_img_path, 'rb') as imgf:
                    facility.image.save(fac_img_name, File(imgf), save=True)
            facilities.append(facility)

        # ------------------------------------------------------------------
        # 3. Service Types (3 per facility)
        # ------------------------------------------------------------------
        service_types = []
        for facility in facilities:
            for svc in SERVICE_DEFINITIONS.get(facility.facility_type, []):
                price = random.randint(10, 20) if facility.facility_type == "OFFICE" else random.randint(50, 300)
                st = ServiceType.objects.create(
                    name=svc["name"],
                    description=svc["description"],
                    duration_minutes=random.choice([30, 45, 60, 90]),
                    price=price,
                    facility=facility,
                )
                service_types.append(st)

        # ------------------------------------------------------------------
        # 4. Managers, Supervisors, Technicians, Staff, Secretaries
        # ------------------------------------------------------------------
        def create_role(username_prefix, count, role):
            users = []
            for i in range(count):
                uname = f"{username_prefix}{i+1}"
                user = self._create_user(uname, fake.first_name(), fake.last_name(), f"{uname}@example.com", plain_pw)
                base = BaseUser.objects.create(user=user, user_type=role, phone_number=fake.phone_number(), address=fake.address())
                users.append(base)
            return users

        managers_base = create_role('manager', 3, 'MANAGER')
        supervisors_base = create_role('supervisor', 3, 'SUPERVISOR')
        secretaries = create_role('secretary', 2, 'SECRETARY')
        staff_members = create_role('staff', 2, 'STAFF')

        # Create Employee records for managers and supervisors so they can supervise technicians
        manager_emps = []
        for base in managers_base:
            emp = Employee.objects.create(
                base_user=base,
                supervisor=None,
                facility=random.choice(facilities),
                hire_date=fake.date_between(start_date='-10y', end_date='today'),
                salary=random.randint(40000, 60000),
                is_active=True
            )
            manager_emps.append(emp)

        supervisor_emps = []
        for base in supervisors_base:
            emp = Employee.objects.create(
                base_user=base,
                supervisor=random.choice(manager_emps) if manager_emps else None,
                facility=random.choice(facilities),
                hire_date=fake.date_between(start_date='-10y', end_date='today'),
                salary=random.randint(35000, 55000),
                is_active=True
            )
            supervisor_emps.append(emp)

        # Technicians
        technicians_base = create_role('tech', 20, 'TECHNICIAN')
        technicians = []
        possible_supervisors = supervisor_emps + manager_emps
        for base in technicians_base:
            emp = Employee.objects.create(
                base_user=base,
                supervisor=random.choice(possible_supervisors) if possible_supervisors else None,
                facility=random.choice(facilities),
                hire_date=fake.date_between(start_date='-5y', end_date='today'),
                salary=random.randint(30000, 50000),
                is_active=True
            )
            technicians.append(emp)

        # ------------------------------------------------------------------
        # 5. Customers, Vehicles, Appointments
        # ------------------------------------------------------------------
        customers = []
        for i in range(25):
            uname = f"customer{i+1}"
            user = self._create_user(uname, fake.first_name(), fake.last_name(), f"{uname}@example.com", plain_pw)
            base = BaseUser.objects.create(user=user, user_type='CUSTOMER', phone_number=fake.phone_number(), address=fake.address())
            cust = Customer.objects.create(base_user=base)
            customers.append(cust)

            # each customer 1-2 vehicles
            for _ in range(random.randint(1, 2)):
                make, model = random_make_model()
                v = Vehicle.objects.create(
                    owner=cust,
                    vin=str(uuid.uuid4())[:17].replace('-', '')[:17],
                    make=make,
                    model=model,
                    year=random.randint(2005, 2025),
                    color=random.choice(['Black', 'White', 'Blue', 'Red', 'Silver']),
                    license_plate=fake.license_plate(),
                    registration_date=fake.date_between(start_date='-10y', end_date='today'),
                    mileage=random.randint(50000, 2000000)
                )
                # Try to assign a specific image for Audi models, else use Default_Car.jpg
                car_img_name = None
                if v.make == 'Audi':
                    model_clean = v.model.replace(' ', '_')
                    candidate = f"Audi_{model_clean}.png"
                    candidate_path = static_image_path(candidate)
                    if os.path.exists(candidate_path):
                        car_img_name = candidate
                if not car_img_name:
                    car_img_name = 'Default_Car.jpg'
                car_img_path = static_image_path(car_img_name)
                if os.path.exists(car_img_path):
                    with open(car_img_path, 'rb') as imgf:
                        v.image.save(car_img_name, File(imgf), save=True)
                # each vehicle gets 1-2 appointments
                for _ in range(random.randint(1, 2)):
                    st = random.choice(service_types)
                    appt_status = random.choice(['SCHEDULED', 'COMPLETED', 'CANCELLED'])
                    if appt_status == 'SCHEDULED':
                        appt_date = fake.date_between(start_date='today', end_date='+60d')
                    else:
                        appt_date = fake.date_between(start_date='-60d', end_date='-1d')
                    appt = Appointment.objects.create(
                        customer=cust,
                        vehicle=v,
                        service_type=st,
                        assigned_technician=random.choice(technicians),
                        scheduled_date=appt_date,
                        scheduled_time=fake.time(pattern='%H:%M'),
                        status=appt_status,
                    )
                    if appt_status == 'COMPLETED':
                        Review.objects.create(
                            appointment=appt,
                            rating=random.randint(4, 5),
                            comment=random.choice(REVIEW_COMMENTS),
                            technician_rating=random.randint(4, 5),
                            technician_comment=random.choice(TECH_COMMENTS)
                        )

        # ------------------------------------------------------------------
        # 5b. Ensure each customer has at least one UPCOMING appointment
        # ------------------------------------------------------------------
        today = timezone.localdate()
        for cust in customers:
            has_upcoming = Appointment.objects.filter(
                vehicle__owner=cust,
                status='SCHEDULED',
                scheduled_date__gte=today
            ).exists()

            if not has_upcoming:
                vehicle = cust.vehicles.order_by('?').first()
                if vehicle is None:
                    # Extremely defensive – create a vehicle if somehow missing
                    make, model = random_make_model()
                    vehicle = Vehicle.objects.create(
                        owner=cust,
                        vin=str(uuid.uuid4())[:17].replace('-', '')[:17],
                        make=make,
                        model=model,
                        year=random.randint(2005, 2025),
                        color=random.choice(['Black', 'White', 'Blue', 'Red', 'Silver']),
                        license_plate=fake.license_plate(),
                        registration_date=fake.date_between(start_date='-10y', end_date='today'),
                        mileage=random.randint(50000, 2000000)
                    )

                Appointment.objects.create(
                    customer=cust,
                    vehicle=vehicle,
                    service_type=random.choice(service_types),
                    assigned_technician=random.choice(technicians),
                    scheduled_date=fake.date_between(start_date='today', end_date='+30d'),
                    scheduled_time=fake.time(pattern='%H:%M'),
                    status='SCHEDULED'
                )

        # ------------------------------------------------------------------
        # Guarantee at least one UPCOMING SCHEDULED appointment per technician
        # ------------------------------------------------------------------
        today = timezone.localdate()

        for tech in technicians:
            upcoming_exists = Appointment.objects.filter(
                assigned_technician=tech,
                status='SCHEDULED',
                scheduled_date__gte=today
            ).exists()

            if not upcoming_exists:
                # Select a random customer with at least one vehicle (guaranteed from above)
                cust = random.choice(customers)
                vehicle = cust.vehicles.order_by('?').first()

                # Fallback: extremely defensive – create vehicle if somehow missing
                if vehicle is None:
                    make, model = random_make_model()
                    vehicle = Vehicle.objects.create(
                        owner=cust,
                        vin=str(uuid.uuid4())[:17].replace('-', '')[:17],
                        make=make,
                        model=model,
                        year=random.randint(2005, 2025),
                        color=random.choice(['Black', 'White', 'Blue', 'Red', 'Silver']),
                        license_plate=fake.license_plate(),
                        registration_date=fake.date_between(start_date='-10y', end_date='today'),
                        mileage=random.randint(50000, 2000000)
                    )

                st = random.choice(service_types)

                # Schedule it for today so it shows up immediately on the technician dashboard
                future_date = today

                Appointment.objects.create(
                    customer=cust,
                    vehicle=vehicle,
                    service_type=st,
                    assigned_technician=tech,
                    scheduled_date=future_date,
                    scheduled_time=fake.time(pattern='%H:%M'),
                    status='SCHEDULED'
                )

        # ------------------------------------------------------------------
        # 6. Messages to secretaries
        # ------------------------------------------------------------------
        for sec_base in secretaries:
            for _ in range(random.randint(5, 10)):
                sender_base = random.choice(technicians_base + [c.base_user for c in customers])
                Message.objects.create(
                    sender=sender_base,
                    recipient=sec_base,
                    subject=random.choice(MESSAGE_SUBJECTS),
                    content=random.choice(MESSAGE_CONTENTS),
                    priority=random.choice(['LOW', 'MEDIUM', 'HIGH'])
                )

        self.stdout.write(self.style.SUCCESS('Demo data generated successfully.'))
        self.stdout.write(self.style.SUCCESS(f'All demo accounts use password: {plain_pw}'))

        # Dump data ensuring UTF-8 encoding so special characters are preserved cross-platform
        with open(output_path, 'w', encoding='utf-8') as fixture_file:
            call_command(
                'dumpdata',
                '--exclude', 'contenttypes',
                '--exclude', 'auth.permission',
                '--indent', '2',
                stdout=fixture_file
            )
        self.stdout.write(self.style.SUCCESS(f'Fixture written to {output_path}'))

    def _create_user(self, username, first, last, email, password, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(username=username, defaults={
            'first_name': first,
            'last_name': last,
            'email': email,
            'is_staff': is_staff,
            'is_superuser': is_superuser,
        })
        if created:
            user.set_password(password)
            user.save()
        return user 
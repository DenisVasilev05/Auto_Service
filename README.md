# (Auto Service) Car repair shop management system


## Features

* **Landing page** showcasing featured facilities, services and customer reviews.
* **Customer dashboard** – register, add vehicles, book & track appointments, leave reviews.
* **Technician dashboard** – see assigned jobs, start/complete services, update notes.
* **(Still under development) Manager/Owner dashboard** – high-level analytics, facility management, user administration.
* **Facility pages** with equipment, working hours & service catalogue.
* **Notifications** for status updates & messages.
* **Seed script** that generates realistic demo data for easier testing of the workflow (customers, employees, vehicles, facilities, appointments).

---

## How to get this project running:

### 1. Clone and enter the project folder

```bash
git clone https://github.com/IMC-UAS-Krems/assignment-2-DenisVasilev05.git
cd Auto_Service
```

### 2. Create & activate a virtual environment

```bash
py -m venv venv               # Python ≥ 3.10 (This project was created with Python 3.13)
# Windows (PowerShell command prompt)
venv\Scripts\activate
```
!!! Important: If you get an error for unauthorized access while trying to activate the virtual environment, please run the following command to allow for script execution for the current session:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```
After this, please run the virtual environment activation command like this:
```bash
venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

The most important packages are:

* Django 5.2.3 – the web framework
* Pillow 11.2.1 – image processing for uploaded vehicle/facility images
* Faker 37.4.0 – used to generate fake customers, appointments, etc.

### 4. Run initial database migrations

```bash
py manage.py migrate
```

SQLite is used for data persistence

### 5. Load demo data

```bash
py manage.py seed_demo_data --reset
```
This command fills the DB with a repair-shop profile, facilities, customers, employees, vehicles, future appointments and reviews.
The singleton pattern is implemented in the model to assure that only one instance of the repair shop is created.
Keep in mind that the seeding takes some time.
After seeding, a single password (pass@1234) is assigned to all generated users and is printed in the console.
Available usernames: customer1, customer2, customer3 ...
                     tech1, tech2, tech3 ...

### 6. (Optional) create a super-user to gain access to the admin interface

```bash
py manage.py createsuperuser
```

### 7. Start the development server

```bash
py manage.py runserver 8000
```

### 8. Open the web application 
Open http://127.0.0.1:8000/ in your browser


## How to Use the Application

### Public Visitor

1. Landing page → browse highlighted facilities & services.
2. "Sign Up" → create a customer account.

### Customer Workflow

1. **Dashboard** – shows your vehicles & upcoming appointments.
2. **Add Vehicle** form – register your car details.
3. **Browse Facilities / Services** and book and appointment with a service for your desired car
4. **Create Appointment** – pick vehicle, service & date/time.
5. **Track appointments** – Appointments update to *Scheduled*, *In Progress*, *Completed*.
6. **Leave a review** – when the service is completed you can rate the job.

### Technician Workflow

*Log in with a staff account that has the `TECHNICIAN` role (username: tech1 or tech2 or tech3 ...) (seed script creates a few).*  The dashboard lists today's jobs and upcoming appointments. Technicians can:

* Start an appointment → status becomes **IN_PROGRESS**.
* Complete an appointment → customer is notified & can review.
* View personal performance stats (reviews, completion rate).

### Manager / Admin Workflow

* Visit `/admin/` for the classic Django admin interface.
* (Still under development) In-app dashboards give counts of appointments, technicians, etc.
* (Not implemented) Manage facilities – update descriptions, capacity, working hours, temporary closures.

---

## Project Structure

```
Auto_Service/
├── service/             ← The repair shop management system application (models, views, templates)
├── media/               ← Uploaded images (at runtime)
├── static/              ← Static assets and resources (Bootstrap, css, scripts, images)
├── templates/           ← The views
├── manage.py
└── requirements.txt
```
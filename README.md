[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Zj5S3O5Q)

# Auto Service Management System

## Setup

1. Clone the repository
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Apply migrations
```bash
cd Auto_Service
python manage.py migrate
```

5. Load initial data
```bash
python manage.py load_initial_data
```

6. Run development server
```bash
python manage.py runserver 8000
```

Default users:
- Admin: username=admin, password=admin123
- Owner: username=owner, password=owner123
- Customer: username=customer1, password=customer1123

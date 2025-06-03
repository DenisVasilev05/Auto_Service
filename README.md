[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Zj5S3O5Q)

# Auto Service Management System

## Quick Setup

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
python manage.py loaddata service/fixtures/populate.json
```

6. Run development server
```bash
python manage.py runserver
```

Default users:
- Admin: username=admin, password=password123
- Owner: username=owner, password=password123
- Customer: username=customer1, password=password123

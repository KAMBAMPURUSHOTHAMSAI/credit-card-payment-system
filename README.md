# Credit Card Payment System

A full-stack credit card payment system built using React, Tailwind CSS, Django, FastAPI, and MySQL.

## Features
- User registration and JWT login
- Secure password hashing
- Credit/Debit card management
- Masked card number storage
- Payment processing with simulated SUCCESS/FAILED result
- Transaction history and filters
- Django admin dashboard
- Daily payment summary
- CSV transaction export
- FastAPI Swagger documentation
- Postman API collection
- Docker Compose deployment
- Automated tests

## Technology Stack
| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS, Vite, Axios |
| Backend | Django REST Framework, FastAPI |
| Authentication | JWT |
| Database | MySQL 8 |
| ORM | Django ORM, SQLAlchemy |
| Testing | Pytest, Django Test Framework, Coverage |
| Deployment | Docker, Docker Compose |

## Project Structure
```text
credit-card-payment-system/
+-- backend/
¦   +-- django_app/
¦   +-- fastapi/
+-- frontend/
+-- postman/
+-- database/
+-- docker/
+-- docs/
+-- docker-compose.yml
+-- .gitignore
+-- README.md
```

## Local URLs
- React: http://localhost:5173
- Django: http://localhost:8000
- Django API Docs: http://localhost:8000/api/docs/
- FastAPI Swagger: http://localhost:8001/docs

## Docker
Start all services:
```bash
docker compose up -d --build
```

Check services:
```bash
docker compose ps
```

Services:
- MySQL: host port 3307
- Django: port 8000
- FastAPI: port 8001
- Frontend: port 5173

## API Documentation
See docs/API.md for API details.

## Database Schema
See docs/DB_SCHEMA.md for database tables and security notes.

## Postman
- postman/Credit-Card-Payment-System.postman_collection.json
- postman/Credit-Card-Payment-System.postman_environment.json

## Database Dump
- database/credit_card_payment_system.sql

## Security
- CVV is not stored
- Full card numbers are not stored
- Only masked card number and last 4 digits are stored
- Passwords are stored using Django password hashing
- JWT authentication protects API access
- Input validation is implemented
- Django ORM and SQLAlchemy are used for database access

## Testing
- Django tests: 7/7 passing
- Django coverage: 81%
- FastAPI tests: 6/6 passing
- FastAPI coverage: 90%

## Screenshots
UI screenshots are stored in docs/screenshots/.

## Setup
1. Install Docker Desktop.
2. Clone the repository.
3. Copy .env.example to .env and set secure local values.
4. Run docker compose up -d --build.
5. Open the frontend at http://localhost:5173.

## Notes
Do not commit the .env file or other secrets to the repository.

## Admin Credentials
Admin account details are documented in docs/ADMIN_CREDENTIALS.md.
The admin password is not stored in Git.

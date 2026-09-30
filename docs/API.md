# API Documentation

## Django API

Base URL: http://localhost:8000/api

### Authentication
- POST /auth/register/
- POST /auth/login/
- POST /auth/refresh/
- POST /auth/logout/

### Cards
- GET /cards/
- POST /cards/
- DELETE /cards/{id}/

### Transactions
- GET /transactions/
- Date, amount, and status filters are supported.

### Admin
- GET /admin/dashboard/
- GET /admin/transactions/export/

### Django API Docs
http://localhost:8000/api/docs/

## FastAPI Payment API

Base URL: http://localhost:8001

### Health
- GET /health

### Payments
- POST /api/payments/
- Requires JWT authentication.
- Creates a transaction with PENDING status before simulated processing.
- Final status is SUCCESS or FAILED.

### Swagger
http://localhost:8001/docs

## Authentication
Protected endpoints use:
Authorization: Bearer <access_token>

## Postman
The Postman collection contains authentication, card, payment, transaction, and admin requests.

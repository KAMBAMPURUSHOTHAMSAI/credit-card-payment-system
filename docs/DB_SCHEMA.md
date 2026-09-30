# Database Schema

Database: credit_card_payment_system
Engine: MySQL 8

## Main Tables

### accounts_user
- Application user records
- Password field contains Django hashed passwords

### payments_card
- id
- user_id
- card_type
- card_brand
- masked_number
- last4
- expiry_month
- expiry_year
- is_active

The system does not store the full card number or CVV.

### payments_transaction
- id
- user_id
- card_id
- amount
- currency
- status
- reference
- description
- failure_reason
- created_at
- updated_at

Transaction status values used by the payment flow include PENDING, SUCCESS, and FAILED.

### payments_adminlog
- Stores admin activity such as daily summary viewing and CSV export operations.

### Django Support Tables
- django_admin_log
- django_content_type
- django_migrations
- django_session
- auth_group
- auth_group_permissions
- auth_permission
- accounts_user_groups
- accounts_user_user_permissions

### JWT Blacklist Tables
- token_blacklist_blacklistedtoken
- token_blacklist_outstandingtoken

The submitted database dump excludes live JWT token data from these blacklist tables.

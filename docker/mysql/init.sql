CREATE DATABASE IF NOT EXISTS credit_card_payment_system;
GRANT ALL PRIVILEGES ON `credit_card_payment_system%`.* TO 'credit_user'@'%';
GRANT CREATE, DROP ON *.* TO 'credit_user'@'%';
FLUSH PRIVILEGES;

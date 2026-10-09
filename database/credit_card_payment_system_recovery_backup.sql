-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: credit_card_payment_system_recovery
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `credit_card_payment_system_recovery`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `credit_card_payment_system_recovery` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `credit_card_payment_system_recovery`;

--
-- Table structure for table `accounts_user`
--

DROP TABLE IF EXISTS `accounts_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `email` varchar(254) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user`
--

LOCK TABLES `accounts_user` WRITE;
/*!40000 ALTER TABLE `accounts_user` DISABLE KEYS */;
INSERT INTO `accounts_user` VALUES (1,'pbkdf2_sha256$600000$oCxnbIdnbXSOW2DYkdu5o7$BnjB29pcA9DQKstAk09Opotd2ZAyDImyMKicj+F77Bk=',NULL,0,'Purushotham','Purushotham','Sai',0,1,'2026-09-30 05:57:36.003478','kambampurushothamsai16@gmail.com'),(2,'pbkdf2_sha256$600000$Fe9amsV9CnYHQ65jPK3NJm$YhwZXT5DO7Z7KGxSCgyTlqKHQ/FPwd8XZpI/rmf3fco=',NULL,1,'Sai','','',1,1,'2026-09-30 06:09:42.864140','admin@gmail.com');
/*!40000 ALTER TABLE `accounts_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_groups`
--

DROP TABLE IF EXISTS `accounts_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_groups`
--

LOCK TABLES `accounts_user_groups` WRITE;
/*!40000 ALTER TABLE `accounts_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_user_permissions`
--

DROP TABLE IF EXISTS `accounts_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_user_permissions`
--

LOCK TABLES `accounts_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `accounts_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add blacklisted token',6,'add_blacklistedtoken'),(22,'Can change blacklisted token',6,'change_blacklistedtoken'),(23,'Can delete blacklisted token',6,'delete_blacklistedtoken'),(24,'Can view blacklisted token',6,'view_blacklistedtoken'),(25,'Can add outstanding token',7,'add_outstandingtoken'),(26,'Can change outstanding token',7,'change_outstandingtoken'),(27,'Can delete outstanding token',7,'delete_outstandingtoken'),(28,'Can view outstanding token',7,'view_outstandingtoken'),(29,'Can add user',8,'add_user'),(30,'Can change user',8,'change_user'),(31,'Can delete user',8,'delete_user'),(32,'Can view user',8,'view_user'),(33,'Can add card',9,'add_card'),(34,'Can change card',9,'change_card'),(35,'Can delete card',9,'delete_card'),(36,'Can view card',9,'view_card'),(37,'Can add transaction',10,'add_transaction'),(38,'Can change transaction',10,'change_transaction'),(39,'Can delete transaction',10,'delete_transaction'),(40,'Can view transaction',10,'view_transaction'),(41,'Can add admin log',11,'add_adminlog'),(42,'Can change admin log',11,'change_adminlog'),(43,'Can delete admin log',11,'delete_adminlog'),(44,'Can view admin log',11,'view_adminlog');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (8,'accounts','user'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'contenttypes','contenttype'),(11,'payments','adminlog'),(9,'payments','card'),(10,'payments','transaction'),(5,'sessions','session'),(6,'token_blacklist','blacklistedtoken'),(7,'token_blacklist','outstandingtoken');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-09-30 05:44:58.448071'),(2,'contenttypes','0002_remove_content_type_name','2026-09-30 05:44:59.827894'),(3,'auth','0001_initial','2026-09-30 05:45:02.253770'),(4,'auth','0002_alter_permission_name_max_length','2026-09-30 05:45:02.743418'),(5,'auth','0003_alter_user_email_max_length','2026-09-30 05:45:02.774756'),(6,'auth','0004_alter_user_username_opts','2026-09-30 05:45:02.812634'),(7,'auth','0005_alter_user_last_login_null','2026-09-30 05:45:02.847232'),(8,'auth','0006_require_contenttypes_0002','2026-09-30 05:45:02.878925'),(9,'auth','0007_alter_validators_add_error_messages','2026-09-30 05:45:02.909933'),(10,'auth','0008_alter_user_username_max_length','2026-09-30 05:45:02.944305'),(11,'auth','0009_alter_user_last_name_max_length','2026-09-30 05:45:02.979106'),(12,'auth','0010_alter_group_name_max_length','2026-09-30 05:45:03.066879'),(13,'auth','0011_update_proxy_permissions','2026-09-30 05:45:03.103713'),(14,'auth','0012_alter_user_first_name_max_length','2026-09-30 05:45:03.131397'),(15,'accounts','0001_initial','2026-09-30 05:45:06.033754'),(16,'admin','0001_initial','2026-09-30 05:45:07.248084'),(17,'admin','0002_logentry_remove_auto_add','2026-09-30 05:45:07.279761'),(18,'admin','0003_logentry_add_action_flag_choices','2026-09-30 05:45:07.314301'),(19,'payments','0001_initial','2026-09-30 05:45:10.132168'),(20,'sessions','0001_initial','2026-09-30 05:45:10.439661'),(21,'token_blacklist','0001_initial','2026-09-30 05:45:11.566436'),(22,'token_blacklist','0002_outstandingtoken_jti_hex','2026-09-30 05:45:12.038628'),(23,'token_blacklist','0003_auto_20171017_2007','2026-09-30 05:45:12.075852'),(24,'token_blacklist','0004_auto_20171017_2013','2026-09-30 05:45:12.651357'),(25,'token_blacklist','0005_remove_outstandingtoken_jti','2026-09-30 05:45:13.137317'),(26,'token_blacklist','0006_auto_20171017_2113','2026-09-30 05:45:13.273974'),(27,'token_blacklist','0007_auto_20171017_2214','2026-09-30 05:45:14.771731'),(28,'token_blacklist','0008_migrate_to_bigautofield','2026-09-30 05:45:17.007406'),(29,'token_blacklist','0010_fix_migrate_to_bigautofield','2026-09-30 05:45:17.051320'),(30,'token_blacklist','0011_linearizes_history','2026-09-30 05:45:17.081342'),(31,'token_blacklist','0012_alter_outstandingtoken_user','2026-09-30 05:45:17.118532');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments_adminlog`
--

DROP TABLE IF EXISTS `payments_adminlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments_adminlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(100) NOT NULL,
  `target` varchar(100) NOT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `admin_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `payments_adminlog_admin_id_387c0391_fk_accounts_user_id` (`admin_id`),
  CONSTRAINT `payments_adminlog_admin_id_387c0391_fk_accounts_user_id` FOREIGN KEY (`admin_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments_adminlog`
--

LOCK TABLES `payments_adminlog` WRITE;
/*!40000 ALTER TABLE `payments_adminlog` DISABLE KEYS */;
INSERT INTO `payments_adminlog` VALUES (1,'VIEW_DAILY_SUMMARY','DAILY_SUMMARY','172.18.0.1','2026-09-30 06:10:50.855215',2),(2,'VIEW_DAILY_SUMMARY','DAILY_SUMMARY','172.18.0.1','2026-09-30 06:11:23.295774',2),(3,'VIEW_DAILY_SUMMARY','DAILY_SUMMARY','172.18.0.1','2026-09-30 06:11:23.323629',2),(4,'EXPORT_TRANSACTIONS','TRANSACTIONS_CSV','172.18.0.1','2026-09-30 06:11:41.889175',2);
/*!40000 ALTER TABLE `payments_adminlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments_card`
--

DROP TABLE IF EXISTS `payments_card`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments_card` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `card_type` varchar(10) NOT NULL,
  `card_brand` varchar(30) NOT NULL,
  `masked_number` varchar(20) NOT NULL,
  `last4` varchar(4) NOT NULL,
  `expiry_month` smallint unsigned NOT NULL,
  `expiry_year` smallint unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `payments_card_user_id_0982ae65_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `payments_card_user_id_0982ae65_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `payments_card_chk_1` CHECK ((`expiry_month` >= 0)),
  CONSTRAINT `payments_card_chk_2` CHECK ((`expiry_year` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments_card`
--

LOCK TABLES `payments_card` WRITE;
/*!40000 ALTER TABLE `payments_card` DISABLE KEYS */;
INSERT INTO `payments_card` VALUES (1,'CREDIT','VISA','************4242','4242',12,2028,1,'2026-09-30 06:00:18.113049',1);
/*!40000 ALTER TABLE `payments_card` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments_transaction`
--

DROP TABLE IF EXISTS `payments_transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments_transaction` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(3) NOT NULL,
  `status` varchar(10) NOT NULL,
  `reference` varchar(64) NOT NULL,
  `description` varchar(255) NOT NULL,
  `failure_reason` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `card_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reference` (`reference`),
  KEY `payments_transaction_card_id_3930bc5d_fk_payments_card_id` (`card_id`),
  KEY `payments_transaction_user_id_ca456f41_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `payments_transaction_card_id_3930bc5d_fk_payments_card_id` FOREIGN KEY (`card_id`) REFERENCES `payments_card` (`id`),
  CONSTRAINT `payments_transaction_user_id_ca456f41_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments_transaction`
--

LOCK TABLES `payments_transaction` WRITE;
/*!40000 ALTER TABLE `payments_transaction` DISABLE KEYS */;
INSERT INTO `payments_transaction` VALUES (1,1000.00,'INR','SUCCESS','PAY-B2F4816D61C84CDE','Docker payment test','','2026-09-30 06:01:06.823169','2026-09-30 06:01:06.839986',1,1);
/*!40000 ALTER TABLE `payments_transaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `token_blacklist_blacklistedtoken`
--

DROP TABLE IF EXISTS `token_blacklist_blacklistedtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `token_blacklist_blacklistedtoken` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `blacklisted_at` datetime(6) NOT NULL,
  `token_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_id` (`token_id`),
  CONSTRAINT `token_blacklist_blacklistedtoken_token_id_3cc7fe56_fk` FOREIGN KEY (`token_id`) REFERENCES `token_blacklist_outstandingtoken` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `token_blacklist_blacklistedtoken`
--

LOCK TABLES `token_blacklist_blacklistedtoken` WRITE;
/*!40000 ALTER TABLE `token_blacklist_blacklistedtoken` DISABLE KEYS */;
/*!40000 ALTER TABLE `token_blacklist_blacklistedtoken` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `token_blacklist_outstandingtoken`
--

DROP TABLE IF EXISTS `token_blacklist_outstandingtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `token_blacklist_outstandingtoken` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `token` longtext NOT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `expires_at` datetime(6) NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `jti` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_blacklist_outstandingtoken_jti_hex_d9bdf6f7_uniq` (`jti`),
  KEY `token_blacklist_outs_user_id_83bc629a_fk_accounts_` (`user_id`),
  CONSTRAINT `token_blacklist_outs_user_id_83bc629a_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `token_blacklist_outstandingtoken`
--

LOCK TABLES `token_blacklist_outstandingtoken` WRITE;
/*!40000 ALTER TABLE `token_blacklist_outstandingtoken` DISABLE KEYS */;
/*!40000 ALTER TABLE `token_blacklist_outstandingtoken` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-09  7:46:26

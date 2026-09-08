-- MySQL dump 10.13  Distrib 8.0.32, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: ops_manager
-- ------------------------------------------------------
-- Server version	5.7.24

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table ops_man_datacenter
--

DROP TABLE IF EXISTS ops_man_datacenter;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_datacenter (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) COLLATE latin1_general_cs NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name_UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_datacenter
--

LOCK TABLES ops_man_datacenter WRITE;
/*!40000 ALTER TABLE ops_man_datacenter DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_datacenter ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_environment
--

DROP TABLE IF EXISTS ops_man_environment;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_environment (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) COLLATE latin1_general_cs NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name_UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_environment
--

LOCK TABLES ops_man_environment WRITE;
/*!40000 ALTER TABLE ops_man_environment DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_environment ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_ldap_group
--

DROP TABLE IF EXISTS ops_man_ldap_group;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_ldap_group (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) COLLATE latin1_general_cs NOT NULL,
  linux_group_id int(11) DEFAULT NULL,
  linux_group_name varchar(255) COLLATE latin1_general_cs NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name_UNIQUE (name),
  UNIQUE KEY linux_group_name_UNIQUE (linux_group_name),
  UNIQUE KEY linux_group_id_UNIQUE (linux_group_id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_ldap_group
--

LOCK TABLES ops_man_ldap_group WRITE;
/*!40000 ALTER TABLE ops_man_ldap_group DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_ldap_group ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_ldap_user
--

DROP TABLE IF EXISTS ops_man_ldap_user;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_ldap_user (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) COLLATE latin1_general_cs NOT NULL,
  username varchar(255) COLLATE latin1_general_cs NOT NULL,
  email varchar(255) COLLATE latin1_general_cs NOT NULL,
  title varchar(255) COLLATE latin1_general_cs DEFAULT NULL,
  department varchar(255) COLLATE latin1_general_cs DEFAULT NULL,
  manager varchar(255) COLLATE latin1_general_cs DEFAULT NULL,
  linux_user_id int(11) DEFAULT NULL,
  password varchar(1024) COLLATE latin1_general_cs NOT NULL,
  ops_man_ldap_group int(11) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY username_UNIQUE (username),
  UNIQUE KEY email_UNIQUE (email),
  UNIQUE KEY linux_user_id_UNIQUE (linux_user_id),
  /*UNIQUE KEY password_UNIQUE (password),*/
  KEY ops_man_1_idx (ops_man_ldap_group),
  CONSTRAINT ops_man_1 FOREIGN KEY (ops_man_ldap_group) REFERENCES ops_man_ldap_group (id) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_ldap_user
--

LOCK TABLES ops_man_ldap_user WRITE;
/*!40000 ALTER TABLE ops_man_ldap_user DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_ldap_user ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_ldap_user_attribute
--

DROP TABLE IF EXISTS ops_man_ldap_user_attribute;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_ldap_user_attribute (
  id int(11) NOT NULL AUTO_INCREMENT,
  ops_man_ldap_user_id int(11) NOT NULL,
  ops_man_ldap_user_attribute_type_id int(11) NOT NULL,
  value varchar(255) COLLATE latin1_general_cs NOT NULL,
  PRIMARY KEY (id),
  KEY ops_man_2_idx (ops_man_ldap_user_id),
  KEY ops_man_3_idx (ops_man_ldap_user_attribute_type_id),
  CONSTRAINT ops_man_2 FOREIGN KEY (ops_man_ldap_user_id) REFERENCES ops_man_ldap_user (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ops_man_3 FOREIGN KEY (ops_man_ldap_user_attribute_type_id) REFERENCES ops_man_ldap_user_attribute_type (id) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_ldap_user_attribute
--

LOCK TABLES ops_man_ldap_user_attribute WRITE;
/*!40000 ALTER TABLE ops_man_ldap_user_attribute DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_ldap_user_attribute ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_ldap_user_attribute_type
--

DROP TABLE IF EXISTS ops_man_ldap_user_attribute_type;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_ldap_user_attribute_type (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) COLLATE latin1_general_cs NOT NULL,
  `limit` int(11) NOT NULL DEFAULT '1',
  PRIMARY KEY (id),
  UNIQUE KEY name_UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_ldap_user_attribute_type
--

LOCK TABLES ops_man_ldap_user_attribute_type WRITE;
/*!40000 ALTER TABLE ops_man_ldap_user_attribute_type DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_ldap_user_attribute_type ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_permission_matrix
--

DROP TABLE IF EXISTS ops_man_permission_matrix;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_permission_matrix (
  id int(11) NOT NULL AUTO_INCREMENT,
  ops_man_datacenter_id int(11) NOT NULL,
  ops_man_environment_id int(11) NOT NULL,
  ops_man_ldap_group_id int(11) NOT NULL,
  PRIMARY KEY (id),
  KEY ops_man_4_idx (ops_man_datacenter_id),
  KEY ops_man_5_idx (ops_man_environment_id),
  KEY ops_man_6_idx (ops_man_ldap_group_id),
  CONSTRAINT ops_man_4 FOREIGN KEY (ops_man_datacenter_id) REFERENCES ops_man_datacenter (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ops_man_5 FOREIGN KEY (ops_man_environment_id) REFERENCES ops_man_environment (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ops_man_6 FOREIGN KEY (ops_man_ldap_group_id) REFERENCES ops_man_ldap_group (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_permission_matrix
--

LOCK TABLES ops_man_permission_matrix WRITE;
/*!40000 ALTER TABLE ops_man_permission_matrix DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_permission_matrix ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_tenant
--

DROP TABLE IF EXISTS ops_man_tenant;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_tenant (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) COLLATE latin1_general_cs NOT NULL,
  service_id int(11) NOT NULL,
  linux_username varchar(255) COLLATE latin1_general_cs NOT NULL,
  linux_uid int(11) NOT NULL,
  is_disabled tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (id),
  UNIQUE KEY name_UNIQUE (name),
  UNIQUE KEY service_id_UNIQUE (service_id),
  UNIQUE KEY linux_username_UNIQUE (linux_username),
  UNIQUE KEY linux_uid_UNIQUE (linux_uid)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_tenant
--

LOCK TABLES ops_man_tenant WRITE;
/*!40000 ALTER TABLE ops_man_tenant DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_tenant ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_tenant_attribute
--

DROP TABLE IF EXISTS ops_man_tenant_attribute;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_tenant_attribute (
  id int(11) NOT NULL AUTO_INCREMENT,
  ops_man_tenant_id int(11) NOT NULL,
  ops_man_tenant_attribute_type_id int(11) NOT NULL,
  value varchar(255) COLLATE latin1_general_cs NOT NULL,
  PRIMARY KEY (id),
  KEY ops_man_8_idx (ops_man_tenant_id),
  KEY ops_man_9_idx (ops_man_tenant_attribute_type_id),
  CONSTRAINT ops_man_8 FOREIGN KEY (ops_man_tenant_id) REFERENCES ops_man_tenant (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ops_man_9 FOREIGN KEY (ops_man_tenant_attribute_type_id) REFERENCES ops_man_tenant_attribute_type (id) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_tenant_attribute
--

LOCK TABLES ops_man_tenant_attribute WRITE;
/*!40000 ALTER TABLE ops_man_tenant_attribute DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_tenant_attribute ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table ops_man_tenant_attribute_type
--

DROP TABLE IF EXISTS ops_man_tenant_attribute_type;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE ops_man_tenant_attribute_type (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) COLLATE latin1_general_cs NOT NULL,
  `limit` int(11) NOT NULL DEFAULT '1',
  PRIMARY KEY (id),
  UNIQUE KEY name_UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table ops_man_tenant_attribute_type
--

LOCK TABLES ops_man_tenant_attribute_type WRITE;
/*!40000 ALTER TABLE ops_man_tenant_attribute_type DISABLE KEYS */;
/*!40000 ALTER TABLE ops_man_tenant_attribute_type ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

ALTER TABLE ops_man_ldap_user_attribute
drop FOREIGN KEY ops_man_3;

ALTER TABLE ops_man_ldap_user_attribute
ADD CONSTRAINT ops_man_3 FOREIGN KEY (ops_man_ldap_user_attribute_type_id) REFERENCES ops_man_ldap_user_attribute_type (id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE ops_man_tenant_attribute
drop FOREIGN KEY ops_man_9;

ALTER TABLE ops_man_tenant_attribute
ADD CONSTRAINT ops_man_9 FOREIGN KEY (ops_man_tenant_attribute_type_id) REFERENCES ops_man_tenant_attribute_type (id) ON DELETE CASCADE ON UPDATE CASCADE;


ALTER TABLE ops_man_ldap_user
ADD Column password_expiry_at datetime;



ALTER TABLE ops_man_ldap_user
drop FOREIGN KEY ops_man_1;

ALTER TABLE ops_man_ldap_user
ADD CONSTRAINT ops_man_1 FOREIGN KEY (ops_man_ldap_group) REFERENCES ops_man_ldap_group (id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE ops_man_ldap_group
ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0;

/* Start: New change 1 */
ALTER TABLE ops_man_ldap_user
MODIFY name varchar(255) NULL;

ALTER TABLE ops_man_ldap_user
MODIFY email varchar(255) NULL;


ALTER TABLE ops_man_tenant_attribute
MODIFY `value` TEXT;

ALTER TABLE ops_man_ldap_user_attribute
MODIFY `value` TEXT;

CREATE TABLE ops_man_history (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(255),
    `action` VARCHAR(255),
    `target` VARCHAR(255),
    `data_json` TEXT,
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE `ops_manager`.`ops_man_ldap_group` 
CHANGE COLUMN `linux_group_name` `linux_group_name` VARCHAR(255) NULL DEFAULT NULL ,
DROP INDEX `linux_group_id_UNIQUE` ,
DROP INDEX `linux_group_name_UNIQUE` ;
;

INSERT INTO `ops_manager`.`ops_man_tenant_attribute_type` (`name`, `limit`) VALUES ('ssh_key', '10');
INSERT INTO `ops_manager`.`ops_man_ldap_user_attribute_type` (`name`, `limit`) VALUES ('password_linux', '1');
INSERT INTO `ops_manager`.`ops_man_ldap_user_attribute_type` (`name`, `limit`) VALUES ('password_mysql', '1');
INSERT INTO `ops_manager`.`ops_man_ldap_user_attribute_type` (`name`, `limit`) VALUES ('password_svn', '1');
INSERT INTO `ops_manager`.`ops_man_ldap_user_attribute_type` (`name`, `limit`) VALUES ('ssh_key', '10');

ALTER TABLE ops_man_ldap_group
ADD COLUMN is_admin_tenant TINYINT(1) NOT NULL DEFAULT 0;

ALTER TABLE ops_man_tenant
ADD COLUMN is_sftp TINYINT(1) NOT NULL DEFAULT 0;


ALTER TABLE `ops_manager`.`ops_man_tenant` 
CHANGE COLUMN `is_sftp` `is_sftp` TINYINT(1) NOT NULL DEFAULT 1;

ALTER TABLE `ops_manager`.`ops_man_tenant` 
CHANGE COLUMN `is_disabled` `is_disabled` TINYINT(1) NOT NULL DEFAULT 1;

/* End: New change 1 */

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-02-21 14:34:57
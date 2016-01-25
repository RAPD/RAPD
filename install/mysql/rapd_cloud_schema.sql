-- MySQL dump 10.15  Distrib 10.0.23-MariaDB, for Linux (x86_64)
--
-- Host: rapd    Database: rapd_cloud
-- ------------------------------------------------------
-- Server version	10.0.23-MariaDB-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `cloud_complete`
--

DROP TABLE IF EXISTS `cloud_complete`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_complete` (
  `cloud_complete_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `cloud_request_id` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `request_timestamp` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `start_timestamp` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `request_type` varchar(12) DEFAULT NULL,
  `status` varchar(12) DEFAULT NULL,
  `ip_address` varchar(15) DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `archive` varchar(96) DEFAULT NULL,
  PRIMARY KEY (`cloud_complete_id`)
) ENGINE=MyISAM AUTO_INCREMENT=17737 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cloud_current`
--

DROP TABLE IF EXISTS `cloud_current`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_current` (
  `cloud_current_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `cloud_request_id` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `request_timestamp` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`cloud_current_id`)
) ENGINE=MyISAM AUTO_INCREMENT=36757 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cloud_requests`
--

DROP TABLE IF EXISTS `cloud_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_requests` (
  `cloud_request_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `request_type` varchar(12) DEFAULT NULL,
  `original_result_id` mediumint(8) unsigned DEFAULT NULL,
  `original_type` varchar(12) DEFAULT NULL,
  `original_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `new_setting_id` mediumint(8) unsigned DEFAULT NULL,
  `additional_image` mediumint(8) unsigned DEFAULT NULL,
  `mk3_phi` float DEFAULT NULL,
  `mk3_kappa` float DEFAULT NULL,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `input_sca` varchar(256) DEFAULT NULL,
  `input_mtz` varchar(256) DEFAULT NULL,
  `input_map` varchar(256) DEFAULT NULL,
  `ha_type` varchar(2) DEFAULT NULL,
  `ha_number` tinyint(3) unsigned DEFAULT NULL,
  `shelxd_try` smallint(5) unsigned DEFAULT NULL,
  `sad_res` float DEFAULT NULL,
  `sequence` varchar(10000) DEFAULT NULL,
  `pdbs_id` mediumint(8) unsigned DEFAULT NULL,
  `nmol` tinyint(3) unsigned DEFAULT NULL,
  `frame_start` smallint(5) unsigned DEFAULT NULL,
  `frame_finish` smallint(5) unsigned DEFAULT NULL,
  `status` varchar(8) DEFAULT NULL,
  `ip_address` varchar(15) DEFAULT '0.0.0.0',
  `puckset_id` mediumint(8) unsigned DEFAULT NULL,
  `option1` varchar(12) DEFAULT NULL,
  `peak_id` mediumint(8) unsigned DEFAULT NULL,
  `inflection_id` mediumint(8) unsigned DEFAULT NULL,
  `hiremote_id` mediumint(8) unsigned DEFAULT NULL,
  `loremote_id` mediumint(8) unsigned DEFAULT NULL,
  `native_id` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`cloud_request_id`),
  KEY `status` (`status`)
) ENGINE=MyISAM AUTO_INCREMENT=38576 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cloud_state`
--

DROP TABLE IF EXISTS `cloud_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_state` (
  `everything` tinyint(3) unsigned DEFAULT NULL,
  `processing` tinyint(3) unsigned DEFAULT NULL,
  `download` tinyint(3) unsigned DEFAULT NULL,
  `remote_processing` tinyint(3) unsigned DEFAULT NULL,
  `remote_download` tinyint(3) unsigned DEFAULT NULL,
  `remote_concurrent_allowed` smallint(5) unsigned DEFAULT NULL,
  `current_queue` smallint(5) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `coordinate`
--

DROP TABLE IF EXISTS `coordinate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `coordinate` (
  `event_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `event` varchar(12) DEFAULT NULL,
  `ip_address` varchar(15) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`event_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `datacollection`
--

DROP TABLE IF EXISTS `datacollection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datacollection` (
  `datacollection_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `group_id` mediumint(8) unsigned DEFAULT NULL,
  `prefix` varchar(64) DEFAULT NULL,
  `run_number` tinyint(3) unsigned DEFAULT NULL,
  `image_start` smallint(5) unsigned DEFAULT NULL,
  `omega_start` float DEFAULT NULL,
  `delta_omega` float DEFAULT NULL,
  `number_images` smallint(5) unsigned DEFAULT NULL,
  `time` float DEFAULT NULL,
  `distance` float DEFAULT NULL,
  `transmission` float DEFAULT NULL,
  `kappa` float DEFAULT NULL,
  `phi` float DEFAULT NULL,
  `beamline` varchar(16) DEFAULT NULL,
  `ip_address` varchar(15) DEFAULT NULL,
  `status` varchar(12) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`datacollection_id`),
  KEY `status` (`status`)
) ENGINE=MyISAM AUTO_INCREMENT=84 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `minikappa`
--

DROP TABLE IF EXISTS `minikappa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `minikappa` (
  `minikappa_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `omega` float DEFAULT NULL,
  `kappa` float DEFAULT NULL,
  `phi` float DEFAULT NULL,
  `beamline` varchar(16) DEFAULT NULL,
  `ip_address` varchar(15) DEFAULT NULL,
  `status` varchar(12) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`minikappa_id`)
) ENGINE=MyISAM AUTO_INCREMENT=675 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-01-21 15:07:59

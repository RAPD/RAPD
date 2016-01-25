-- MySQL dump 10.15  Distrib 10.0.23-MariaDB, for Linux (x86_64)
--
-- Host: rapd    Database: rapd_data
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
-- Table structure for table `autosol_results`
--

DROP TABLE IF EXISTS `autosol_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autosol_results` (
  `autosol_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `sad_result_id` mediumint(8) unsigned DEFAULT NULL,
  `directory` varchar(256) DEFAULT NULL,
  `spacegroup` varchar(8) DEFAULT NULL,
  `wavelength` float DEFAULT NULL,
  `ha_type` varchar(2) DEFAULT NULL,
  `fprime` float DEFAULT NULL,
  `f2prime` float DEFAULT NULL,
  `sites_start` tinyint(3) unsigned DEFAULT NULL,
  `sites_refined` tinyint(3) unsigned DEFAULT NULL,
  `res_built` smallint(5) unsigned DEFAULT NULL,
  `side_built` smallint(5) unsigned DEFAULT NULL,
  `number_chains` tinyint(3) unsigned DEFAULT NULL,
  `model_map_cc` float DEFAULT NULL,
  `fom` float DEFAULT NULL,
  `den_mod_r` float DEFAULT NULL,
  `bayes_cc` float DEFAULT NULL,
  `r` float DEFAULT NULL,
  `rfree` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`autosol_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2299 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `beamcenter`
--

DROP TABLE IF EXISTS `beamcenter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `beamcenter` (
  `beamcenter_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `beamline` varchar(16) DEFAULT NULL,
  `x_b` float DEFAULT NULL,
  `x_m1` float DEFAULT NULL,
  `x_m2` float DEFAULT NULL,
  `x_m3` float DEFAULT NULL,
  `x_m4` float DEFAULT NULL,
  `x_m5` float DEFAULT NULL,
  `x_m6` float DEFAULT NULL,
  `x_r` float DEFAULT NULL,
  `y_b` float DEFAULT NULL,
  `y_m1` float DEFAULT NULL,
  `y_m2` float DEFAULT NULL,
  `y_m3` float DEFAULT NULL,
  `y_m4` float DEFAULT NULL,
  `y_m5` float DEFAULT NULL,
  `y_m6` float DEFAULT NULL,
  `y_r` float DEFAULT NULL,
  `image_ids` varchar(512) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`beamcenter_id`),
  KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cell_analysis_results`
--

DROP TABLE IF EXISTS `cell_analysis_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cell_analysis_results` (
  `cell_analysis_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `sad_result_id` mediumint(8) unsigned DEFAULT NULL,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `pdb_id` varchar(6) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `automr_sg` varchar(8) DEFAULT NULL,
  `automr_rfz` float DEFAULT NULL,
  `automr_tfz` float DEFAULT NULL,
  `automr_gain` float DEFAULT NULL,
  `automr_tar` varchar(256) DEFAULT NULL,
  `automr_adf` varchar(256) DEFAULT NULL,
  `automr_peaks` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`cell_analysis_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=1275956 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `current`
--

DROP TABLE IF EXISTS `current`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `current` (
  `beamline` varchar(12) NOT NULL DEFAULT '',
  `setting_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `puckset_id` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`beamline`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diffcenter_results`
--

DROP TABLE IF EXISTS `diffcenter_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `diffcenter_results` (
  `diffcenter_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `image_id` int(10) unsigned DEFAULT NULL,
  `fullname` varchar(256) DEFAULT NULL,
  `sample_id` mediumint(8) unsigned DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `ice_rings` float DEFAULT NULL,
  `max_cell` float DEFAULT NULL,
  `distl_res` float DEFAULT NULL,
  `overloads` smallint(5) unsigned DEFAULT NULL,
  `labelit_res` float DEFAULT NULL,
  `total_spots` smallint(5) unsigned DEFAULT NULL,
  `good_b_spots` smallint(5) unsigned DEFAULT NULL,
  `max_signal_str` float DEFAULT NULL,
  `mean_int_signal` float DEFAULT NULL,
  `min_signal_str` float DEFAULT NULL,
  `total_signal` int(10) unsigned DEFAULT NULL,
  `in_res_spots` smallint(5) unsigned DEFAULT NULL,
  `saturation_50` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`diffcenter_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=21314 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `image_status`
--

DROP TABLE IF EXISTS `image_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `image_status` (
  `image_status_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `fullname` varchar(128) DEFAULT NULL,
  `directory` varchar(128) DEFAULT NULL,
  `image_prefix` varchar(64) DEFAULT NULL,
  `run_number` smallint(5) unsigned DEFAULT NULL,
  `image_number` smallint(5) unsigned DEFAULT NULL,
  `adsc_number` mediumint(8) unsigned DEFAULT NULL,
  `beamline` varchar(8) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`image_status_id`),
  UNIQUE KEY `blocker` (`fullname`,`adsc_number`)
) ENGINE=MyISAM AUTO_INCREMENT=790342 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `images` (
  `image_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `fullname` varchar(128) DEFAULT NULL,
  `adsc_number` mediumint(8) unsigned DEFAULT NULL,
  `adc` varchar(5) DEFAULT NULL,
  `axis` varchar(6) DEFAULT NULL,
  `beam_center_x` float DEFAULT NULL,
  `beam_center_y` float DEFAULT NULL,
  `binning` varchar(5) DEFAULT NULL,
  `byte_order` varchar(14) DEFAULT NULL,
  `ccd_image_saturation` smallint(5) unsigned DEFAULT NULL,
  `count_cutoff` mediumint(8) unsigned DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `detector` varchar(12) DEFAULT NULL,
  `detector_sn` varchar(12) DEFAULT NULL,
  `collect_mode` varchar(8) DEFAULT NULL,
  `dim` tinyint(4) DEFAULT NULL,
  `distance` float DEFAULT NULL,
  `header_bytes` smallint(6) DEFAULT NULL,
  `osc_range` float DEFAULT NULL,
  `osc_start` float DEFAULT NULL,
  `phi` float DEFAULT NULL,
  `kappa` float DEFAULT NULL,
  `pixel_size` float DEFAULT NULL,
  `size1` smallint(5) unsigned DEFAULT NULL,
  `size2` smallint(5) unsigned DEFAULT NULL,
  `time` float DEFAULT NULL,
  `period` float DEFAULT NULL,
  `twotheta` float DEFAULT NULL,
  `type` varchar(15) DEFAULT NULL,
  `unif_ped` smallint(6) DEFAULT NULL,
  `wavelength` float DEFAULT NULL,
  `directory` varchar(128) DEFAULT NULL,
  `image_prefix` varchar(64) DEFAULT NULL,
  `run_number` smallint(5) unsigned DEFAULT NULL,
  `image_number` smallint(5) unsigned DEFAULT NULL,
  `transmission` float DEFAULT NULL,
  `puck` varchar(1) DEFAULT NULL,
  `sample` tinyint(3) unsigned DEFAULT NULL,
  `sample_id` mediumint(8) unsigned DEFAULT NULL,
  `ring_current` float DEFAULT NULL,
  `ring_mode` varchar(48) DEFAULT NULL,
  `md2_aperture` tinyint(3) unsigned DEFAULT NULL,
  `md2_prg_exp` float DEFAULT NULL,
  `md2_net_exp` mediumint(8) unsigned DEFAULT NULL,
  `md2_x` float DEFAULT NULL,
  `md2_y` float DEFAULT NULL,
  `md2_z` float DEFAULT NULL,
  `acc_time` mediumint(8) unsigned DEFAULT NULL,
  `beamline` varchar(8) DEFAULT NULL,
  `calc_beam_center_x` float DEFAULT NULL,
  `calc_beam_center_y` float DEFAULT NULL,
  `flux` float DEFAULT NULL,
  `beam_size_x` float DEFAULT NULL,
  `beam_size_y` float DEFAULT NULL,
  `gauss_x` float DEFAULT NULL,
  `gauss_y` float DEFAULT NULL,
  `run_id` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`image_id`),
  UNIQUE KEY `blocker` (`fullname`,`adsc_number`,`date`),
  KEY `run_id` (`run_id`),
  KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=9488341 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `integrate_results`
--

DROP TABLE IF EXISTS `integrate_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `integrate_results` (
  `integrate_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `run_id` mediumint(8) unsigned DEFAULT NULL,
  `sample_id` mediumint(8) unsigned DEFAULT NULL,
  `version` smallint(5) unsigned DEFAULT '0',
  `pipeline` varchar(12) DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `request_id` mediumint(8) unsigned DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `template` varchar(256) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `type` varchar(12) DEFAULT NULL,
  `images_dir` varchar(256) DEFAULT NULL,
  `image_start` smallint(5) unsigned DEFAULT NULL,
  `image_end` smallint(5) unsigned DEFAULT NULL,
  `integrate_status` varchar(12) DEFAULT NULL,
  `solved` varchar(8) DEFAULT NULL,
  `parsed` varchar(256) DEFAULT NULL,
  `summary_long` varchar(256) DEFAULT NULL,
  `plots` varchar(256) DEFAULT NULL,
  `xia_log` varchar(256) DEFAULT NULL,
  `xds_log` varchar(256) DEFAULT NULL,
  `xscale_log` varchar(256) DEFAULT NULL,
  `scala_log` varchar(256) DEFAULT NULL,
  `unmerged_sca_file` varchar(256) DEFAULT NULL,
  `sca_file` varchar(256) DEFAULT NULL,
  `mtz_file` varchar(256) DEFAULT NULL,
  `hkl_file` varchar(256) DEFAULT NULL,
  `merge_file` varchar(256) DEFAULT NULL,
  `download_file` varchar(256) DEFAULT NULL,
  `wavelength` float DEFAULT NULL,
  `spacegroup` varchar(12) DEFAULT NULL,
  `a` float DEFAULT NULL,
  `b` float DEFAULT NULL,
  `c` float DEFAULT NULL,
  `alpha` float DEFAULT NULL,
  `beta` float DEFAULT NULL,
  `gamma` float DEFAULT NULL,
  `twinscore` float DEFAULT NULL,
  `rd_analysis` float DEFAULT NULL,
  `rd_conclusion` varchar(16) DEFAULT NULL,
  `cc_anom` float DEFAULT NULL,
  `cc_cut_res` float DEFAULT NULL,
  `cc_cut_val` float DEFAULT NULL,
  `rcr_anom` float DEFAULT NULL,
  `rcr_cut_res` float DEFAULT NULL,
  `rcr_cut_val` float DEFAULT NULL,
  `proc_time` time DEFAULT NULL,
  `shell_overall` mediumint(8) unsigned DEFAULT NULL,
  `shell_inner` mediumint(8) unsigned DEFAULT NULL,
  `shell_outer` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`integrate_result_id`),
  KEY `result_id` (`result_id`),
  CONSTRAINT `integrate_results_ibfk_1` FOREIGN KEY (`result_id`) REFERENCES `results` (`result_id`)
) ENGINE=InnoDB AUTO_INCREMENT=79462 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `integrate_shell_results`
--

DROP TABLE IF EXISTS `integrate_shell_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `integrate_shell_results` (
  `isr_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `shell_type` varchar(8) DEFAULT NULL,
  `high_res` float DEFAULT NULL,
  `low_res` float DEFAULT NULL,
  `completeness` float DEFAULT NULL,
  `multiplicity` float DEFAULT NULL,
  `i_sigma` float DEFAULT NULL,
  `cc_half` float DEFAULT NULL,
  `r_merge` float DEFAULT NULL,
  `r_merge_anom` float DEFAULT NULL,
  `r_meas` float DEFAULT NULL,
  `r_meas_pm` float DEFAULT NULL,
  `r_pim` float DEFAULT NULL,
  `r_pim_pm` float DEFAULT NULL,
  `wilson_b` float DEFAULT NULL,
  `partial_bias` float DEFAULT NULL,
  `anom_completeness` float DEFAULT NULL,
  `anom_multiplicity` float DEFAULT NULL,
  `anom_correlation` float DEFAULT NULL,
  `anom_slope` float DEFAULT NULL,
  `total_obs` int(10) unsigned DEFAULT NULL,
  `unique_obs` int(10) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`isr_id`)
) ENGINE=MyISAM AUTO_INCREMENT=230759 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mad_results`
--

DROP TABLE IF EXISTS `mad_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mad_results` (
  `mad_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `request_id` mediumint(8) unsigned DEFAULT NULL,
  `source_data_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `version` smallint(5) unsigned DEFAULT '0',
  `mad_status` varchar(8) DEFAULT NULL,
  `shelxc_result_id` mediumint(8) unsigned DEFAULT NULL,
  `shelxd_result_id` mediumint(8) unsigned DEFAULT NULL,
  `shelxe_result_id` mediumint(8) unsigned DEFAULT NULL,
  `autosol_result_id` mediumint(8) unsigned DEFAULT NULL,
  `shelx_html` varchar(256) DEFAULT NULL,
  `shelx_plots` varchar(256) DEFAULT NULL,
  `autosol_html` varchar(256) DEFAULT NULL,
  `autosol_pdb` varchar(256) DEFAULT NULL,
  `autosol_mtz` varchar(256) DEFAULT NULL,
  `download_file` varchar(256) DEFAULT NULL,
  `shelxd_ha_pdb` varchar(256) DEFAULT NULL,
  `shelxe_phs` varchar(256) DEFAULT NULL,
  `shelx_tar` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`mad_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `merge_results`
--

DROP TABLE IF EXISTS `merge_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `merge_results` (
  `merge_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `request_id` mediumint(8) unsigned DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `set1` mediumint(8) unsigned DEFAULT NULL,
  `set2` mediumint(8) unsigned DEFAULT NULL,
  `merge_status` varchar(12) DEFAULT NULL,
  `solved` varchar(8) DEFAULT NULL,
  `summary` varchar(256) DEFAULT NULL,
  `details` varchar(256) DEFAULT NULL,
  `plots` varchar(256) DEFAULT NULL,
  `merge_file` varchar(256) DEFAULT NULL,
  `mtz_file` varchar(256) DEFAULT NULL,
  `download_file` varchar(256) DEFAULT NULL,
  `wavelength` float DEFAULT NULL,
  `spacegroup` varchar(12) DEFAULT NULL,
  `a` float DEFAULT NULL,
  `b` float DEFAULT NULL,
  `c` float DEFAULT NULL,
  `alpha` float DEFAULT NULL,
  `beta` float DEFAULT NULL,
  `gamma` float DEFAULT NULL,
  `shell_overall` mediumint(8) unsigned DEFAULT NULL,
  `shell_inner` mediumint(8) unsigned DEFAULT NULL,
  `shell_outer` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`merge_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=3675 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `merge_shell_results`
--

DROP TABLE IF EXISTS `merge_shell_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `merge_shell_results` (
  `msr_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `shell_type` varchar(8) DEFAULT NULL,
  `high_res` float DEFAULT NULL,
  `low_res` float DEFAULT NULL,
  `completeness` float DEFAULT NULL,
  `multiplicity` float DEFAULT NULL,
  `i_sigma` float DEFAULT NULL,
  `r_merge` float DEFAULT NULL,
  `r_meas` float DEFAULT NULL,
  `r_meas_pm` float DEFAULT NULL,
  `r_pim` float DEFAULT NULL,
  `r_pim_pm` float DEFAULT NULL,
  `wilson_b` float DEFAULT NULL,
  `partial_bias` float DEFAULT NULL,
  `anom_completeness` float DEFAULT NULL,
  `anom_multiplicity` float DEFAULT NULL,
  `anom_correlation` float DEFAULT NULL,
  `anom_slope` float DEFAULT NULL,
  `total_obs` int(10) unsigned DEFAULT NULL,
  `unique_obs` int(10) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`msr_id`)
) ENGINE=MyISAM AUTO_INCREMENT=9361 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mr_results`
--

DROP TABLE IF EXISTS `mr_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mr_results` (
  `mr_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `request_id` mediumint(8) unsigned DEFAULT NULL,
  `source_data_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `version` smallint(5) unsigned DEFAULT '0',
  `mr_status` varchar(8) DEFAULT NULL,
  `summary_html` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`mr_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=3882 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mr_trial_results`
--

DROP TABLE IF EXISTS `mr_trial_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mr_trial_results` (
  `mr_trial_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `mr_result_id` mediumint(8) unsigned DEFAULT NULL,
  `gain` float DEFAULT NULL,
  `rfz` float DEFAULT NULL,
  `tfz` float DEFAULT NULL,
  `spacegroup` varchar(12) DEFAULT NULL,
  `archive` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`mr_trial_id`)
) ENGINE=MyISAM AUTO_INCREMENT=10186 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `orphan_results`
--

DROP TABLE IF EXISTS `orphan_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orphan_results` (
  `orphan_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `type` varchar(6) DEFAULT NULL,
  `data_root_dir` varchar(128) DEFAULT NULL,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  PRIMARY KEY (`orphan_result_id`),
  UNIQUE KEY `blocker` (`type`,`data_root_dir`,`result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=19631 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pair_results`
--

DROP TABLE IF EXISTS `pair_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pair_results` (
  `pair_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `fullname_1` varchar(256) DEFAULT NULL,
  `image1_id` int(10) unsigned DEFAULT NULL,
  `adsc_number_1` mediumint(8) unsigned DEFAULT NULL,
  `date_1` datetime DEFAULT NULL,
  `fullname_2` varchar(256) DEFAULT NULL,
  `image2_id` int(10) unsigned DEFAULT NULL,
  `adsc_number_2` mediumint(8) unsigned DEFAULT NULL,
  `date_2` datetime DEFAULT NULL,
  `sample_id` mediumint(8) unsigned DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `type` varchar(12) DEFAULT NULL,
  `distl_status` varchar(8) DEFAULT NULL,
  `distl_res_1` float DEFAULT NULL,
  `distl_labelit_res_1` float DEFAULT NULL,
  `distl_ice_rings_1` smallint(5) unsigned DEFAULT NULL,
  `distl_total_spots_1` mediumint(8) unsigned DEFAULT NULL,
  `distl_spots_in_res_1` mediumint(8) unsigned DEFAULT NULL,
  `distl_good_bragg_spots_1` mediumint(8) unsigned DEFAULT NULL,
  `distl_overloads_1` mediumint(8) unsigned DEFAULT NULL,
  `distl_max_cell_1` float DEFAULT NULL,
  `distl_mean_int_signal_1` mediumint(8) unsigned DEFAULT NULL,
  `distl_min_signal_strength_1` mediumint(8) unsigned DEFAULT NULL,
  `distl_max_signal_strength_1` mediumint(8) unsigned DEFAULT NULL,
  `distl_res_2` float DEFAULT NULL,
  `distl_labelit_res_2` float DEFAULT NULL,
  `distl_ice_rings_2` smallint(5) unsigned DEFAULT NULL,
  `distl_total_spots_2` mediumint(8) unsigned DEFAULT NULL,
  `distl_spots_in_res_2` mediumint(8) unsigned DEFAULT NULL,
  `distl_good_bragg_spots_2` mediumint(8) unsigned DEFAULT NULL,
  `distl_overloads_2` mediumint(8) unsigned DEFAULT NULL,
  `distl_max_cell_2` float DEFAULT NULL,
  `distl_mean_int_signal_2` mediumint(8) unsigned DEFAULT NULL,
  `distl_min_signal_strength_2` mediumint(8) unsigned DEFAULT NULL,
  `distl_max_signal_strength_2` mediumint(8) unsigned DEFAULT NULL,
  `labelit_status` varchar(8) DEFAULT NULL,
  `labelit_iteration` tinyint(3) unsigned DEFAULT NULL,
  `labelit_res` float DEFAULT NULL,
  `labelit_spots_fit` mediumint(8) unsigned DEFAULT NULL,
  `labelit_metric` float DEFAULT NULL,
  `labelit_spacegroup` varchar(8) DEFAULT NULL,
  `labelit_distance` float DEFAULT NULL,
  `labelit_x_beam` float DEFAULT NULL,
  `labelit_y_beam` float DEFAULT NULL,
  `labelit_a` float DEFAULT NULL,
  `labelit_b` float DEFAULT NULL,
  `labelit_c` float DEFAULT NULL,
  `labelit_alpha` float DEFAULT NULL,
  `labelit_beta` float DEFAULT NULL,
  `labelit_gamma` float DEFAULT NULL,
  `labelit_mosaicity` float DEFAULT NULL,
  `labelit_rmsd` float DEFAULT NULL,
  `raddose_status` varchar(8) DEFAULT NULL,
  `raddose_dose_per_image` float DEFAULT NULL,
  `raddose_adjusted_dose` float DEFAULT NULL,
  `raddose_henderson_limit` mediumint(8) unsigned DEFAULT NULL,
  `raddose_exp_dose_limit` mediumint(8) unsigned DEFAULT NULL,
  `best_complexity` varchar(8) DEFAULT NULL,
  `best_norm_status` varchar(8) DEFAULT NULL,
  `best_norm_res_limit` float DEFAULT NULL,
  `best_norm_completeness` float DEFAULT NULL,
  `best_norm_atten` float DEFAULT NULL,
  `best_norm_rot_range` float DEFAULT NULL,
  `best_norm_phi_end` float DEFAULT NULL,
  `best_norm_total_exp` float DEFAULT NULL,
  `best_norm_redundancy` float DEFAULT NULL,
  `best_norm_i_sigi_all` float DEFAULT NULL,
  `best_norm_i_sigi_high` float DEFAULT NULL,
  `best_norm_r_all` float DEFAULT NULL,
  `best_norm_r_high` float DEFAULT NULL,
  `best_norm_unique_in_blind` float DEFAULT NULL,
  `best_anom_status` varchar(8) DEFAULT NULL,
  `best_anom_res_limit` float DEFAULT NULL,
  `best_anom_completeness` float DEFAULT NULL,
  `best_anom_atten` float DEFAULT NULL,
  `best_anom_rot_range` float DEFAULT NULL,
  `best_anom_phi_end` float DEFAULT NULL,
  `best_anom_total_exp` float DEFAULT NULL,
  `best_anom_redundancy` float DEFAULT NULL,
  `best_anom_i_sigi_all` float DEFAULT NULL,
  `best_anom_i_sigi_high` float DEFAULT NULL,
  `best_anom_r_all` float DEFAULT NULL,
  `best_anom_r_high` float DEFAULT NULL,
  `best_anom_unique_in_blind` float DEFAULT NULL,
  `mosflm_norm_status` varchar(8) DEFAULT NULL,
  `mosflm_norm_res_limit` float DEFAULT NULL,
  `mosflm_norm_completeness` float DEFAULT NULL,
  `mosflm_norm_redundancy` float DEFAULT NULL,
  `mosflm_norm_distance` float DEFAULT NULL,
  `mosflm_norm_delta_phi` float DEFAULT NULL,
  `mosflm_norm_img_exposure_time` float DEFAULT NULL,
  `mosflm_anom_status` varchar(8) DEFAULT NULL,
  `mosflm_anom_res_limit` float DEFAULT NULL,
  `mosflm_anom_completeness` float DEFAULT NULL,
  `mosflm_anom_redundancy` float DEFAULT NULL,
  `mosflm_anom_distance` float DEFAULT NULL,
  `mosflm_anom_delta_phi` float DEFAULT NULL,
  `mosflm_anom_img_exposure_time` float DEFAULT NULL,
  `summary_short` varchar(128) DEFAULT NULL,
  `summary_long` varchar(128) DEFAULT NULL,
  `summary_stac` varchar(128) DEFAULT NULL,
  `image_small_1` varchar(128) DEFAULT NULL,
  `image_big_1` varchar(128) DEFAULT NULL,
  `image_small_2` varchar(128) DEFAULT NULL,
  `image_big_2` varchar(128) DEFAULT NULL,
  `image_raw_1` varchar(256) DEFAULT NULL,
  `image_preds_1` varchar(256) DEFAULT NULL,
  `image_raw_2` varchar(256) DEFAULT NULL,
  `image_preds_2` varchar(256) DEFAULT NULL,
  `best_plots` varchar(128) DEFAULT NULL,
  `best_plots_anom` varchar(128) DEFAULT NULL,
  `stac_file1` varchar(256) DEFAULT NULL,
  `stac_file2` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pair_result_id`),
  KEY `result_id` (`result_id`),
  CONSTRAINT `pair_results_ibfk_1` FOREIGN KEY (`result_id`) REFERENCES `results` (`result_id`)
) ENGINE=InnoDB AUTO_INCREMENT=338740 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pdbs`
--

DROP TABLE IF EXISTS `pdbs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pdbs` (
  `pdbs_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `pdb_file` varchar(128) DEFAULT NULL,
  `pdb_name` varchar(128) DEFAULT NULL,
  `pdb_description` varchar(256) DEFAULT NULL,
  `location` varchar(256) DEFAULT NULL,
  `username` varchar(48) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `pdbs_id` (`pdbs_id`)
) ENGINE=MyISAM AUTO_INCREMENT=1500 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `presets`
--

DROP TABLE IF EXISTS `presets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `presets` (
  `presets_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `setting_id` mediumint(8) unsigned DEFAULT NULL,
  `beamline` varchar(12) DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`presets_id`)
) ENGINE=MyISAM AUTO_INCREMENT=117 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `processes`
--

DROP TABLE IF EXISTS `processes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `processes` (
  `process_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `type` varchar(12) DEFAULT NULL,
  `rtype` varchar(12) DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `display` varchar(12) DEFAULT 'show',
  `progress` tinyint(3) unsigned DEFAULT '0',
  `timestamp1` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `timestamp2` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`process_id`),
  KEY `data_root_dir` (`data_root_dir`),
  KEY `timestamp1` (`timestamp1`)
) ENGINE=MyISAM AUTO_INCREMENT=1093613 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `projects` (
  `project_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `project` varchar(48) DEFAULT NULL,
  `protein` varchar(48) DEFAULT NULL,
  `ligand` varchar(48) DEFAULT NULL,
  `project_type` varchar(12) DEFAULT NULL,
  `seq` varchar(1000) DEFAULT NULL,
  `mw` float DEFAULT NULL,
  `solvent` float DEFAULT NULL,
  `metal` varchar(8) DEFAULT NULL,
  `sites` tinyint(3) unsigned DEFAULT NULL,
  `pdb` varchar(8) DEFAULT NULL,
  `username` varchar(48) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`project_id`),
  UNIQUE KEY `project` (`project`)
) ENGINE=MyISAM AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `puck_settings`
--

DROP TABLE IF EXISTS `puck_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `puck_settings` (
  `puckset_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `beamline` varchar(16) DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `A` varchar(48) DEFAULT NULL,
  `B` varchar(48) DEFAULT NULL,
  `C` varchar(48) DEFAULT NULL,
  `D` varchar(48) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `puckset_id` (`puckset_id`)
) ENGINE=MyISAM AUTO_INCREMENT=73 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `qa_results`
--

DROP TABLE IF EXISTS `qa_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `qa_results` (
  `qa_result_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` bigint(20) unsigned DEFAULT NULL,
  `image_id` bigint(20) unsigned DEFAULT NULL,
  PRIMARY KEY (`qa_result_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `quickanalysis_results`
--

DROP TABLE IF EXISTS `quickanalysis_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `quickanalysis_results` (
  `quickanalysis_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `image_id` int(10) unsigned DEFAULT NULL,
  `fullname` varchar(256) DEFAULT NULL,
  `sample_id` mediumint(8) unsigned DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `ice_rings` float DEFAULT NULL,
  `max_cell` float DEFAULT NULL,
  `distl_res` float DEFAULT NULL,
  `overloads` smallint(5) unsigned DEFAULT NULL,
  `labelit_res` float DEFAULT NULL,
  `total_spots` smallint(5) unsigned DEFAULT NULL,
  `good_b_spots` smallint(5) unsigned DEFAULT NULL,
  `max_signal_str` float DEFAULT NULL,
  `mean_int_signal` float DEFAULT NULL,
  `min_signal_str` float DEFAULT NULL,
  `total_signal` int(10) unsigned DEFAULT NULL,
  `in_res_spots` smallint(5) unsigned DEFAULT NULL,
  `saturation_50` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`quickanalysis_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=1018453 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapd_config`
--

DROP TABLE IF EXISTS `rapd_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapd_config` (
  `descriptor` varchar(24) NOT NULL DEFAULT '',
  `controller_ip` varchar(15) DEFAULT NULL,
  `detector_ip` varchar(15) DEFAULT NULL,
  `cluster_ip` varchar(15) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`descriptor`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapd_status`
--

DROP TABLE IF EXISTS `rapd_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapd_status` (
  `ip_address` varchar(15) DEFAULT NULL,
  `type` varchar(12) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `blocker` (`ip_address`,`type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reference_data`
--

DROP TABLE IF EXISTS `reference_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reference_data` (
  `reference_data_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id_1` mediumint(8) unsigned DEFAULT NULL,
  `result_id_2` mediumint(8) unsigned DEFAULT NULL,
  `result_id_3` mediumint(8) unsigned DEFAULT NULL,
  `result_id_4` mediumint(8) unsigned DEFAULT NULL,
  `result_id_5` mediumint(8) unsigned DEFAULT NULL,
  `result_id_6` mediumint(8) unsigned DEFAULT NULL,
  `result_id_7` mediumint(8) unsigned DEFAULT NULL,
  `result_id_8` mediumint(8) unsigned DEFAULT NULL,
  `result_id_9` mediumint(8) unsigned DEFAULT NULL,
  `result_id_10` mediumint(8) unsigned DEFAULT NULL,
  `snap_id` mediumint(8) unsigned DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reference_data_id`)
) ENGINE=MyISAM AUTO_INCREMENT=294 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `results`
--

DROP TABLE IF EXISTS `results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `results` (
  `result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `type` varchar(12) DEFAULT NULL,
  `id` mediumint(8) unsigned DEFAULT NULL,
  `setting_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `sample_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `display` varchar(12) DEFAULT 'show',
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`result_id`),
  KEY `data_root_dir` (`data_root_dir`),
  KEY `timestamp` (`timestamp`),
  KEY `result_id` (`result_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1098483 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `run_status`
--

DROP TABLE IF EXISTS `run_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `run_status` (
  `run_status_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `adc` varchar(5) DEFAULT NULL,
  `anom_wedge` tinyint(3) unsigned DEFAULT NULL,
  `anomalous` varchar(4) DEFAULT NULL,
  `beam_center` varchar(20) DEFAULT NULL,
  `binning` varchar(5) DEFAULT NULL,
  `comment` varchar(128) DEFAULT NULL,
  `compression` varchar(4) DEFAULT NULL,
  `directory` varchar(128) DEFAULT NULL,
  `image_prefix` varchar(64) DEFAULT NULL,
  `mad` varchar(4) DEFAULT NULL,
  `mode` varchar(5) DEFAULT NULL,
  `beamline` varchar(8) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`run_status_id`),
  UNIQUE KEY `blocker` (`adc`,`anom_wedge`,`anomalous`,`beam_center`,`binning`,`comment`,`compression`,`directory`,`image_prefix`,`mad`,`mode`)
) ENGINE=MyISAM AUTO_INCREMENT=4758 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `runs`
--

DROP TABLE IF EXISTS `runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `runs` (
  `run_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `directory` varchar(128) DEFAULT NULL,
  `image_prefix` varchar(64) DEFAULT NULL,
  `run_number` smallint(5) unsigned DEFAULT NULL,
  `start` smallint(5) unsigned DEFAULT NULL,
  `total` smallint(5) unsigned DEFAULT NULL,
  `distance` float DEFAULT NULL,
  `twotheta` float DEFAULT NULL,
  `phi` float DEFAULT NULL,
  `kappa` float DEFAULT NULL,
  `omega` float DEFAULT NULL,
  `axis` varchar(6) DEFAULT NULL,
  `width` float DEFAULT NULL,
  `time` float DEFAULT NULL,
  `de_zngr` varchar(5) DEFAULT NULL,
  `anomalous` varchar(3) DEFAULT NULL,
  `beamline` varchar(8) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`run_id`),
  UNIQUE KEY `blocker` (`directory`,`image_prefix`,`run_number`,`start`)
) ENGINE=InnoDB AUTO_INCREMENT=92553 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sad_results`
--

DROP TABLE IF EXISTS `sad_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sad_results` (
  `sad_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `request_id` mediumint(8) unsigned DEFAULT NULL,
  `source_data_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `version` smallint(5) unsigned DEFAULT '0',
  `sad_status` varchar(8) DEFAULT NULL,
  `shelxc_result_id` mediumint(8) unsigned DEFAULT NULL,
  `shelxd_result_id` mediumint(8) unsigned DEFAULT NULL,
  `shelxe_result_id` mediumint(8) unsigned DEFAULT NULL,
  `autosol_result_id` mediumint(8) unsigned DEFAULT NULL,
  `shelx_html` varchar(256) DEFAULT NULL,
  `shelx_plots` varchar(256) DEFAULT NULL,
  `autosol_html` varchar(256) DEFAULT NULL,
  `autosol_pdb` varchar(256) DEFAULT NULL,
  `autosol_mtz` varchar(256) DEFAULT NULL,
  `download_file` varchar(256) DEFAULT NULL,
  `shelxd_ha_pdb` varchar(256) DEFAULT NULL,
  `shelxe_phs` varchar(256) DEFAULT NULL,
  `shelx_tar` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`sad_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4256 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `samples`
--

DROP TABLE IF EXISTS `samples`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `samples` (
  `sample_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `sheetname` varchar(48) DEFAULT NULL,
  `PuckID` varchar(48) DEFAULT NULL,
  `sample` tinyint(3) DEFAULT NULL,
  `CrystalID` varchar(48) DEFAULT NULL,
  `Protein` varchar(48) DEFAULT NULL,
  `ligand` varchar(48) DEFAULT NULL,
  `Comment` varchar(128) DEFAULT NULL,
  `FreezingCondition` varchar(128) DEFAULT NULL,
  `CrystalCondition` varchar(128) DEFAULT NULL,
  `Metal` varchar(8) DEFAULT NULL,
  `Project` varchar(48) DEFAULT NULL,
  `Person` varchar(48) DEFAULT NULL,
  `username` varchar(48) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sample_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2949 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `settings` (
  `setting_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `beamline` varchar(12) DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `multiprocessing` varchar(5) DEFAULT NULL,
  `spacegroup` varchar(12) DEFAULT NULL,
  `sample_type` varchar(12) DEFAULT NULL,
  `solvent_content` float DEFAULT NULL,
  `susceptibility` float DEFAULT NULL,
  `crystal_size_x` smallint(5) unsigned DEFAULT NULL,
  `crystal_size_y` smallint(5) unsigned DEFAULT NULL,
  `crystal_size_z` smallint(5) unsigned DEFAULT NULL,
  `a` float DEFAULT NULL,
  `b` float DEFAULT NULL,
  `c` float DEFAULT NULL,
  `alpha` float DEFAULT NULL,
  `beta` float DEFAULT NULL,
  `gamma` float DEFAULT NULL,
  `work_dir_override` varchar(5) DEFAULT NULL,
  `work_directory` varchar(256) DEFAULT NULL,
  `beam_flip` varchar(5) DEFAULT NULL,
  `x_beam` varchar(12) DEFAULT NULL,
  `y_beam` varchar(12) DEFAULT NULL,
  `index_hi_res` float DEFAULT NULL,
  `strategy_type` varchar(8) DEFAULT NULL,
  `best_complexity` varchar(4) DEFAULT NULL,
  `mosflm_seg` tinyint(3) unsigned DEFAULT NULL,
  `mosflm_rot` float DEFAULT NULL,
  `mosflm_start` float DEFAULT '0',
  `mosflm_end` float DEFAULT '360',
  `min_exposure_per` float DEFAULT NULL,
  `aimed_res` float DEFAULT NULL,
  `beam_size_x` varchar(12) DEFAULT NULL,
  `beam_size_y` varchar(12) DEFAULT NULL,
  `integrate` varchar(5) DEFAULT NULL,
  `reference_data_id` mediumint(8) unsigned DEFAULT '0',
  `setting_type` varchar(8) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`setting_id`)
) ENGINE=MyISAM AUTO_INCREMENT=11764 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shelxc_results`
--

DROP TABLE IF EXISTS `shelxc_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shelxc_results` (
  `shelxc_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `sad_result_id` mediumint(8) unsigned DEFAULT NULL,
  `resolutions` varchar(256) DEFAULT NULL,
  `completeness` varchar(256) DEFAULT NULL,
  `dsig` varchar(256) DEFAULT NULL,
  `isig` varchar(256) DEFAULT NULL,
  `data` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`shelxc_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4334 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shelxd_results`
--

DROP TABLE IF EXISTS `shelxd_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shelxd_results` (
  `shelxd_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `sad_result_id` mediumint(8) unsigned DEFAULT NULL,
  `best_occ` varchar(256) DEFAULT NULL,
  `trials` smallint(5) unsigned DEFAULT NULL,
  `cca` float DEFAULT NULL,
  `cca_max` float DEFAULT NULL,
  `cca_min` float DEFAULT NULL,
  `cca_mean` float DEFAULT NULL,
  `cca_stddev` float DEFAULT NULL,
  `ccw` float DEFAULT NULL,
  `ccw_max` float DEFAULT NULL,
  `ccw_min` float DEFAULT NULL,
  `ccw_mean` float DEFAULT NULL,
  `ccw_stddev` float DEFAULT NULL,
  `fom` float DEFAULT NULL,
  `fom_max` float DEFAULT NULL,
  `fom_min` float DEFAULT NULL,
  `fom_mean` float DEFAULT NULL,
  `fom_stddev` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`shelxd_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=5104 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shelxe_results`
--

DROP TABLE IF EXISTS `shelxe_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shelxe_results` (
  `shelxe_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `sad_result_id` mediumint(8) unsigned DEFAULT NULL,
  `solution` varchar(5) DEFAULT NULL,
  `resolution` varchar(256) DEFAULT NULL,
  `number_sites` smallint(5) unsigned DEFAULT NULL,
  `inverted` varchar(5) DEFAULT NULL,
  `cc_norm` float DEFAULT NULL,
  `cc_inv` float DEFAULT NULL,
  `contrast_norm` float DEFAULT NULL,
  `contrast_inv` float DEFAULT NULL,
  `connect_norm` float DEFAULT NULL,
  `connect_inv` float DEFAULT NULL,
  `mapcc_norm` float DEFAULT NULL,
  `mapcc_inv` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`shelxe_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=5188 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shelxe_sites`
--

DROP TABLE IF EXISTS `shelxe_sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shelxe_sites` (
  `shelxe_site_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `shelxe_result_id` mediumint(8) unsigned DEFAULT NULL,
  `sad_result_id` mediumint(8) unsigned DEFAULT NULL,
  `site_number` smallint(5) unsigned DEFAULT NULL,
  `x` float DEFAULT NULL,
  `y` float DEFAULT NULL,
  `z` float DEFAULT NULL,
  `occxz` float DEFAULT NULL,
  `density` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`shelxe_site_id`)
) ENGINE=MyISAM AUTO_INCREMENT=110710 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `single_results`
--

DROP TABLE IF EXISTS `single_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `single_results` (
  `single_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `data_root_dir` varchar(128) DEFAULT NULL,
  `settings_id` mediumint(8) unsigned DEFAULT NULL,
  `repr` varchar(128) DEFAULT NULL,
  `fullname` varchar(256) DEFAULT NULL,
  `image_id` int(10) unsigned DEFAULT NULL,
  `adsc_number` mediumint(8) unsigned DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `sample_id` mediumint(8) unsigned DEFAULT NULL,
  `work_dir` varchar(256) DEFAULT NULL,
  `type` varchar(12) DEFAULT NULL,
  `distl_status` varchar(8) DEFAULT NULL,
  `distl_res` float DEFAULT NULL,
  `distl_labelit_res` float DEFAULT NULL,
  `distl_ice_rings` smallint(5) unsigned DEFAULT NULL,
  `distl_total_spots` mediumint(8) unsigned DEFAULT NULL,
  `distl_spots_in_res` mediumint(8) unsigned DEFAULT NULL,
  `distl_good_bragg_spots` mediumint(8) unsigned DEFAULT NULL,
  `distl_overloads` mediumint(8) unsigned DEFAULT NULL,
  `distl_max_cell` float DEFAULT NULL,
  `distl_mean_int_signal` mediumint(8) unsigned DEFAULT NULL,
  `distl_min_signal_strength` mediumint(8) unsigned DEFAULT NULL,
  `distl_max_signal_strength` mediumint(8) unsigned DEFAULT NULL,
  `labelit_status` varchar(8) DEFAULT NULL,
  `labelit_iteration` tinyint(3) unsigned DEFAULT NULL,
  `labelit_res` float DEFAULT NULL,
  `labelit_spots_fit` mediumint(8) unsigned DEFAULT NULL,
  `labelit_metric` float DEFAULT NULL,
  `labelit_spacegroup` varchar(8) DEFAULT NULL,
  `labelit_distance` float DEFAULT NULL,
  `labelit_x_beam` float DEFAULT NULL,
  `labelit_y_beam` float DEFAULT NULL,
  `labelit_a` float DEFAULT NULL,
  `labelit_b` float DEFAULT NULL,
  `labelit_c` float DEFAULT NULL,
  `labelit_alpha` float DEFAULT NULL,
  `labelit_beta` float DEFAULT NULL,
  `labelit_gamma` float DEFAULT NULL,
  `labelit_mosaicity` float DEFAULT NULL,
  `labelit_rmsd` float DEFAULT NULL,
  `raddose_status` varchar(8) DEFAULT NULL,
  `raddose_dose_per_second` float DEFAULT NULL,
  `raddose_dose_per_image` float DEFAULT NULL,
  `raddose_adjusted_dose` float DEFAULT NULL,
  `raddose_henderson_limit` mediumint(8) unsigned DEFAULT NULL,
  `raddose_exp_dose_limit` mediumint(8) unsigned DEFAULT NULL,
  `best_complexity` varchar(8) DEFAULT NULL,
  `best_norm_status` varchar(8) DEFAULT NULL,
  `best_norm_res_limit` float DEFAULT NULL,
  `best_norm_completeness` float DEFAULT NULL,
  `best_norm_atten` float DEFAULT NULL,
  `best_norm_rot_range` float DEFAULT NULL,
  `best_norm_phi_end` float DEFAULT NULL,
  `best_norm_total_exp` float DEFAULT NULL,
  `best_norm_redundancy` float DEFAULT NULL,
  `best_norm_i_sigi_all` float DEFAULT NULL,
  `best_norm_i_sigi_high` float DEFAULT NULL,
  `best_norm_r_all` float DEFAULT NULL,
  `best_norm_r_high` float DEFAULT NULL,
  `best_norm_unique_in_blind` float DEFAULT NULL,
  `best_anom_status` varchar(8) DEFAULT NULL,
  `best_anom_res_limit` float DEFAULT NULL,
  `best_anom_completeness` float DEFAULT NULL,
  `best_anom_atten` float DEFAULT NULL,
  `best_anom_rot_range` float DEFAULT NULL,
  `best_anom_phi_end` float DEFAULT NULL,
  `best_anom_total_exp` float DEFAULT NULL,
  `best_anom_redundancy` float DEFAULT NULL,
  `best_anom_i_sigi_all` float DEFAULT NULL,
  `best_anom_i_sigi_high` float DEFAULT NULL,
  `best_anom_r_all` float DEFAULT NULL,
  `best_anom_r_high` float DEFAULT NULL,
  `best_anom_unique_in_blind` float DEFAULT NULL,
  `mosflm_norm_status` varchar(8) DEFAULT NULL,
  `mosflm_norm_res_limit` float DEFAULT NULL,
  `mosflm_norm_completeness` float DEFAULT NULL,
  `mosflm_norm_redundancy` float DEFAULT NULL,
  `mosflm_norm_distance` float DEFAULT NULL,
  `mosflm_norm_delta_phi` float DEFAULT NULL,
  `mosflm_norm_img_exposure_time` float DEFAULT NULL,
  `mosflm_anom_status` varchar(8) DEFAULT NULL,
  `mosflm_anom_res_limit` float DEFAULT NULL,
  `mosflm_anom_completeness` float DEFAULT NULL,
  `mosflm_anom_redundancy` float DEFAULT NULL,
  `mosflm_anom_distance` float DEFAULT NULL,
  `mosflm_anom_delta_phi` float DEFAULT NULL,
  `mosflm_anom_img_exposure_time` float DEFAULT NULL,
  `summary_short` varchar(128) DEFAULT NULL,
  `summary_long` varchar(128) DEFAULT NULL,
  `summary_stac` varchar(128) DEFAULT NULL,
  `image_small` varchar(128) DEFAULT NULL,
  `image_big` varchar(128) DEFAULT NULL,
  `image_raw` varchar(256) DEFAULT NULL,
  `image_preds` varchar(256) DEFAULT NULL,
  `best_plots` varchar(128) DEFAULT NULL,
  `best_plots_anom` varchar(128) DEFAULT NULL,
  `stac_file1` varchar(256) DEFAULT NULL,
  `stac_file2` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`single_result_id`),
  KEY `image_id` (`image_id`),
  KEY `result_id` (`result_id`),
  KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=668836 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stats_results`
--

DROP TABLE IF EXISTS `stats_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stats_results` (
  `stats_result_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` mediumint(8) unsigned DEFAULT NULL,
  `process_id` mediumint(8) unsigned DEFAULT NULL,
  `cell_sum` varchar(256) DEFAULT NULL,
  `xtriage_sum` varchar(256) DEFAULT NULL,
  `xtriage_plots` varchar(256) DEFAULT NULL,
  `molrep_sum` varchar(256) DEFAULT NULL,
  `molrep_img` varchar(256) DEFAULT NULL,
  `precession_sum` varchar(256) DEFAULT NULL,
  `precession_img0` varchar(256) DEFAULT NULL,
  `precession_img1` varchar(256) DEFAULT NULL,
  `precession_img2` varchar(256) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`stats_result_id`)
) ENGINE=MyISAM AUTO_INCREMENT=65817 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `status_cluster`
--

DROP TABLE IF EXISTS `status_cluster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status_cluster` (
  `ip_address` varchar(15) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `ip_address` (`ip_address`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `status_controller`
--

DROP TABLE IF EXISTS `status_controller`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status_controller` (
  `controller_ip` varchar(15) DEFAULT NULL,
  `data_root_dir` varchar(256) DEFAULT NULL,
  `beamline` varchar(15) DEFAULT NULL,
  `dataserver_ip` varchar(15) DEFAULT NULL,
  `cluster_ip` varchar(15) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `controller_ip` (`controller_ip`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `status_dataserver`
--

DROP TABLE IF EXISTS `status_dataserver`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status_dataserver` (
  `ip_address` varchar(15) DEFAULT NULL,
  `beamline` varchar(15) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `ip_address` (`ip_address`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `strategy_wedges`
--

DROP TABLE IF EXISTS `strategy_wedges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `strategy_wedges` (
  `strategy_wedge_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `id` mediumint(8) unsigned NOT NULL,
  `int_type` varchar(12) DEFAULT NULL,
  `strategy_type` varchar(12) DEFAULT NULL,
  `run_number` tinyint(3) unsigned DEFAULT NULL,
  `phi_start` float DEFAULT NULL,
  `number_images` smallint(5) unsigned DEFAULT NULL,
  `delta_phi` float DEFAULT NULL,
  `overlap` varchar(4) DEFAULT NULL,
  `distance` float DEFAULT NULL,
  `exposure_time` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`strategy_wedge_id`)
) ENGINE=MyISAM AUTO_INCREMENT=1031504 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `version`
--

DROP TABLE IF EXISTS `version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `version` (
  `version` mediumint(8) unsigned NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`version`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-01-21 15:06:40

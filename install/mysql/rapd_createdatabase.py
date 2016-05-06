"""
Creates new MySQL database for RAPD
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import sys

import pymysql

# RAPD imports
import utils.text as text

VERSION = "2.0"

class MakeDB(object):
    """
    Create and empty database to the current specifications.

    host - location of MySQL server
    user - user for MySQL server
    password
    verbose - True/False

    """
    def __init__(self,host,user,passwd,verbose=True):
        """
        Set up the class by saving variables
        """

        if verbose:
            print 'MakeDB::__init__'

        #passed-in variables
        self.host    = host
        self.user    = user
        self.passwd  = passwd
        self.verbose = verbose

    def CreateNewRapdData(self):
        """
        Create the database rapd_data
        """
        if self.verbose:
            print 'MakeDB::CreateNewRapdData'

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()

        #try to delete the database
        try:
            curs.execute('drop database rapd_data')
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Database rapd_data does not exist to delete'

        #try to make the database
        try:
            curs.execute('create database rapd_data')
        except _mysql_exceptions.ProgrammingError:
            if self.verbose:
                print 'Database rapd_data already exists'
        #switch to it
        curs.execute('use rapd_data')

        #
        # Database version
        #
        tblcmd = '''CREATE TABLE version (version     MEDIUMINT UNSIGNED NOT NULL,
                                          timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                          PRIMARY KEY (version))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table version already exists'

        tblcmd = 'INSERT INTO version (version) VALUES (3)'
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Having trouble setting version number of database'

        #
        # Settings
        #
        tblcmd = '''CREATE TABLE settings (setting_id        MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                           beamline          VARCHAR(16),
                                           data_root_dir     VARCHAR(256),
                                           multiprocesing    VARCHAR(5),
                                           spacegroup        VARCHAR(12),
                                           sample_type       VARCHAR(12),
                                           solvent_content   FLOAT,
                                           susceptibility    FLOAT,
                                           crystal_size_x    SMALLINT UNSIGNED,
                                           crystal_size_y    SMALLINT UNSIGNED,
                                           crystal_size_z    SMALLINT UNSIGNED,
                                           a                 FLOAT,
                                           b                 FLOAT,
                                           c                 FLOAT,
                                           alpha             FLOAT,
                                           beta              FLOAT,
                                           gamma             FLOAT,
                                           work_dir_override VARCHAR(5),
                                           work_directory    VARCHAR(256),
                                           beam_flip         VARCHAR(5),
                                           x_beam            VARCHAR(12),
                                           y_beam            VARCHAR(12),
                                           index_hi_res      FLOAT,
                                           strategy_type     VARCHAR(8),
                                           best_complexity   VARCHAR(4),
                                           mosflm_seg        TINYINT UNSIGNED,
                                           mosflm_rot        FLOAT,
                                           min_exposure_per  FLOAT,
                                           aimed_res         FLOAT,              #not used as of 11/24/09
                                           beam_size_x       VARCHAR(12),        #not used at NECAT as of 11/24/09
                                           beam_size_y       VARCHAR(12),        #not used at NECAT as of 11/24/09
                                           integrate         VARCHAR(5),
                                           reference_data_id MEDIUMINT UNSIGNED,
                                           setting_type      VARCHAR(8),
                                           timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                           PRIMARY KEY       (setting_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table settings already exists'


        #the table presets for storing settings BEFORE the first shot is taken
        tblcmd = '''CREATE TABLE presets ( presets_id           MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                           setting_id           MEDIUMINT UNSIGNED,
                                           beamline             VARCHAR(16),
                                           data_root_dir        VARCHAR(256),
                                           timestamp            TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                           PRIMARY KEY          (presets_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table presets already exists'


        #the table current for storing current beamline settings
        tblcmd = '''CREATE TABLE current ( beamline             VARCHAR(16),
                                           setting_id           MEDIUMINT UNSIGNED,
                                           data_root_dir        VARCHAR(256),
                                           puckset_id           MEDIUMINT UNSIGNED,
                                           timestamp            TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                           PRIMARY KEY          (beamline))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table current already exists'

        #
        # PUCK AND SAMPLE INFO
        #
        #construct a table for puck sets
        tblcmd =  '''CREATE TABLE puck_settings (puckset_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                 beamline      VARCHAR(16),
                                                 data_root_dir VARCHAR(256),
                                                 A             VARCHAR(48),
                                                 B             VARCHAR(48),
                                                 C             VARCHAR(48),
                                                 D             VARCHAR(48),
                                                 timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                 UNIQUE KEY    (puckset_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table puck_settings already exists'

        #construct a table for samples
        tblcmd =  '''CREATE TABLE samples(sample_id         MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                          sheetname         VARCHAR(48),
                                          PuckID            VARCHAR(48),
                                          sample            TINYINT UNSIGNED,
                                          CrystalID         VARCHAR(48),
                                          Protein           VARCHAR(48),
                                          ligand            VARCHAR(48),
                                          Comment           VARCHAR(128),
                                          FreezingCondition VARCHAR(128),
                                          CrystalCondition  VARCHAR(128),
                                          Metal             VARCHAR(8),
                                          project           VARCHAR(48),
                                          Person            VARCHAR(48),
                                          username          VARCHAR(48),
                                          timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                          UNIQUE KEY        (sample_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table samples already exists'

        #construct a table for projects
        tblcmd =  '''CREATE TABLE projects (project_id         MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                          project           VARCHAR(48),
                                          protein           VARCHAR(48),
                                          ligand            VARCHAR(48),
                                          project_type      VARCHAR(12),
                                          seq               VARCHAR(1000),
                                          mw                FLOAT,
                                          solvent           FLOAT,
                                          metal             VARCHAR(8),
                                          sites             TINYINT UNSIGNED,
                                          pdb               VARCHAR(8),
                                          username          VARCHAR(48),
                                          timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                          PRIMARY KEY       (project_id),
                                          UNIQUE KEY        (project))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table projects already exists'

        #
        # BEAMLINE TABLES
        #
        #construct a table for storing beamcenter values
        tblcmd = '''CREATE TABLE beamcenter (beamcenter_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                             beamline         VARCHAR(16),
                                             x_b              FLOAT,
                                             x_m1             FLOAT,
                                             x_m2             FLOAT,
                                             x_m3             FLOAT,
                                             x_m4             FLOAT,
                                             x_m5             FLOAT,
                                             x_m6             FLOAT,
                                             x_r              FLOAT,
                                             y_b              FLOAT,
                                             y_m1             FLOAT,
                                             y_m2             FLOAT,
                                             y_m3             FLOAT,
                                             y_m4             FLOAT,
                                             y_m5             FLOAT,
                                             y_m6             FLOAT,
                                             y_r              FLOAT,
                                             image_ids        VARCHAR(512),
                                             timestamp        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                             PRIMARY KEY      (beamcenter_id),
                                             INDEX            (timestamp)) ENGINE=InnoDB'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table beamcenter already exists'

        #
        # STATUS TABLES
        #
        #construct a new table for xf_status data
        tblcmd =  '''CREATE TABLE image_status (image_status_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                fullname         VARCHAR(256),
                                                directory        VARCHAR(256),
                                                image_prefix     VARCHAR(64),
                                                run_number       SMALLINT UNSIGNED,
                                                image_number     SMALLINT UNSIGNED,
                                                adsc_number      MEDIUMINT UNSIGNED,
                                                beamline         VARCHAR(16),
                                                timestamp        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                PRIMARY KEY      (image_status_id),
                                                UNIQUE KEY       blocker(fullname, adsc_number))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table image_status already exists'

        #create a table for images
        tblcmd =  '''CREATE TABLE images (image_id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
                                          fullname              VARCHAR(256),
                                          adsc_number           MEDIUMINT UNSIGNED,
                                          adc                   VARCHAR(5),
                                          axis                  VARCHAR(6),
                                          beam_center_x         FLOAT,
                                          beam_center_y         FLOAT,
                                          binning               VARCHAR(5),
                                          byte_order            VARCHAR(14),
                                          ccd_image_saturation  SMALLINT UNSIGNED,
                                          date                  DATETIME,
                                          detector_sn           SMALLINT,
                                          collect_mode          VARCHAR(8),
                                          dim                   TINYINT,
                                          distance              FLOAT,
                                          header_bytes          SMALLINT,
                                          osc_range             FLOAT,
                                          osc_start             FLOAT,
                                          phi                   FLOAT,
                                          pixel_size            FLOAT,
                                          size1                 SMALLINT UNSIGNED,
                                          size2                 SMALLINT UNSIGNED,
                                          time                  FLOAT,
                                          twotheta              FLOAT,
                                          type                  VARCHAR(15),
                                          unif_ped              SMALLINT,
                                          wavelength            FLOAT,
                                          directory             VARCHAR(256),
                                          image_prefix          VARCHAR(64),
                                          run_number            SMALLINT UNSIGNED,
                                          image_number          SMALLINT UNSIGNED,
                                          transmission          FLOAT,
                                          puck                  VARCHAR(1),
                                          sample                TINYINT UNSIGNED,
                                          sample_id             MEDIUMINT UNSIGNED,
                                          ring_current          FLOAT,
                                          ring_mode             VARCHAR(48),
                                          md2_aperture          TINYINT UNSIGNED,
                                          md2_prg_exp           FLOAT,
                                          md2_net_exp           MEDIUMINT UNSIGNED,
                                          acc_time              MEDIUMINT UNSIGNED,
                                          beamline              VARCHAR(16),
                                          calc_beam_center_x    FLOAT,
                                          calc_beam_center_y    FLOAT,
                                          flux                  FLOAT,
                                          beam_size_x           FLOAT,
                                          beam_size_y           FLOAT,
                                          gauss_x               FLOAT,
                                          gauss_y               FLOAT,
                                          run_id                MEDIUMINT UNSIGNED,
                                          timestamp             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                          PRIMARY KEY           (image_id),
                                          UNIQUE KEY            blocker(fullname, adsc_number, date))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table images already exists'

        #construct a new table for marcollect data
        tblcmd =  '''create table run_status ( run_status_id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                               adc           VARCHAR(5),
                                               anom_wedge    TINYINT UNSIGNED,
                                               anomalous     VARCHAR(4),
                                               beam_center   VARCHAR(20),
                                               binning       VARCHAR(5),
                                               comment       VARCHAR(256),
                                               compression   VARCHAR(4),
                                               directory     VARCHAR(256),
                                               image_prefix  VARCHAR(64),
                                               mad           VARCHAR(4),
                                               mode          VARCHAR(5),
                                               beamline      VARCHAR(16),
                                               timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                               PRIMARY KEY   (run_status_id),
                                               UNIQUE KEY    blocker (adc,
                                                                      anom_wedge,
                                                                      anomalous,
                                                                      beam_center,
                                                                      binning,
                                                                      comment,
                                                                      compression,
                                                                      directory,
                                                                      image_prefix,
                                                                      mad,
                                                                      mode) )'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table run_status already exists'


        #construct a new table for run data
        tblcmd =  '''create table runs (run_id        MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                        directory     VARCHAR(256),
                                        image_prefix  VARCHAR(64),
                                        run_number    SMALLINT UNSIGNED,
                                        start         SMALLINT UNSIGNED,
                                        total         SMALLINT UNSIGNED,
                                        distance      FLOAT,
                                        twotheta      FLOAT,
                                        phi           FLOAT,
                                        kappa         FLOAT,
                                        omega         FLOAT,
                                        axis          VARCHAR(6),
                                        width         FLOAT,
                                        time          FLOAT,
                                        de_zngr       VARCHAR(5),
                                        anomalous     VARCHAR(3),
                                        beamline      VARCHAR(16),
                                        timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                        PRIMARY KEY   (run_id),
                                        UNIQUE KEY     blocker (directory,
                                                                image_prefix,
                                                                run_number,
                                                                start))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table runs already exists'

        #
        # RESULTS TABLES
        #

        #create a table for orphan results
        tblcmd = '''CREATE TABLE orphan_results ( orphan_result_id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  type             VARCHAR(6),
                                                  data_root_dir    VARCHAR(256),
                                                  result_id        MEDIUMINT UNSIGNED,
                                                  date             DATETIME,
                                                  PRIMARY KEY      (orphan_result_id),
                                                  UNIQUE KEY       blocker(type,data_root_dir,result_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table orphan_results already exists'

        #create a table to hold runs currently being processed
        tblcmd = '''CREATE TABLE processes ( process_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                             type          VARCHAR(12),
                                             rtype         VARCHAR(12),
                                             repr          VARCHAR(128),
                                             data_root_dir VARCHAR(256),
                                             state         VARCHAR(12),
                                             display       VARCHAR(12) DEFAULT 'show',
                                             progress      TINYINT UNSIGNED DEFAULT 0,
                                             timestamp1    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                             timestamp2    TIMESTAMP,
                                             PRIMARY KEY   (process_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table processes already exists'

        #create a table to coordinate results
        tblcmd = '''CREATE TABLE results ( result_id     MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                           type          VARCHAR(12),
                                           id            MEDIUMINT UNSIGNED,
                                           setting_id    MEDIUMINT UNSIGNED,
                                           process_id    MEDIUMINT UNSIGNED,
                                           sample_id     MEDIUMINT UNSIGNED,
                                           data_root_dir VARCHAR(256),
                                           display       VARCHAR(12),
                                           timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                           PRIMARY KEY   (result_id),
                                           INDEX         (data_root_dir),
                                           INDEX         (timestamp))'''


        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table results already exists'

        #create a table for pair results
        tblcmd = '''CREATE TABLE pair_results ( pair_result_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                result_id         MEDIUMINT UNSIGNED,
                                                process_id        MEDIUMINT UNSIGNED,
                                                data_root_dir     VARCHAR(256),
                                                settings_id       MEDIUMINT UNSIGNED,
                                                repr              VARCHAR(128),
                                                fullname_1        VARCHAR(256),
                                                image1_id         INT UNSIGNED,
                                                adsc_number_1     MEDIUMINT UNSIGNED,
                                                date_1            DATETIME,
                                                fullname_2        VARCHAR(256),
                                                image2_id         INT UNSIGNED,
                                                adsc_number_2     MEDIUMINT UNSIGNED,
                                                date_2            DATETIME,
                                                sample_id         MEDIUMINT UNSIGNED,
                                                work_dir          VARCHAR(256),
                                                type              VARCHAR(12),

                                                distl_status                VARCHAR(8),
                                                distl_res_1                 FLOAT,
                                                distl_labelit_res_1         FLOAT,
                                                distl_ice_rings_1           SMALLINT UNSIGNED,
                                                distl_total_spots_1         MEDIUMINT UNSIGNED,
                                                distl_spots_in_res_1        MEDIUMINT UNSIGNED,
                                                distl_good_bragg_spots_1    MEDIUMINT UNSIGNED,
                                                distl_overloads_1           MEDIUMINT UNSIGNED,
                                                distl_max_cell_1            FLOAT,
                                                distl_mean_int_signal_1     MEDIUMINT UNSIGNED,
                                                distl_min_signal_strength_1 MEDIUMINT UNSIGNED,
                                                distl_max_signal_strength_1 MEDIUMINT UNSIGNED,
                                                distl_res_2                 FLOAT,
                                                distl_labelit_res_2         FLOAT,
                                                distl_ice_rings_2           SMALLINT UNSIGNED,
                                                distl_total_spots_2         MEDIUMINT UNSIGNED,
                                                distl_spots_in_res_2        MEDIUMINT UNSIGNED,
                                                distl_good_bragg_spots_2    MEDIUMINT UNSIGNED,
                                                distl_overloads_2           MEDIUMINT UNSIGNED,
                                                distl_max_cell_2            FLOAT,
                                                distl_mean_int_signal_2     MEDIUMINT UNSIGNED,
                                                distl_min_signal_strength_2 MEDIUMINT UNSIGNED,
                                                distl_max_signal_strength_2 MEDIUMINT UNSIGNED,

                                                labelit_status          VARCHAR(8),
                                                labelit_iteration       TINYINT UNSIGNED,
                                                labelit_res             FLOAT,
                                                labelit_spots_fit       MEDIUMINT UNSIGNED,
                                                labelit_metric          FLOAT,
                                                labelit_spacegroup      VARCHAR(8),
                                                labelit_distance        FLOAT,
                                                labelit_x_beam          FLOAT,
                                                labelit_y_beam          FLOAT,
                                                labelit_a               FLOAT,
                                                labelit_b               FLOAT,
                                                labelit_c               FLOAT,
                                                labelit_alpha           FLOAT,
                                                labelit_beta            FLOAT,
                                                labelit_gamma           FLOAT,
                                                labelit_mosaicity       FLOAT,
                                                labelit_rmsd            FLOAT,

                                                raddose_status          VARCHAR(8),
                                                raddose_dose_per_image  FLOAT,
                                                raddose_adjusted_dose   FLOAT,
                                                raddose_henderson_limit MEDIUMINT UNSIGNED,
                                                raddose_exp_dose_limit  MEDIUMINT UNSIGNED,

                                                best_complexity               VARCHAR(8),
                                                best_norm_status              FLOAT,
                                                best_norm_res_limit           FLOAT,
                                                best_norm_completeness        FLOAT,
                                                best_norm_atten               FLOAT,
                                                best_norm_rot_range           FLOAT,
                                                best_norm_phi_end             FLOAT,
                                                best_norm_total_exp           FLOAT,
                                                best_norm_redundancy          FLOAT,
                                                best_norm_i_sigi_all          FLOAT,
                                                best_norm_i_sigi_high         FLOAT,
                                                best_norm_r_all               FLOAT,
                                                best_norm_r_high              FLOAT,
                                                best_norm_unique_in_blind     FLOAT,

                                                best_anom_status              VARCHAR(8),
                                                best_anom_status              FLOAT,
                                                best_anom_res_limit           FLOAT,
                                                best_anom_completeness        FLOAT,
                                                best_anom_atten               FLOAT,
                                                best_anom_rot_range           FLOAT,
                                                best_anom_phi_end             FLOAT,
                                                best_anom_total_exp           FLOAT,
                                                best_anom_redundancy          FLOAT,
                                                best_anom_i_sigi_all          FLOAT,
                                                best_anom_i_sigi_high         FLOAT,
                                                best_anom_r_all               FLOAT,
                                                best_anom_r_high              FLOAT,
                                                best_anom_unique_in_blind     FLOAT,

                                                mosflm_norm_status            VARCHAR(8),
                                                mosflm_norm_res_limit         FLOAT,
                                                mosflm_norm_completeness      FLOAT,
                                                mosflm_norm_redundancy        FLOAT,
                                                mosflm_norm_distance          FLOAT,
                                                mosflm_norm_delta_phi         FLOAT,
                                                mosflm_norm_img_exposure_time FLOAT,

                                                mosflm_anom_status            VARCHAR(8),
                                                mosflm_anom_res_limit         FLOAT,
                                                mosflm_anom_completeness      FLOAT,
                                                mosflm_anom_redundancy        FLOAT,
                                                mosflm_anom_distance          FLOAT,
                                                mosflm_anom_delta_phi         FLOAT,
                                                mosflm_anom_img_exposure_time FLOAT,

                                                summary_short     VARCHAR(256),
                                                summary_long      VARCHAR(256),
                                                summary_stac      VARCHAR(256),

                                                image_raw_1       VARCHAR(256),
                                                image_preds_1     VARCHAR(256),
                                                image_raw_2       VARCHAR(256),
                                                image_preds_2     VARCHAR(256),

                                                best_plots        VARCHAR(256),
                                                best_plots_anom   VARCHAR(256),

                                                #files used for future runs of STAC
                                                stac_file1        VARCHAR(256),
                                                stac_file2        VARCHAR(256),

                                                timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                                                PRIMARY KEY       (pair_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table pair_results already exists'


        #create a table for run results
        tblcmd = '''CREATE TABLE integrate_results ( integrate_result_id     MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                     result_id               MEDIUMINT UNSIGNED,
                                                     process_id              MEDIUMINT UNSIGNED,
                                                     run_id                  MEDIUMINT UNSIGNED,
                                                     sample_id               MEDIUMINT UNSIGNED,
                                                     version                 SMALLINT UNSIGNED DEFAULT 0,
                                                     pipeline                VARCHAR(12),
                                                     data_root_dir           VARCHAR(256),
                                                     settings_id             MEDIUMINT UNSIGNED,
                                                     request_id              MEDIUMINT UNSIGNED,
                                                     sample_id               MEDIUMINT UNSIGNED,
                                                     repr                    VARCHAR(128),
                                                     template                VARCHAR(256),
                                                     date                    DATETIME,
                                                     work_dir                VARCHAR(256),
                                                     type                    VARCHAR(12),
                                                     images_dir              VARCHAR(256),
                                                     image_start             SMALLINT UNSIGNED,
                                                     image_end               SMALLINT UNSIGNED,
                                                     integrate_status        VARCHAR(12),
                                                     solved                  VARCHAR(8),
                                                     parsed                  VARCHAR(256),
                                                     summary_long            VARCHAR(256),
                                                     plots                   VARCHAR(256),
                                                     xia_log                 VARCHAR(256),
                                                     xds_log                 VARCHAR(256),
                                                     xscale_log              VARCHAR(256),
                                                     scala_log               VARCHAR(256),
                                                     unmerged_sca_file       VARCHAR(256),
                                                     sca_file                VARCHAR(256),
                                                     mtz_file                VARCHAR(256),
                                                     hkl_file                VARCHAR(256),
                                                     merge_file              VARCHAR(256),
                                                     download_file           VARCHAR(256),
                                                     wavelength              FLOAT,
                                                     spacegroup              VARCHAR(12),
                                                     a                       FLOAT,
                                                     b                       FLOAT,
                                                     c                       FLOAT,
                                                     alpha                   FLOAT,
                                                     beta                    FLOAT,
                                                     gamma                   FLOAT,
                                                     twinscore               FLOAT,
                                                     rd_analysis             FLOAT,
                                                     rd_conclusion           VARCHAR(16),
                                                     cc_anom                 FLOAT,
                                                     cc_cut_res              FLOAT,
                                                     cc_cut_val              FLOAT,
                                                     rcr_anom                FLOAT,
                                                     rcr_cut_res             FLOAT,
                                                     rcr_cut_val             FLOAT,
                                                     proc_time               TIME,
                                                     shell_overall           MEDIUMINT UNSIGNED,
                                                     shell_inner             MEDIUMINT UNSIGNED,
                                                     shell_outer             MEDIUMINT UNSIGNED,
                                                     timestamp               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                     PRIMARY KEY             (integrate_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table integrate_results already exists'


        #create a table for subresults for integrations
        tblcmd = ''' CREATE TABLE integrate_shell_results ( isr_id             MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                            shell_type         VARCHAR(8),
                                                            high_res           FLOAT,
                                                            low_res            FLOAT,
                                                            completeness       FLOAT,
                                                            multiplicity       FLOAT,
                                                            i_sigma            FLOAT,
                                                            r_merge            FLOAT,
                                                            r_meas             FLOAT,
                                                            r_meas_pm          FLOAT,
                                                            r_pim              FLOAT,
                                                            r_pim_pm           FLOAT,
                                                            wilson_b           FLOAT,
                                                            partial_bias       FLOAT,
                                                            anom_completeness  FLOAT,
                                                            anom_multiplicity  FLOAT,
                                                            anom_correlation   FLOAT,
                                                            anom_slope         FLOAT,
                                                            total_obs          INT UNSIGNED,
                                                            unique_obs         INT UNSIGNED,
                                                            timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                            PRIMARY KEY        (isr_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table integrate_shell_results already exists'


        #create a table for merging results
        tblcmd = '''CREATE TABLE merge_results ( merge_result_id         MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                 result_id               MEDIUMINT UNSIGNED,
                                                 process_id              MEDIUMINT UNSIGNED,
                                                 data_root_dir           VARCHAR(256),
                                                 settings_id             MEDIUMINT UNSIGNED,
                                                 request_id              MEDIUMINT UNSIGNED,
                                                 repr                    VARCHAR(128),
                                                 work_dir                VARCHAR(256),
                                                 set1                    MEDIUMINT UNSIGNED,
                                                 set2                    MEDIUMINT UNSIGNED,
                                                 merge_status            VARCHAR(12),
                                                 solved                  VARCHAR(8),
                                                 summary                 VARCHAR(256),
                                                 details                 VARCHAR(256),
                                                 plots                   VARCHAR(256),
                                                 merge_file              VARCHAR(256),
                                                 mtz_file                VARCHAR(256),
                                                 download_file           VARCHAR(256),
                                                 wavelength              FLOAT,
                                                 spacegroup              VARCHAR(12),
                                                 a                       FLOAT,
                                                 b                       FLOAT,
                                                 c                       FLOAT,
                                                 alpha                   FLOAT,
                                                 beta                    FLOAT,
                                                 gamma                   FLOAT,
                                                 shell_overall           MEDIUMINT UNSIGNED,
                                                 shell_inner             MEDIUMINT UNSIGNED,
                                                 shell_outer             MEDIUMINT UNSIGNED,
                                                 timestamp               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                 PRIMARY KEY             (merge_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table merge_results already exists'

        #create a table for shell results for merges
        tblcmd = ''' CREATE TABLE merge_shell_results ( msr_id             MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                        shell_type         VARCHAR(8),
                                                        high_res           FLOAT,
                                                        low_res            FLOAT,
                                                        completeness       FLOAT,
                                                        multiplicity       FLOAT,
                                                        i_sigma            FLOAT,
                                                        r_merge            FLOAT,
                                                        r_meas             FLOAT,
                                                        r_meas_pm          FLOAT,
                                                        r_pim              FLOAT,
                                                        r_pim_pm           FLOAT,
                                                        wilson_b           FLOAT,
                                                        partial_bias       FLOAT,
                                                        anom_completeness  FLOAT,
                                                        anom_multiplicity  FLOAT,
                                                        anom_correlation   FLOAT,
                                                        anom_slope         FLOAT,
                                                        total_obs          INT UNSIGNED,
                                                        unique_obs         INT UNSIGNED,
                                                        timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                        PRIMARY KEY        (msr_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table merge_shell_results already exists'



        #create a table for reference results to be used for including previous data in strategy calculations
        tblcmd = '''CREATE TABLE reference_data ( reference_data_id       MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  integrate_result_id_1   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_2   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_3   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_4   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_5   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_6   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_7   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_8   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_9   MEDIUMINT UNSIGNED,
                                                  integrate_result_id_10  MEDIUMINT UNSIGNED,
                                                  snap_result_id          MEDIUMINT UNSIGNED,
                                                  timestamp               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                  PRIMARY KEY             (reference_data_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table reference_data already exists'

        #create a table for single image results
        tblcmd = '''CREATE TABLE single_results ( single_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  result_id         MEDIUMINT UNSIGNED,
                                                  process_id        MEDIUMINT UNSIGNED,
                                                  data_root_dir     VARCHAR(256),
                                                  settings_id       MEDIUMINT UNSIGNED,
                                                  repr              VARCHAR(128),
                                                  fullname          VARCHAR(256),
                                                  image_id          INT UNSIGNED,
                                                  adsc_number       MEDIUMINT UNSIGNED,
                                                  date              DATETIME,
                                                  sample_id         MEDIUMINT UNSIGNED,
                                                  work_dir          VARCHAR(256),
                                                  type              VARCHAR(12),

                                                  distl_status              VARCHAR(8),
                                                  distl_res                 FLOAT,
                                                  distl_labelit_res         FLOAT,
                                                  distl_ice_rings           SMALLINT UNSIGNED,
                                                  distl_total_spots         MEDIUMINT UNSIGNED,
                                                  distl_spots_in_res        MEDIUMINT UNSIGNED,
                                                  distl_good_bragg_spots    MEDIUMINT UNSIGNED,
                                                  distl_overloads           MEDIUMINT UNSIGNED,
                                                  distl_max_cell            FLOAT,
                                                  distl_mean_int_signal     MEDIUMINT UNSIGNED,
                                                  distl_min_signal_strength MEDIUMINT UNSIGNED,
                                                  distl_max_signal_strength MEDIUMINT UNSIGNED,

                                                  labelit_status          VARCHAR(8),
                                                  labelit_iteration       TINYINT UNSIGNED,
                                                  labelit_res             FLOAT,
                                                  labelit_spots_fit       MEDIUMINT UNSIGNED,
                                                  labelit_metric          FLOAT,
                                                  labelit_spacegroup      VARCHAR(8),
                                                  labelit_distance        FLOAT,
                                                  labelit_x_beam          FLOAT,
                                                  labelit_y_beam          FLOAT,
                                                  labelit_a               FLOAT,
                                                  labelit_b               FLOAT,
                                                  labelit_c               FLOAT,
                                                  labelit_alpha           FLOAT,
                                                  labelit_beta            FLOAT,
                                                  labelit_gamma           FLOAT,
                                                  labelit_mosaicity       FLOAT,
                                                  labelit_rmsd            FLOAT,

                                                  raddose_status          VARCHAR(8),
                                                  raddose_dose_per_second FLOAT,
                                                  raddose_dose_per_image  FLOAT,
                                                  raddose_adjusted_dose   FLOAT,
                                                  raddose_henderson_limit MEDIUMINT UNSIGNED,
                                                  raddose_exp_dose_limit  MEDIUMINT UNSIGNED,

                                                  best_complexity               VARCHAR(8),
                                                  best_norm_status              FLOAT,
                                                  best_norm_res_limit           FLOAT,
                                                  best_norm_completeness        FLOAT,
                                                  best_norm_atten               FLOAT,
                                                  best_norm_rot_range           FLOAT,
                                                  best_norm_phi_end             FLOAT,
                                                  best_norm_total_exp           FLOAT,
                                                  best_norm_redundancy          FLOAT,
                                                  best_norm_i_sigi_all          FLOAT,
                                                  best_norm_i_sigi_high         FLOAT,
                                                  best_norm_r_all               FLOAT,
                                                  best_norm_r_high              FLOAT,
                                                  best_norm_unique_in_blind     FLOAT,

                                                  best_anom_status              VARCHAR(8),
                                                  best_anom_status              FLOAT,
                                                  best_anom_res_limit           FLOAT,
                                                  best_anom_completeness        FLOAT,
                                                  best_anom_atten               FLOAT,
                                                  best_anom_rot_range           FLOAT,
                                                  best_anom_phi_end             FLOAT,
                                                  best_anom_total_exp           FLOAT,
                                                  best_anom_redundancy          FLOAT,
                                                  best_anom_i_sigi_all          FLOAT,
                                                  best_anom_i_sigi_high         FLOAT,
                                                  best_anom_r_all               FLOAT,
                                                  best_anom_r_high              FLOAT,
                                                  best_anom_unique_in_blind     FLOAT,

                                                  mosflm_norm_status            VARCHAR(8),
                                                  mosflm_norm_res_limit         FLOAT,
                                                  mosflm_norm_completeness      FLOAT,
                                                  mosflm_norm_redundancy        FLOAT,
                                                  mosflm_norm_distance          FLOAT,
                                                  mosflm_norm_delta_phi         FLOAT,
                                                  mosflm_norm_img_exposure_time FLOAT,

                                                  mosflm_anom_status            VARCHAR(8),
                                                  mosflm_anom_res_limit         FLOAT,
                                                  mosflm_anom_completeness      FLOAT,
                                                  mosflm_anom_redundancy        FLOAT,
                                                  mosflm_anom_distance          FLOAT,
                                                  mosflm_anom_delta_phi         FLOAT,
                                                  mosflm_anom_img_exposure_time FLOAT,

                                                  summary_short     VARCHAR(256),
                                                  summary_long      VARCHAR(256),
                                                  summary_stac      VARCHAR(256),

                                                  image_raw         VARCHAR(256),
                                                  image_preds       VARCHAR(256),

                                                  best_plots        VARCHAR(256),
                                                  best_plots_anom   VARCHAR(256),

                                                  #files used for future runs of STAC
                                                  stac_file1        VARCHAR(256),
                                                  stac_file2        VARCHAR(256),

                                                  timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                                                  PRIMARY KEY       (single_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table single_results already exists'


        #Wedges of strategy
        tblcmd = '''CREATE TABLE strategy_wedges ( strategy_wedge_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                   id                 MEDIUMINT UNSIGNED NOT NULL,
                                                   int_type           VARCHAR(12),
                                                   strategy_type      VARCHAR(12),
                                                   run_number         TINYINT UNSIGNED,
                                                   phi_start          FLOAT,
                                                   number_images      SMALLINT UNSIGNED,
                                                   delta_phi          FLOAT,
                                                   overlap            VARCHAR(4),
                                                   distance           FLOAT,
                                                   exposure_time      FLOAT,
                                                   timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                   PRIMARY KEY        (strategy_wedge_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table strategy_wedges already exists'


        #Diffraction-based centering esults table
        tblcmd = '''CREATE TABLE diffcenter_results ( diffcenter_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                      result_id             MEDIUMINT UNSIGNED,
                                                      process_id            MEDIUMINT UNSIGNED,
                                                      settings_id           MEDIUMINT UNSIGNED,
                                                      image_id              INT UNSIGNED,
                                                      fullname              VARCHAR(256),
                                                      sample_id             MEDIUMINT UNSIGNED,
                                                      work_dir              VARCHAR(256),
                                                      ice_rings             FLOAT,
                                                      max_cell              FLOAT,
                                                      distl_res             FLOAT,
                                                      overloads             SMALLINT UNSIGNED,
                                                      labelit_res           FLOAT,
                                                      total_spots           SMALLINT UNSIGNED,
                                                      good_b_spots          SMALLINT UNSIGNED,
                                                      max_signal_str        FLOAT,
                                                      mean_int_signal       FLOAT,
                                                      min_signal_str        FLOAT,
                                                      total_signal          INT UNSIGNED,
                                                      in_res_spots          SMALLINT UNSIGNED,
                                                      saturation_50         FLOAT,
                                                      timestamp             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                      PRIMARY KEY           (diffcenter_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table diffcenter_results already exists'

        #Snap-based analysis results table
        tblcmd = '''CREATE TABLE quickanalysis_results ( quickanalysis_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                         result_id             MEDIUMINT UNSIGNED,
                                                         process_id            MEDIUMINT UNSIGNED,
                                                         settings_id           MEDIUMINT UNSIGNED,
                                                         image_id              INT UNSIGNED,
                                                         fullname              VARCHAR(256),
                                                         sample_id             MEDIUMINT UNSIGNED,
                                                         work_dir              VARCHAR(256),
                                                         ice_rings             FLOAT,
                                                         max_cell              FLOAT,
                                                         distl_res             FLOAT,
                                                         overloads             SMALLINT UNSIGNED,
                                                         labelit_res           FLOAT,
                                                         total_spots           SMALLINT UNSIGNED,
                                                         good_b_spots          SMALLINT UNSIGNED,
                                                         max_signal_str        FLOAT,
                                                         mean_int_signal       FLOAT,
                                                         min_signal_str        FLOAT,
                                                         total_signal          INT UNSIGNED,
                                                         in_res_spots          SMALLINT UNSIGNED,
                                                         saturation_50         FLOAT,
                                                         timestamp             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                         PRIMARY KEY           (quickanalysis_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table dquickanalysis_results already exists'

        #MR structure solution tables
        tblcmd = '''CREATE TABLE mr_results (  mr_result_id   MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                               result_id      MEDIUMINT UNSIGNED,
                                               process_id     MEDIUMINT UNSIGNED,
                                               settings_id    MEDIUMINT UNSIGNED,
                                               request_id     MEDIUMINT UNSIGNED,
                                               run_id         MEDIUMINT UNSIGNED,
                                               merge_id       MEDIUMINT UNSIGNED,
                                               source_data_id MEDIUMINT UNSIGNED,
                                               data_root_dir  VARCHAR(256),
                                               work_dir       VARCHAR(256),
                                               repr           VARCHAR(128),
                                               version        SMALLINT UNSIGNED DEFAULT 0,
                                               mr_status      VARCHAR(8),
                                               summary_html   VARCHAR(256),
                                               timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                               PRIMARY KEY    (mr_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table mr_results already exists'

        #AutoMR result table
        tblcmd = '''CREATE TABLE mr_trial_results (mr_trial_id       MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                   mr_result_id      MEDIUMINT UNSIGNED,
                                                   gain              FLOAT,
                                                   rfz               FLOAT,
                                                   tfz               FLOAT,
                                                   spacegroup        VARCHAR(12),
                                                   archive           VARCHAR(256),
                                                   PRIMARY KEY       (mr_trial_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table phaser_results already exists'

        #SAD structure solution tables
        tblcmd = '''CREATE TABLE sad_results ( sad_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                               result_id      MEDIUMINT UNSIGNED,
                                               process_id     MEDIUMINT UNSIGNED,
                                               settings_id    MEDIUMINT UNSIGNED,
                                               request_id     MEDIUMINT UNSIGNED,                            # == rapd_cloud.cloud_requests.cloud_request_id
                                               run_id         MEDIUMINT UNSIGNED,
                                               merge_id       MEDIUMINT UNSIGNED,
                                               source_data_id MEDIUMINT UNSIGNED,
                                               data_root_dir  VARCHAR(256),
                                               work_dir       VARCHAR(256),
                                               repr           VARCHAR(128),
                                               version        SMALLINT UNSIGNED DEFAULT 0,
                                               sad_status     VARCHAR(8),
                                               shelxc_result_id      MEDIUMINT UNSIGNED,
                                               shelxd_result_id      MEDIUMINT UNSIGNED,
                                               shelxe_result_id      MEDIUMINT UNSIGNED,
                                               autosol_result_id     MEDIUMINT UNSIGNED,
                                               shelx_html     VARCHAR(256),
                                               shelx_plots    VARCHAR(256),
                                               autosol_html   VARCHAR(256),
                                               autosol_pdb    VARCHAR(256),
                                               autosol_mtz    VARCHAR(256),
                                               download_file  VARCHAR(256),
                                               shelxd_ha_pdb  VARCHAR(256),
                                               shelxe_phs     VARCHAR(256),
                                               shelx_tar      VARCHAR(256),
                                               timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                               PRIMARY KEY    (sad_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table sad_results already exists'




        tblcmd = '''CREATE TABLE shelxc_results ( shelxc_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  sad_result_id     MEDIUMINT UNSIGNED,
                                                  resolutions       VARCHAR(256),
                                                  completeness      VARCHAR(256),
                                                  dsig              VARCHAR(256),
                                                  isig              VARCHAR(256),
                                                  data              VARCHAR(256),
                                                  timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                  PRIMARY KEY       (shelxc_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table shelxc_results already exists'

        tblcmd = '''CREATE TABLE shelxd_results ( shelxd_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  sad_result_id     MEDIUMINT UNSIGNED,
                                                  best_occ          VARCHAR(256),
                                                  trials            SMALLINT UNSIGNED,
                                                  cca               FLOAT,
                                                  cca_max           FLOAT,
                                                  cca_min           FLOAT,
                                                  cca_mean          FLOAT,
                                                  cca_stddev        FLOAT,
                                                  ccw               FLOAT,
                                                  ccw_max           FLOAT,
                                                  ccw_min           FLOAT,
                                                  ccw_mean          FLOAT,
                                                  ccw_stddev        FLOAT,
                                                  fom               FLOAT,
                                                  fom_max           FLOAT,
                                                  fom_min           FLOAT,
                                                  fom_mean          FLOAT,
                                                  fom_stddev        FLOAT,
                                                  timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                  PRIMARY KEY       (shelxd_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table shelxd_results already exists'

        tblcmd = '''CREATE TABLE shelxe_results ( shelxe_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  sad_result_id     MEDIUMINT UNSIGNED,
                                                  solution          VARCHAR(5),
                                                  resolution        VARCHAR(256),
                                                  number_sites      SMALLINT UNSIGNED,
                                                  inverted          VARCHAR(5),
                                                  cc_norm           FLOAT,
                                                  cc_inv            FLOAT,
                                                  contrast_norm     FLOAT,
                                                  contrast_inv      FLOAT,
                                                  connect_norm      FLOAT,
                                                  connect_inv       FLOAT,
                                                  mapcc_norm        FLOAT,
                                                  mapcc_inv         FLOAT,
                                                  timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                  PRIMARY KEY       (shelxe_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table shelxe_results already exists'

        tblcmd = '''CREATE TABLE shelxe_sites ( shelxe_site_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                shelxe_result_id  MEDIUMINT UNSIGNED,
                                                sad_result_id     MEDIUMINT UNSIGNED,
                                                site_number       SMALLINT UNSIGNED,
                                                x                 FLOAT,
                                                y                 FLOAT,
                                                z                 FLOAT,
                                                occxz             FLOAT,
                                                density           FLOAT,
                                                timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                PRIMARY KEY       (shelxe_site_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table shelxe_sites already exists'

        tblcmd = '''CREATE TABLE autosol_results ( autosol_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                   sad_result_id      MEDIUMINT UNSIGNED,
                                                   directory          VARCHAR(256),
                                                   spacegroup         VARCHAR(8),
                                                   wavelength         FLOAT,
                                                   ha_type            VARCHAR(2),
                                                   fprime             FLOAT,
                                                   f2prime            FLOAT,
                                                   sites_start        TINYINT UNSIGNED,
                                                   sites_refined      TINYINT UNSIGNED,
                                                   res_built          SMALLINT UNSIGNED,
                                                   side_built         SMALLINT UNSIGNED,
                                                   number_chains      TINYINT UNSIGNED,
                                                   model_map_cc       FLOAT,
                                                   fom                FLOAT,
                                                   den_mod_r          FLOAT,
                                                   bayes_cc           FLOAT,
                                                   r                  FLOAT,
                                                   rfree              FLOAT,
                                                   timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                   PRIMARY KEY        (autosol_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table autosol_results already exists'

        tblcmd = '''CREATE TABLE cell_analysis_results ( cell_analysis_result_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                         sad_result_id      MEDIUMINT UNSIGNED,
                                                         result_id          MEDIUMINT UNSIGNED,
                                                         pdb_id             VARCHAR(6),
                                                         name               VARCHAR(128),
                                                         automr_sg          VARCHAR(8),
                                                         automr_rfz         FLOAT,
                                                         automr_tfz         FLOAT,
                                                         automr_gain        FLOAT,
                                                         automr_tar         VARCHAR(256),
                                                         automr_adf         VARCHAR(256),
                                                         automr_peaks       VARCHAR(256),
                                                         timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                         PRIMARY KEY        (cell_analysis_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table cell_analysis_results already exists'

        #Table for dataset analysis results
        tblcmd = '''CREATE TABLE stats_results ( stats_result_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                 result_id          MEDIUMINT UNSIGNED,
                                                 process_id         MEDIUMINT UNSIGNED,
                                                 cell_sum           VARCHAR(256),
                                                 xtriage_sum        VARCHAR(256),
                                                 xtriage_plots      VARCHAR(256),
                                                 molrep_sum         VARCHAR(256),
                                                 molrep_img         VARCHAR(256),
                                                 precession_sum     VARCHAR(256),
                                                 precession_img0    VARCHAR(256),
                                                 precession_img1    VARCHAR(256),
                                                 precession_img2    VARCHAR(256),
                                                 timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                 PRIMARY KEY        (stats_result_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table cell_analysis_results already exists'


        #
        # Tables for Status
        #
        #create a table for dataserver status
        tblcmd = '''CREATE TABLE status_dataserver ( ip_address         VARCHAR(15),
                                                     beamline           VARCHAR(16),
                                                     timestamp          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                                     UNIQUE KEY         (ip_address) )'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table status_dataserver already exists'

        #create a table for controller status
        tblcmd = '''CREATE TABLE status_controller ( controller_ip      VARCHAR(15),
                                                     data_root_dir      VARCHAR(256),
                                                     beamline           VARCHAR(16),
                                                     dataserver_ip      VARCHAR(15),
                                                     cluster_ip         VARCHAR(15),
                                                     timestamp          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                                     UNIQUE KEY         (controller_ip) )'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table status_controller already exists'


        #create a table for cluster status
        tblcmd = '''CREATE TABLE status_cluster ( ip_address         VARCHAR(15),
                                                  timestamp          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                                  UNIQUE KEY         (ip_address) )'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table status_cluster already exists'

        #create a table for uploaded pdbs
        tblcmd = '''CREATE TABLE pdbs ( pdbs_id         MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                        pdb_file        VARCHAR(128),
                                        pdb_name        VARCHAR(128),
                                        pdb_description VARCHAR(256),
                                        username        VARCHAR(48),
                                        location        VARCHAR(256),
                                        timestamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                        UNIQUE KEY (pdbs_id) )'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table status_cluster already exists'


        #close the connection
        curs.close()
        conn.close()

    def CreateNewCloud(self):
        """
        Create the database rapd_cloud
        """
        if self.verbose:
            print 'MakeDB::CreateNewCloud'

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()

        #try to delete the database
        try:
            curs.execute('drop database rapd_cloud')
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Database rapd_cloud does not exist to delete'

        #try to make the database
        try:
            curs.execute('create database rapd_cloud')
        except _mysql_exceptions.ProgrammingError:
            if self.verbose:
                print 'Database rapd_cloud already exists'
        #switch to it
        curs.execute('use rapd_cloud')

        #
        # CLOUD TABLES
        #
        #logging the state of the cloud
        tblcmd = '''CREATE TABLE cloud_state ( everything                TINYINT UNSIGNED,
                                               processing                TINYINT UNSIGNED,
                                               download                  TINYINT UNSIGNED,
                                               remote_proccessing        TINYINT UNSIGNED,
                                               remote_download           TINYINT UNSIGNED,
                                               remote_concurrent_allowed SMALLINT UNSIGNED,
                                               current_queue             SMALLINT UNSIGNED,
                                               timestamp                 TIMESTAMP )'''


        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table cloud_state already exists'

        #create a table for cloud requests
        tblcmd = '''CREATE TABLE cloud_requests ( cloud_request_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  request_type        VARCHAR(12),
                                                  original_result_id  MEDIUMINT UNSIGNED,
                                                  original_type       VARCHAR(12),
                                                  original_id         MEDIUMINT UNSIGNED,
                                                  data_root_dir       VARCHAR(256),
                                                  new_setting_id      MEDIUMINT UNSIGNED,
                                                  additional_image    MEDIUMINT UNSIGNED,
                                                  mk3_phi             FLOAT,
                                                  mk3_kappa           FLOAT,
                                                  result_id           MEDIUMINT UNSIGNED,
                                                  input_sca           VARCHAR(256),
                                                  input_mtz           VARCHAR(256),
                                                  input_map           VARCHAR(256),
                                                  ha_type             VARCHAR(2),
                                                  ha_number           TINYINT UNSIGNED,
                                                  shelxd_try          MEDIUMINT UNSIGNED,
                                                  sad_res             FLOAT,
                                                  sequence            VARCHAR(10000),
                                                  pdbs_id             MEDIUMINT UNSIGNED,
                                                  nmol                TINYINT UNSIGNED,
                                                  frame_start         SMALLINT UNSIGNED,
                                                  frame_finish        SMALLINT UNSIGNED,
                                                  status              VARCHAR(12),
                                                  ip_address          VARCHAR(15) DEFAULT "0.0.0.0",
                                                  puckset_id          MEDIUMINT UNSIGNED,
                                                  option1             VARCHAR(12),
                                                  timestamp           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                                  PRIMARY KEY         (cloud_request_id))'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table cloud_requests already exists'


        #create a table for cloud processes
        tblcmd = '''CREATE TABLE cloud_current ( cloud_current_id   MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                 cloud_request_id   MEDIUMINT UNSIGNED,
                                                 timestamp          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                                 request_timestamp  TIMESTAMP,
                                                 PRIMARY KEY        (cloud_current_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table cloud_current already exists'

        #create a table for cloud results
        tblcmd = '''CREATE TABLE cloud_complete ( cloud_complete_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  cloud_request_id   MEDIUMINT UNSIGNED,
                                                  timestamp          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                                  request_timestamp  TIMESTAMP,
                                                  start_timestamp    TIMESTAMP,
                                                  result_id          MEDIUMINT UNSIGNED,
                                                  request_type       VARCHAR(12),
                                                  status             VARCHAR(12),
                                                  ip_address         VARCHAR(15),
                                                  data_root_dir      VARCHAR(256),
                                                  archive            VARCHAR(96),
                                                  PRIMARY KEY        (cloud_complete_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table cloud_complete already exists'

        #create a table for minikappa requests
        tblcmd = '''CREATE TABLE minikappa ( minikappa_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                             omega         FLOAT,
                                             kappa         FLOAT,
                                             phi           FLOAT,
                                             beamline      VARCHAR(16),
                                             ip_address    VARCHAR(15),
                                             status        VARCHAR(12),
                                             timestamp     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                             PRIMARY KEY   (minikappa_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table minikappa already exists'

        #create a table for data collection requests
        tblcmd = '''CREATE TABLE datacollection ( datacollection_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                  group_id           MEDIUMINT UNSIGNED,
                                                  prefix             VARCHAR(64),
                                                  run_number         TINYINT UNSIGNED,
                                                  image_start        SMALLINT UNSIGNED,
                                                  omega_start        FLOAT,
                                                  delta_omega        FLOAT,
                                                  number_images      SMALLINT UNSIGNED,
                                                  time               FLOAT,
                                                  distance           FLOAT,
                                                  transmission       FLOAT,
                                                  kappa              FLOAT,
                                                  phi                FLOAT,
                                                  beamline           VARCHAR(16),
                                                  ip_address         VARCHAR(15),
                                                  status             VARCHAR(12),
                                                  timestamp          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                                  PRIMARY KEY        (datacollection_id))'''

        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table minikappa already exists'


    def CreateNewRapdUsers(self):
        """
        Create the database rapd_users
        """
        if self.verbose:
            print 'MakeDB::CreateNewRapdUsers'

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()

        #try to delete the database
        try:
            curs.execute('drop database rapd_users')
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Database rapd_users does not exist to delete'

        #try to make the database
        try:
            curs.execute('create database rapd_users')
        except _mysql_exceptions.ProgrammingError:
            if self.verbose:
                print 'Database rapd_users already exists'
        #switch to it
        curs.execute('use rapd_users')

        #authorize table
        tblcmd = '''CREATE TABLE IF NOT EXISTS authorize ( firstname    VARCHAR(20),
                                                           lastname     VARCHAR(20),
                                                           username     VARCHAR(48),
                                                           password     VARCHAR(50),
                                                           group1       VARCHAR(20),
                                                           group2       VARCHAR(20),
                                                           group3       VARCHAR(20),
                                                           pchange      VARCHAR(1),
                                                           email        VARCHAR(100),
                                                           redirect     VARCHAR(100),
                                                           verified     VARCHAR(1),
                                                           last_login    DATE ) '''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table authorize already exists'

        #log_login table
        tblcmd = '''CREATE TABLE IF NOT EXISTS log_login ( username    VARCHAR(20),
                                                           date        VARCHAR(20),
                                                           time        VARCHAR(20),
                                                           ip_addr     VARCHAR(20),
                                                           oper_sys    VARCHAR(20),
                                                           brow        VARCHAR(20) ) '''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table log_login already exists'

        #banned table
        tblcmd = '''CREATE TABLE IF NOT EXISTS banned ( no_access    VARCHAR(30),
                                                        type        VARCHAR(10) ) '''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table banned already exists'

        #trash table
        tblcmd = '''CREATE TABLE IF NOT EXISTS trash ( firstname    VARCHAR(20),
                                                       lastname     VARCHAR(20),
                                                       username     VARCHAR(48),
                                                       password     VARCHAR(50),
                                                       group1       VARCHAR(20),
                                                       group2       VARCHAR(20),
                                                       group3       VARCHAR(20),
                                                       pchange      VARCHAR(1),
                                                       email        VARCHAR(100),
                                                       redirect     VARCHAR(100),
                                                       verified     VARCHAR(1),
                                                       last_login   DATE,
                                                       del_date     DATE  ) '''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table trash already exists'


        #trips table
        tblcmd = '''CREATE TABLE IF NOT EXISTS trips ( trip_id        MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                       username       VARCHAR(48),
                                                       trip_start     DATETIME,
                                                       trip_finish    DATETIME,
                                                       data_root_dir  VARCHAR(256),
                                                       beamline       VARCHAR(16),
                                                       timestamp      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                                       PRIMARY KEY    (trip_id) ) '''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table trips already exists'

        #authorized_clients table
        tblcmd = '''CREATE TABLE IF NOT EXISTS authorized_clients ( client_ip      VARCHAR(15),
                                                                    client_name    VARCHAR(128),
                                                                    beamline       VARCHAR(16),
                                                                    timestamp      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                                                    UNIQUE KEY     (client_ip) )'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table authorized_clients already exists'

        #candidate_dirs table for adding directories
        tblcmd = '''CREATE TABLE IF NOT EXISTS candidate_dirs ( dir_id      MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                                dirname     VARCHAR(256),
                                                                beamline    VARCHAR(16),
                                                                timestamp   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                                                UNIQUE KEY  (dir_id) )'''
        try:
            curs.execute(tblcmd)
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Table candidate_dirs already exists'
        #close the connection
        curs.close()

    def CreateAdministrator(self):
        """
        Create the administrator for the site
        """
        if self.verbose:
            print 'MakeDB::CreateAdministrator'

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()

        #try to delete the database
        try:
            curs.execute('use rapd_users')
            curs.execute('INSERT INTO authorize (username,password,group1,group2,pchange,redirect) VALUES ("administrator",PASSWORD("administrator"),"Users","Administrators",1,"./admin/adminpage.php")')
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Error in creating administrator'

def get_host_info():
    """
    Query the user for host and database information
    """

    # Get the host name
    msg1 = text.green+"Input host of MySQL database: "+text.stop
    select1 = raw_input(msg1).strip()
    if select1:
        hostname = str(select1)
        if len(hostname) == 0:
            print text.error+"Error - you have not input a host"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a host"+text.stop
        sys.exit(9)
    print "                              %s" % hostname

    # Get the port
    msg4 = text.green+"Input port of MySQL database (3306 is standard): "+text.stop
    select4 = raw_input(msg4).strip()
    if select4:
        port = int(select4)
        if port == 0:
            print text.error+"Error - you have not input a port"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a port"+text.stop
        sys.exit(9)
    print "                                                 %d" % port

    # Get the user name
    msg2 = text.green+"Input user name: "+text.stop
    select2 = raw_input(msg2).strip()
    if select2:
        username = str(select2)
        if len(username) == 0:
            print text.error+"Error - you have not input a username"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a username"+text.stop
        sys.exit(9)
    print "                 %s" % username

    # Get the password
    msg3 = text.green+"Input password: "+text.stop
    #select3 = getpass.getpass(msg3).strip()
    select3 = raw_input(msg3).strip()
    if select3:
        password =  str(select3)
        if len(password) == 0:
            print text.error+"Error - you have not input a password"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a password"+text.stop
        sys.exit(9)
    print "                %s" % password

    return hostname, port, username, password

def perform_mysql_command(hostname, port, username, password, db, command):
    """
    Run a MySQL command_back

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    db -- the database to run on
    command -- compatible MySQL command
    """
    print "perform_mysql_command"
    print command

    connection = pymysql.connect(host=hostname,
                                 port=port,
                                 db=db,
                                 user=username,
                                 passwd=password)

    cursor = connection.cursor()

    cursor.execute(command)
    connection.commit()

    # cursor.close()
    # connection.close()

    return True

def check_database_connection(hostname, port, username, password):
    """
    Attempts to connect to the database using the input parameters

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    try:
        connection = pymysql.connect(host=hostname,
                                     port=port,
                                     user=username,
                                     passwd=password)

        print text.green+"Able to connect to MySQL database"+text.stop

    except pymysql.err.OperationalError as e:
        error_number, error_message = e
        # print error_number, error_message

        if error_number == 2003:

            # Server is not reachable
            if "Errno 8" in error_message:
                print text.error+"Error - cannot find the server %s" % hostname
                print "The raw error: %s" % error_message + text.stop
                sys.exit(9)

            # Server exists, but cannot connect
            elif "Errno 61" in error_message:
                print text.error+"Error - cannot connect to database on host:%s port:%d" % (hostname, port)
                print "The raw error: %s" % error_message + text.stop
                sys.exit(9)

            # Unknown
            else:
                print text.error+"Unknown error connecting to the database"
                print "The raw error: %s" % error_message + text.stop
                sys.exit(9)

        # Permission problems
        elif error_number == 1045:
            print text.error+"Error - problem connecting to the database with username:%s password:%s" % (username, password)
            print "The raw error: %s" % error_message + text.stop
            sys.exit(9)

        # Unknown
        else:
            print text.error+"Unknown error"
            print "The raw error:%d %s" % (error_number, error_message+text.stop)
            sys.exit(9)

    return True

def check_database_version(hostname, port, username, password):
    """
    Find the status of the RAPD MySQL database.
    Returns 0 for no database present or a version number found.

    The NE-CAT RAPD v1.x database is version 4.
    The database version should match the RAPD version from here on, so the
    version currently under development is 2.0

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    try:
        connection = pymysql.connect(host=hostname,
                                     port=port,
                                     db="rapd",
                                     user=username,
                                     passwd=password)

        cursor = connection.cursor()

    # No table
    except pymysql.err.InternalError as e:
        error_number, error_message = e
        # print error_number, error_message

        if error_number == 1049:
            print text.blue+"Looks like a new installation of RAPD database"+text.stop
            return 0

    # Get the RAPD database version number
    try:
        cursor.execute("SELECT * FROM version")
        for row in cursor.fetchall():
            version, timestamp = row
            return version
    except pymysql.err.ProgrammingError as e: #(1049, u"Unknown database 'rapd'")
        error_number, error_message = e
        if error_number == 1146:
            print text.blue+"Looks like a new installation of RAPD database"+text.stop
            return 0

def create_db(hostname, port, username, password, db, drop=False):
    """
    Generic method for db creation

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    db -- name of the db to be created
    drop -- drop the table first?
    """

    connection = pymysql.connect(host=hostname,
                                 port=port,
                                 user=username,
                                 passwd=password)

    cursor = connection.cursor()

    # Try to delete the database - used in testing
    if drop == True:
        try:
            cursor.execute("drop database %s" % db)
            connection.commit()
            print text.green+"Database %s dropped" % db + text.stop
        except:
            print "Database %s does not exist to delete" % db

    # Create the database
    # try:
    cursor.execute("CREATE DATABASE %s" % db)
    connection.commit()
    # except _mysql_exceptions.ProgrammingError:
    #     if self.verbose:
    #         print 'Database rapd_data already exists'

    print text.green+"Database %s created" % db + text.stop

def create_table(hostname,
                 port,
                 username,
                 password,
                 db,
                 table,
                 table_definition,
                 drop=False):
    """
    Generic method for db creation

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    db -- db to put table in
    table -- name of the table to be created
    table_definition -- table definition string
    drop -- drop the table first?
    """

    connection = pymysql.connect(host=hostname,
                                 port=port,
                                 db=db,
                                 user=username,
                                 passwd=password)

    cursor = connection.cursor()

    # Try to delete the database - used in testing
    if drop == True:
        try:
            cursor.execute("drop table %s" % table)
            connection.commit()
            print text.green+"Table %s dropped" % table + text.stop
        except pymysql.err.InternalError as e:
            error_number, error_message = e
            if error_number == 1051:
                print text.blue+"Table %s does not exist to drop." % table +text.stop

    # Create the database
    # try:
    cursor.execute("CREATE TABLE %s (%s)" % (table, table_definition))
    connection.commit()
    # except _mysql_exceptions.ProgrammingError:
    #     if self.verbose:
    #         print 'Database rapd_data already exists'

    print text.green+"Table %s created" % table + text.stop

def create_version_table(hostname, port, username, password):
    """
    Create the version table

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    # Create the version table
    version_table_string = """version VARCHAR(16) NOT NULL,
                              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                              PRIMARY KEY (version)"""
    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 db="rapd",
                 table="version",
                 table_definition=version_table_string,
                 drop=False)

    # Inerst version into the table
    version_insert_string = "INSERT INTO version (version) VALUES (%s)" % VERSION
    perform_mysql_command(hostname=hostname,
                          port=port,
                          username=username,
                          password=password,
                          db="rapd",
                          command=version_insert_string)
    print "Version set to %s" % VERSION

def create_data_tables(hostname, port, username, password):
    """
    Create the "data" tables

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    # Create the version table
    runs_table_string = """CREATE TABLE runs (
        run_id mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        directory varchar(128) DEFAULT NULL,
        image_prefix varchar(64) DEFAULT NULL,
        run_number smallint(5) unsigned DEFAULT NULL,
        start_image_number mediumint(8) unsigned DEFAULT NULL,
        number_images mediumint(8) unsigned DEFAULT NULL,
        distance float DEFAULT NULL,
        phi float DEFAULT NULL,
        kappa float DEFAULT NULL,
        omega float DEFAULT NULL,
        osc_axis varchar(6) DEFAULT NULL,
        osc_start float DEFAULT NULL,
        osc_width float DEFAULT NULL,
        time float DEFAULT NULL,
        transmission float DEFAULT NULL,
        energy float DEFAULT NULL,
        anomalous varchar(6) DEFAULT NULL,
        site_tag varchar(16) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id))"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 db="rapd",
                 table="runs",
                 table_definition=run_table_string,
                 drop=False)

    return True

def perform_naive_install(hostname, port, username, password):
    """
    Orchestrate the installation of v2.0 of the RAPD MySQL database

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    print text.blue+"Performing installation of RAPD database version %s" % VERSION + text.stop

    # Create the rapd database
    create_db(hostname=hostname,
              port=port,
              username=username,
              password=password,
              db="rapd",
              drop=True)

    # Create the version table
    create_version_table(hostname=hostname,
                         port=port,
                         username=username,
                         password=password)

    # Create "data" tables
    create_data_tables(hostname=hostname,
                       port=port,
                       username=username,
                       password=password)


def main():
    """
    Orchestrate command-line running
    """

    print "\nrapd_createdatabase.py v%s" % VERSION
    print "==========================="

    # Get the host information
    #hostname, port, username, password = get_host_info()

    hostname = "rapd"
    port = 3306
    username = "rapd1"
    password = "necatm)nster!"

    # Check that the db is accessible
    check_database_connection(hostname, port, username, password)

    # Check the current state of the database
    database_version = check_database_version(hostname, port, username, password)

    # Perform install
    if database_version in (0, None):
        perform_naive_install(hostname, port, username, password)

    # Version is current
    elif database_version == VERSION:
        print text.green+"RAPD database version %s is current." % database_version + text.stop
        # For Development
        perform_naive_install(hostname, port, username, password)

    # Version is not understood
    else:
        print text.error+"RAPD database version %s is NOT understood." % database_version + text.stop

if __name__ == '__main__':

    main()

    sys.exit()








    tmp = MakeDB(host=my_hostname,user=my_username,passwd=my_password,verbose=True)
    tmp.CreateNewRapdData()
    tmp.CreateNewCloud()
    tmp.CreateNewRapdUsers()

    msg4 = '\nCreate an administrator account [y/n]?'
    select4 = raw_input(msg4).strip()
    if select4:
        try:
            select4 = select4[0].lower()
            if select4 == 'y':
                print 'Creating administrator user. Password will be administrator'
                tmp.CreateAdministrator()
            else:
                print 'Bye.'
        except:
            print 'Error creating administrator.'

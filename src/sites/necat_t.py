"""
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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

__created__ = "2016-01-28"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import sys
import importlib

# RAPD imports
from utils.site import read_secrets

# Site ID - limited to 12 characters by MySQL
ID = "NECAT_T"
#ID = ("T")
BEAMLINE="T"

# The secrets file - do not put in github repo!
SECRETS = "sites.secrets_necat_t"
# Copy the secrets attribute to the local scope
# Do not remove unless you know what you are doing!
read_secrets(SECRETS, sys.modules[__name__])

# X-ray source characteristics
# Flux of the beam
"""
BEAM_FLUX = 1.5E12
# Size of the beam in microns
BEAM_SIZE_X = 50
BEAM_SIZE_Y = 20
# Shape of the beam - ellipse, rectangle
BEAM_SHAPE = "ellipse"
# Shape of the attenuated beam - circle or rectangle
BEAM_APERTURE_SHAPE = "circle"
# Gaussian description of the beam for raddose
BEAM_GAUSS_X = 0.03
BEAM_GAUSS_Y = 0.01
# Beam center calibration
BEAM_CENTER_DATE = "2017-3-02"
# Beamcenter equation coefficients (b, m1, m2, m3, m4, m5, m6)
# Beamcenter equation coefficients (b, m1, m2, m3)
BEAM_CENTER_X = (163.2757684023,
                 0.0003178917,
                 -5.0236657815e-06,
                 5.8164218288e-09)
BEAM_CENTER_Y = (155.1904879862,
                 -0.0014631216,
                 8.60559283424e-07,
                 -2.5709929645e-10)
"""
# Keyed to ID
BEAM_INFO = {
    "NECAT_T": {# Flux of the beam
          "BEAM_FLUX":1.5E12,
          # Size of the beam in microns
          "BEAM_SIZE_X":50,
          "BEAM_SIZE_Y":20,
          # Shape of the beam - ellipse, rectangle
          "BEAM_SHAPE":"ellipse",
          # Shape of the attenuated beam - circle or rectangle
          "BEAM_APERTURE_SHAPE":"circle",
          # Gaussian description of the beam for raddose
          "BEAM_GAUSS_X":0.03,
          "BEAM_GAUSS_Y":0.01,
          # Beam center calibration
          'BEAM_CENTER_DATE' : "2017-3-02",
          # Beamcenter equation coefficients (b, m1, m2, m3, m4, m5, m6)
          # Beamcenter equation coefficients (b, m1, m2, m3)
          'BEAM_CENTER_X' : (163.2757684023,
                           0.0003178917,
                           -5.0236657815e-06,
                           5.8164218288e-09),
          'BEAM_CENTER_Y' : (155.1904879862,
                           -0.0014631216,
                           8.60559283424e-07,
                           -2.5709929645e-10)
          }
             }
          
# Method RAPD uses to track groups
#   uid -- the uid of data root directory corresponds to session.group_id
#GROUP_ID = "uid"
GROUP_ID = None

# Logging
# Linux should be /var/log/
#LOGFILE_DIR = "/tmp/rapd2/logs"
LOGFILE_DIR = "/share/apps/necat/tmp3"
LOG_LEVEL = 50

# Where files from UI are uploaded - should be visible by launch instance
UPLOAD_DIR = "/gpfs5/users/necat/rapd/uranium/trunk/uploads"

# RAPD cluster process settings
# Port for cluster to listen on
#LAUNCHER_PORT = 50000
# Aggregator - be careful when changing
#LAUNCHER_ADDRESS = (LAUNCHER_HOST, LAUNCHER_PORT)

# Launcher settings
LAUNCHER_LOCK_FILE = "/tmp/rapd2/lock/launcher.lock"
# Launcher to send jobs to
# The value should be the key of the launcher to select in LAUNCHER_SPECIFICATIONS
LAUNCHER_TARGET = 1
# Directories to look for launcher adapters
RAPD_LAUNCHER_ADAPTER_DIRECTORIES = ("launch.launcher_adapters",
                                     "sites.launcher_adapters")
# Queried in order, so a shell_simple.py in src/sites/launcher_adapters will override
# the same file in launch/launcher_adapters

# Data gatherer settings
# The data gatherer for this site, in the src/sites/gatherers directory
GATHERER = "necat.py"
GATHERER_LOCK_FILE = "/tmp/rapd2/lock/gatherer.lock"

# Directories to look for rapd agents
RAPD_PLUGIN_DIRECTORIES = ("sites.agents",
                          "agents")
# Queried in order, so a rapd_agent_echo.py in src/sites/agents will override
# the same file in src/agents

# Control process settings
# Process is a singleton? The file to lock to. False if no locking.
CONTROL_LOCK_FILE = "/tmp/rapd2/lock/rapd_core.lock"

# Control settings
# Port for core process to listen on
#CORE_PORT = 50001
CONTROL_PORT = 50001

# Database to use for control operations. Options: "mysql"
#CONTROL_DATABASE = "mysql"
CONTROL_DATABASE = "mongodb"

#CONTROL_DATABASE_DATA = "rapd_data"
#CONTROL_DATABASE_USERS = "rapd_users"
#CONTROL_DATABASE_CLOUD = "rapd_cloud"
#DB_NAME_DATA = "rapd_data"
#DB_NAME_USERS = "rapd_users"
#DB_NAME_CLOUD = "rapd_cloud"
# Redis databse
# Running in a cluster configuration - True || False
#CONTROL_REDIS_CLUSTER = False
#CONTROL_REDIS_CLUSTER = True
REDIS_CLUSTER = True

# Detector settings
# Must have a file in sites.detectors that is all lowercase of this string
#DETECTOR = "NECAT_ADSC_Q315_TEST"
DETECTOR = "NECAT_DECTRIS_EIGER16M"
#DETECTOR_SUFFIX = ".img"
DETECTOR_SUFFIX = ".cbf"

# Monitor for collected images
#IMAGE_MONITOR = "sites.image_monitors.necat_e"
IMAGE_MONITOR = "sites.monitors.image_monitors.necat_e"


# Redis databse
# Running in a cluster configuration - True || False
IMAGE_MONITOR_REDIS_CLUSTER = REDIS_CLUSTER
# Images collected into following directories will be ignored
#IMAGE_IGNORE_DIRECTORIES = ()
#IMAGE_SHORT_CIRCUIT_DIRECTORIES = [
IMAGE_IGNORE_DIRECTORIES = (
    "/gpfs5/users/necat/phii_dfa_1/in",
    "/gpfs5/users/necat/phii_dfa_2/in",
    "/gpfs5/users/necat/phii_raster_snap/in",
    "/gpfs5/users/necat/phii_rastersnap_scan_data",
    "/gpfs5/users/necat/phii_dfa_scan_data",
    "/gpfs5/users/necat/phii_ova_scan_data",
    "/epu/rdma/gpfs5/users/necat/rapd/uranium/trunk/test_data",
    "/epu/rdma/gpfs5/users/necat/phii_dfa_1/in",
    "/epu/rdma/gpfs5/users/necat/phii_dfa_2/in",
    "/epu/rdma/gpfs5/users/necat/phii_raster_snap/in",
    "/epu/rdma/gpfs5/users/necat/phii_rastersnap_scan_data",
    "/epu/rdma/gpfs5/users/necat/phii_dfa_scan_data",
    "/epu/rdma/gpfs5/users/necat/phii_ova_scan_data",
    "/epu/rdma/gpfs5/users/necat/rapd/uranium/trunk/test_data",
    )
# Images collected containing the following string will be ignored
IMAGE_IGNORE_STRINGS = ("ignore", )

# So if image is not present, look in long term storage location.
ALT_IMAGE_LOCATIONS = True

# Monitor for collected run information
RUN_MONITOR = "sites.monitors.run_monitors.necat_e"
# Running in a cluster configuration - True || False
RUN_MONITOR_REDIS_CLUSTER = REDIS_CLUSTER
# Expected time limit for a run to be collected in minutes (0 = forever)
RUN_WINDOW = 60

# Cloud Settings
# The cloud monitor module
CLOUD_MONITOR = "cloud.rapd_cloud"
# Pause between checking the database for new cloud requests in seconds
CLOUD_INTERVAL = 10
# Directories to look for cloud handlers
CLOUD_HANDLER_DIRECTORIES = ("cloud.handlers", )
# Cloud handlers
CLOUD_MINIKAPPA = False
CLOUD_MINIKAPPA_HANDLER = None
CLOUD_DATA_COLLECTION_PARAMS = False
CLOUD_DATA_COLLECTION_PARAMS_HANDLER = "datacollectionparameters"
CLOUD_DOWNLOAD_HANDLER = "download"
CLOUD_BINARY_MERGE_HANDLER = "binary_merge"
CLOUD_MR_HANDLER = "mr"
CLOUD_REINDEX_HANDLER = "reindex"
CLOUD_REINTEGRATE_HANDLER = "reintegrate"

# For connecting to the site
SITE_ADAPTER = "sites.site_adapters.necat"
# Running in a cluster configuration - True || False
#SITE_ADAPTER_REDIS_CLUSTER = False
SITE_ADAPTER_REDIS_CLUSTER = REDIS_CLUSTER

# For connecting to the remote access system fr the site
REMOTE_ADAPTER = "sites.site_adapters.necat_remote"     # file name prefix for adapter in src/
REMOTE_ADAPTER_REDIS_CLUSTER = REDIS_CLUSTER

##
## Aggregators
## Be extra careful when modifying
CONTROL_DATABASE_SETTINGS = {"CONTROL_DATABASE":CONTROL_DATABASE,
                             'DATABASE_HOST':DB_HOST,
                             #'DATABASE_PORT':SECRETS.DB_PORT,
                             'DATABASE_USER':DB_USER,
                             'DATABASE_PASSWORD':DB_PASSWORD,
                             'DATABASE_NAME_DATA':"rapd_data",
                             'DATABASE_NAME_USERS':"rapd_users",
                             'DATABASE_NAME_CLOUD':"rapd_cloud",
                             # Connection can be 'pool' for database on single computer, or
                             # 'sentinal' for high availability on redundant computers.
                             'REDIS_CONNECTION':"sentinel",
                             "REDIS_HOST":REDIS_HOST,
                             "REDIS_PORT":REDIS_PORT,
                             "REDIS_DB":REDIS_DB,
                             "REDIS_SENTINEL_HOSTS":SENTINEL_HOSTS,
                             "REDIS_MASTER_NAME":REDIS_MASTER_NAME,
                             }

LAUNCHER_SETTINGS = {
    "LAUNCHER_REGISTER":LAUNCHER_REGISTER,
    "LAUNCHER_SPECIFICATIONS":LAUNCHER_SPECIFICATIONS,
    "LOCK_FILE":LAUNCHER_LOCK_FILE,
    "RAPD_LAUNCHER_ADAPTER_DIRECTORIES":RAPD_LAUNCHER_ADAPTER_DIRECTORIES
}

LAUNCH_SETTINGS = {
    "RAPD_PLUGIN_DIRECTORIES":RAPD_PLUGIN_DIRECTORIES,
    #"LAUNCHER_ADDRESS":(LAUNCHER_SPECIFICATIONS[LAUNCHER_TARGET]["ip_address"],
    #                    LAUNCHER_SPECIFICATIONS[LAUNCHER_TARGET]["port"])
    "LAUNCHER_SPECIFICATIONS":LAUNCHER_SPECIFICATIONS,
}

IMAGE_MONITOR_SETTINGS = {"REDIS_CLUSTER" : REDIS_CLUSTER,
                          'REDIS_CONNECTION':"sentinel",
                          "REDIS_SENTINEL_HOSTS" : SENTINEL_HOSTS,
                          #"SENTINEL_PORT" : SECRETS.SENTINEL_PORT,
                          "REDIS_MASTER_NAME" : REDIS_MASTER_NAME,
                          "REDIS_HOST":REDIS_HOST,
                          "REDIS_PORT":REDIS_PORT,
                          "REDIS_DB":REDIS_DB,
                          }

RUN_MONITOR_SETTINGS = {"REDIS_CLUSTER" : REDIS_CLUSTER,
                        'REDIS_CONNECTION':"sentinel",
                          "REDIS_SENTINEL_HOSTS" : SENTINEL_HOSTS,
                          #"SENTINEL_PORT" : SECRETS.SENTINEL_PORT,
                          "REDIS_MASTER_NAME" : REDIS_MASTER_NAME,
                          "REDIS_HOST":REDIS_HOST,
                          "REDIS_PORT":REDIS_PORT,
                          "REDIS_DB":REDIS_DB,
                          }

CLOUD_MONITOR_SETTINGS = {
        "CLOUD_BINARY_MERGE_HANDLER":CLOUD_BINARY_MERGE_HANDLER,
        "CLOUD_DATA_COLLECTION_PARAMS":CLOUD_DATA_COLLECTION_PARAMS,
        "CLOUD_DATA_COLLECTION_PARAMS_HANDLER":CLOUD_DATA_COLLECTION_PARAMS_HANDLER,
        "CLOUD_DOWNLOAD_HANDLER":CLOUD_DOWNLOAD_HANDLER,
        "CLOUD_MINIKAPPA":CLOUD_MINIKAPPA,
        "CLOUD_MINIKAPPA_HANDLER":CLOUD_MINIKAPPA_HANDLER,
        "CLOUD_MR_HANDLER":CLOUD_MR_HANDLER,
        "CLOUD_REINDEX_HANDLER":CLOUD_REINDEX_HANDLER,
        "CLOUD_REINTEGRATE_HANDLER":CLOUD_REINTEGRATE_HANDLER,
        #"LAUNCHER_ADDRESS":LAUNCHER_ADDRESS,
        "DETECTOR_SUFFIX":DETECTOR_SUFFIX,
        "UI_HOST":UI_HOST,
        "UI_PORT":UI_PORT,
        "UI_USER":UI_USER,
        "UI_PASSWORD":UI_PASSWORD,
        "UPLOAD_DIR":UPLOAD_DIR
        }

SITE_ADAPTER_SETTINGS = {"ID":ID,
                         "REDIS_HOST":SITE_REDIS_IP,
                         "REDIS_PORT":SITE_REDIS_PORT,
                         "REDIS_DB":SITE_REDIS_DB}

REMOTE_ADAPTER_SETTINGS = {"ID":ID,
                           "MONGO_CONNECTION_STRING":MONGO_CONNECTION_STRING,
                           "REDIS_CLUSTER":REDIS_CLUSTER,
                           'REDIS_CONNECTION':"sentinel",
                           "REDIS_SENTINEL_HOSTS":SENTINEL_HOSTS,
                           #"SENTINEL_PORT":SECRETS.SENTINEL_PORT,
                           "REDIS_MASTER_NAME":REDIS_MASTER_NAME}

## Aggregators
## Be extra careful when modifying
"""
LAUNCH_SETTINGS = {
    "LAUNCH_ADDRESSES":LAUNCH_ADDRESSES
}

BEAM_SETTINGS = {"BEAM_FLUX":BEAM_FLUX,
                 "BEAM_SIZE_X":BEAM_SIZE_X,
                 "BEAM_SIZE_Y":BEAM_SIZE_Y,
                 "BEAM_SHAPE":BEAM_SHAPE,
                 "BEAM_APERTURE_SHAPE":BEAM_APERTURE_SHAPE,
                 "BEAM_GAUSS_X":BEAM_GAUSS_X,
                 "BEAM_GAUSS_Y":BEAM_GAUSS_Y,
                 "BEAM_CENTER_DATE":BEAM_CENTER_DATE,
                 "BEAM_CENTER_X":BEAM_CENTER_X,
                 "BEAM_CENTER_Y":BEAM_CENTER_Y}


IMAGE_MONITOR_SETTINGS = {"REDIS_HOST" : IMAGE_MONITOR_REDIS_HOST,
                          "REDIS_PORT" : IMAGE_MONITOR_REDIS_PORT,
                          "REDIS_CLUSTER" : IMAGE_MONITOR_REDIS_CLUSTER,
                          "SENTINEL_HOST" : IMAGE_MONITOR_SENTINEL_HOST,
                          "SENTINEL_PORT" : IMAGE_MONITOR_SENTINEL_PORT,
                          "REDIS_MASTER_NAME" : IMAGE_MONITOR_REDIS_MASTER_NAME}

RUN_MONITOR_SETTINGS = {"REDIS_HOST" : RUN_MONITOR_REDIS_HOST,
                        "REDIS_PORT" : RUN_MONITOR_REDIS_PORT,
                        "REDIS_CLUSTER" : RUN_MONITOR_REDIS_CLUSTER,
                        "SENTINEL_HOST" : RUN_MONITOR_SENTINEL_HOST,
                        "SENTINEL_PORT" : RUN_MONITOR_SENTINEL_PORT,
                        "REDIS_MASTER_NAME" : RUN_MONITOR_REDIS_MASTER_NAME}

CLOUD_MONITOR_SETTINGS = {
    "CLOUD_HANDLER_DIRECTORIES" : CLOUD_HANDLER_DIRECTORIES,
    "LAUNCH_ADDRESSES" : LAUNCH_ADDRESSES,
    "DETECTOR_SUFFIX" : DETECTOR_SUFFIX,
    "UI_HOST" : UI_HOST,
    "UI_PORT" : UI_PORT,
    "UI_USER" : UI_USER,
    "UI_PASSWORD" : UI_PASSWORD,
    "UPLOAD_DIR" : UPLOAD_DIR
    }

SITE_ADAPTER_SETTINGS = {"ID" : ID,
                         "REDIS_HOST" : SITE_ADAPTER_REDIS_HOST,
                         "REDIS_PORT" : SITE_ADAPTER_REDIS_PORT,
                         "REDIS_DB" : SITE_ADAPTER_REDIS_DB}

REMOTE_ADAPTER_SETTINGS = {"ID" : ID,
                           "MONGO_CONNECTION_STRING" : REMOTE_ADAPTER_MONGO_CONNECTION_STRING,
                           "REDIS_CLUSTER" : REMOTE_ADAPTER_REDIS_CLUSTER,
                           "SENTINEL_HOST" : REMOTE_ADAPTER_SENTINEL_HOST,
                           "SENTINEL_PORT" : REMOTE_ADAPTER_SENTINEL_PORT,
                           "REDIS_MASTER_NAME" : REMOTE_ADAPTER_REDIS_MASTER_NAME,
                           "REDIS_HOST" : REMOTE_ADAPTER_REDIS_HOST,
                           "REDIS_PORT" : REMOTE_ADAPTER_REDIS_PORT}
"""
# secret_settings_general = { #database information
#                             'db_host'                : 'rapd.nec.aps.anl.gov',         #location of mysql database
#                             'db_user'                : 'rapd1',                        #internal username
#                             'db_password'            : '',         #
#                             'db_data_name'           : 'rapd_data',                    #database names
#                             'db_users_name'          : 'rapd_users',                   #
#                             'db_cloud_name'          : 'rapd_cloud',                   #
#                             #ui server information
#                             'ui_host'                : 'rapd.nec.aps.anl.gov',         #server of the ui
#                             'ui_user_dir'            : '/var/www/html/rapd/users/',    #location of the users
#                             'ui_upload_dir'          : '/var/www/html/rapd/uploads/',  #location of uploaded files
#                             'ui_port'                : 22,                             #
#                             'ui_user'                : 'apache',                       #username on the ui host for ssh
#                             'ui_password'            : '',                 #
#                             #controller settings
#                             'controller_port'        : 50001,                          #the post for the core process to listen on for communications
#                             #cluster server settings
#                             'cluster_port'           : 50000,
#                             'process_port_init'      : 50002,                         #the port number to start at when making a listener
#                             'cluster_logfile_dir'    : '/share/apps/necat/tmp',        #the location to put the tempfile - could be local or shared
#                             #'cluster_logfile_dir'     : '/tmp',
#                             #image tags for special images
#                             'beamcenter_tag'         : 'beamcenter',
#                             #diffraction-based centering settings
#                             'diffcenter_tag'         : '_dfa_',
#                             'diffcenter_server'      : '164.54.212.150',  #gadolinium
#                             #'diffcenter_server'     : '164.54.212.162',  #gadolinium-4 compute-0-3
#                             'diffcenter_port'        : 8125,
#                             #snapshot-based quality analysis settings
#                             'quickanalysis_tag'      : 'raster_snap',
#                             'quickanalysis_server'   : '164.54.212.150',  #gadolinium
#                             'quickanalysis_port'     : 8125,
#                             'quickanalysis_test_tag' : 'raster_snap_test',
#                             #tag for ignoring the image
#                             'ignore_tag'             : 'delete',
#                             #Controlling the number of processes running concurrently
#                             'throttle_strategy'      : False,
#                             'active_strategy_limit'  : 2,
#                             #A delay between existence and moving a file from fs to webserver
#                             'filesystem_delay'       : 0.5,
#                             #should the users get data from rapd in their data_root_dir?
#                             'copy_data'              : True,
#                             #directory for beamline puck settings files
#                             'puck_dir'               : {'C' : '/mnt/shared_drive/CONFIG/phi/',
#                                                         'E' : '/mnt/shared_drive/CONFIG/phii/'},
#                             #Cutoff date in MYSQL format,yyyy-mm-dd hh:mm:ss, for creating Master Puck List
#                             'puck_cutoff'            : '2011-01-01 00:00:00',
#                             #testing information
#                             'faux_coll_dir'          : '/gpfs5/users/necat/test_rapd',
#                             #where to place uploaded files
#                             'upload_dir'             : '/gpfs5/users/necat/rapd/uranium/trunk/uploads/',
#                             #turn on/off tranfer to ui
#                             'xfer_to_ui'             : True,
#                             #Redis
#                             'remote_redis_ip'        : '164.54.212.169',
#                             'remote_redis_ip2'       : '164.54.212.172'
#                             }
#
# #For detector vendortypes look in ../share/phenix/modules/cctbx_project/iotbx/detectors
# #for your detector file and do a search for 'self.vendortype'
# #Common detector vendortypes are 'MARCCD', 'ADSC', 'Pilatus-6M', "EIGER"
# settings_C = {'beamline'          : 'C',
#               'multiprocessing'   : 'True',
#               'spacegroup'        : 'None',
#               'sample_type'       : 'Protein',
#               'solvent_content'   : '0.55',
#               'susceptibility'    : '1.0',
#               'crystal_size_x'    : '100',
#               'crystal_size_y'    : '100',
#               'crystal_size_z'    : '100',
#               'a'                 : '0',
#               'b'                 : '0',
#               'c'                 : '0',
#               'alpha'             : '0',
#               'beta'              : '0',
#               'gamma'             : '0',
#               'work_dir_override' : 'False',
#               'work_directory'    : '/gpfs5/users/necat/rapd/uranium/trunk',
#               'beam_flip'         : 'False',
#               'x_beam'            : '0',
#               'y_beam'            : '0',
#               'index_hi_res'      : '0',
#               'strategy_type'     : 'best',
#               'best_complexity'   : 'none',
#               'mosflm_seg'        : '1',
#               'mosflm_rot'        : '0.0',
#               'mosflm_start'      : '0.0',
#               'mosflm_end'        : '360.0',
#               'min_exposure_per'  : '1',
#               'aimed_res'         : '0',
#               'beam_size_x'       : 'AUTO',
#               'beam_size_y'       : 'AUTO',
#               'integrate'         : 'rapd',
#               'reference_data_id' : '0',
#               #Detector info
#               'vendortype'         : 'Pilatus-6M',
#               'max_distance'       : 1200, #max crystal to detector distance in mm
#               'min_distance'       : 150,  #min crystal to detector distance in mm
#               'min_del_omega'      : 0.2,  #min delta omega per frame
#               'min_exp_time'       : 0.2,  #min exposure time per frame
#               #Control processing of unbinned data
#               'unbinned_onthefly' : True,
#               #Should we perform remote-access tasks?
#               'remote'            : True,
#               'connect_to_beamline' : True,
#               #Beam center formula for overiding center
#               'use_beam_formula'  : True,
#               #Remote server information
#               #Redis database information
#               'remote_redis_ip'   : '164.54.212.169',
#               'remote_redis_port' : 6379,
#               'remote_redis_db'   : 0,
#               # Short circuits for scanning analysis
#               'analysis_shortcircuits' : ['/gpfs5/users/necat/phi_dfa_1/in/0_0',
#                                           '/gpfs5/users/necat/phi_dfa_2/in/0_0',
#                                           '/gpfs5/users/necat/phi_raster_snap/in/0_0',
#                                           '/gpfs5/users/necat/phi_rastersnap_scan_data/0_0',
#                                           '/gpfs5/users/necat/phi_dfa_scan_data/0_0',
#                                           '/gpfs5/users/necat/phi_ova_scan_data/0_0',
#                                           '/gpfs5/users/necat/rapd/uranium/trunk/test_data'],
#               #Calculated based on shift seen in Labelit position
#               'beam_center_date'  : 'December 15, 2015',
#               'beam_center_x_b'   : 216.69863163342047,
#               'beam_center_x_m1'  : 0.0074191081960643147,
#               'beam_center_x_m2'  : -6.5562922339598381e-05,
#               'beam_center_x_m3'  : 2.1583593307933331e-07,
#               'beam_center_x_m4'  : -3.4704636547598035e-10,
#               'beam_center_x_m5'  : 2.7271585390017941e-13,
#               'beam_center_x_m6'  : -8.3513972486673267e-17,
#               'beam_center_y_b'   : 221.63035570545022,
#               'beam_center_y_m1'  : 0.01491441871781808,
#               'beam_center_y_m2'  : -0.00010365810753786116,
#               'beam_center_y_m3'  : 3.4916735265130452e-07,
#               'beam_center_y_m4'  : -6.0339399295445197e-10,
#               'beam_center_y_m5'  : 5.1086581671903505e-13,
#               'beam_center_y_m6'  : -1.669020800967166e-16,
#              }
#
#
#
# secret_settings_C = { 'beamline'          : 'C',
#                       #cluster info
#                       'cluster_host'      : '164.54.212.150',   #gadolinium
#                       'adsc_server'       : 'http://164.54.212.80:8001',
#                       #Redis database information
#                       'redis_ip'          : '164.54.212.56',
#                       'redis_port'        : 6379,
#                       'redis_db'          : 0,
#                       #alternative cluster information
#                       'cluster_stac'      : '164.54.212.165',   #uranium
#                       'cluster_strategy'  : False,
#                       'cluster_integrate' : False,
#                       #MongoDB
#                       'mongo-type'        : 'replicaset',
#                       'mongo-connection'  : 'remote,remote-c,rapd',
#                       'mongo-replicaset'  : 'rs0',
#                       'mongo-connection-string' : 'mongodb://remote,remote-c,rapd/?replicaSet=rs0',
#                       #Redis database information
#                       'remote_redis_ip'    : '164.54.212.169',
#                       'remote_redis_ip2'   : '164.54.212.172',
#                       'remote_redis_port'  : 6379,
#                       'remote_redis_db'    : 0,
#                       #cloud information
#                       'cloud_interval'     : 1.0,                           #set to 0.0 if you want cloud monitoring turned off
#                       'local_ip_prefix'    :     '164.54.212',
#                       'adx_perframe_file'  :     '/mnt/shared_drive/CONFIG/phi_adx_perframe_cenxyz.dat',
#                       'scan_coords_file'   :     '/mnt/shared_drive/CONFIG/PHI_SCREEN_SCAN_COORDS.DAT',
#                       'console_marcollect' :    '/mnt/shared_drive/CONFIG/id_c_marcollect',
#                       'diffcenter_test_image' : '/gpfs5/users/necat/rapd/uranium/trunk/images/dfa_test_1_001.img',
#                       'diffcenter_test_dat' :   '/gpfs5/users/necat/phi_dfa_1/out/dfa_heartbeat.dat',
#                       'rastersnap_test_dat' :   '/gpfs5/users/necat/phi_raster_snap/out/phi_heartbeat.dat',
#                       'rastersnap_test_image' : '/gpfs5/users/necat/rapd/uranium/trunk/test_data/test_raster_snap_test_0_0001.cbf',
#                       'file_source': 'PILATUS'}
#
# secret_settings_C.update(secret_settings_general)
#
# ##########################################################################
#
# settings_E = { 'beamline'           : 'E',
#                'multiprocessing'    : 'True',
#                'spacegroup'         : 'None',
#                'sample_type'        : 'Protein',
#                'solvent_content'    : '0.55',
#                'susceptibility'     : '1.0',
#                'crystal_size_x'     : '100',
#                'crystal_size_y'     : '100',
#                'crystal_size_z'     : '100',
#                'a'                  : '0',
#                'b'                  : '0',
#                'c'                  : '0',
#                'alpha'              : '0',
#                'beta'               : '0',
#                'gamma'              : '0',
#                'work_dir_override'  : 'False',
#                'work_directory'     : '/gpfs5/users/necat/rapd/copper/trunk',
#                'beam_flip'          : 'False',
#                'x_beam'             : '0',
#                'y_beam'             : '0',
#                'index_hi_res'       : '0',
#                'strategy_type'      : 'best',
#                'best_complexity'    : 'none',
#                'mosflm_seg'         : '1',
#                'mosflm_rot'         : '0.0',
#                'mosflm_start'       : '0.0',
#                'mosflm_end'         : '360.0',
#                'min_exposure_per'   : '1' ,
#                'aimed_res'          : '0',
#                'beam_size_x'        : 'AUTO',
#                'beam_size_y'        : 'AUTO',
#                'integrate'          : 'rapd',
#                'reference_data_id'  : '0',
#                #Detector info
#                'vendortype'         : 'ADSC',
#                'max_distance'       : 1200, #max crystal to detector distance in mm (BEST)
#                'min_distance'       : 125,  #min crystal to detector distance in mm (BEST)
#                'min_del_omega'      : 0.5,  #min delta omega per frame (BEST)
#                'min_exp_time'       : 0.5,  #min exposure time per frame
#                #Control processing of unbinned data
#                'unbinned_onthefly'  : True,
#                #Should we perform remote-access tasks?
#                'remote'             : True,
#                'connect_to_beamline':True,
#                #Remote server information
#                #Redis database information
#                'remote_redis_ip'        : '164.54.212.169',
#                'remote_redis_port'      : 6379,
#                'remote_redis_db'        : 0 ,
#                #Beam center formula for overiding center
#                'use_beam_formula'  : True,
#                # Short circuits for scanning analysis
#                'analysis_shortcircuits' : ['/gpfs5/users/necat/phii_dfa_1/in',
#                                            '/gpfs5/users/necat/phii_dfa_2/in',
#                                            '/gpfs5/users/necat/phii_raster_snap/in',
#                                            '/gpfs5/users/necat/phii_rastersnap_scan_data',
#                                            '/gpfs5/users/necat/phii_dfa_scan_data',
#                                            '/gpfs5/users/necat/phii_ova_scan_data',
#                                            '/gpfs5/users/necat/rapd/uranium/trunk/test_data'],
#                #Calculated from Labelit refined position
#          'beam_center_date'  : 'December 7, 2015 (Q315)',
#          'beam_center_x_b': 153.94944895756946,
#                'beam_center_x_m1': -0.016434436106566495,
#                'beam_center_x_m2': 3.5990848937868658e-05,
#                'beam_center_x_m3': -8.2987834172005917e-08,
#                'beam_center_x_m4': 1.0732920112697317e-10,
#                'beam_center_x_m5': -7.339858946384788e-14,
#                'beam_center_x_m6': 2.066312749407257e-17,
#          'beam_center_y_b': 158.56546190593907,
#                'beam_center_y_m1': 0.0057578279496966192,
#                'beam_center_y_m2': -3.9726067083100419e-05,
#                'beam_center_y_m3': 1.1458201832002297e-07,
#                'beam_center_y_m4': -1.7875879553926729e-10,
#                'beam_center_y_m5': 1.4579198435694557e-13,
#                'beam_center_y_m6': -4.7910792416525411e-17,
#
#
#
#                }
#
#
# secret_settings_E = { 'beamline'          : 'E',
#                       #cluster info
#                       #'cluster_host'      : '164.54.212.165',    #uranium
#                       #'cluster_host'      : '164.54.212.166',    #copper
#                       'cluster_host'      : '164.54.212.150',    #gadolinium
#                       #'cluster_host'      : '127.0.0.1',         #localhost
#                       'adsc_server'       :  'http://164.54.212.180:8001',
#                       #Redis database information
#                       'redis_ip'          : '164.54.212.125',
#                       'redis_port'        : 6379,
#                       'redis_db'          : 0,
#                       "adx_perframe_file" : "/mnt/shared_drive/CONFIG/phii_adx_perframe_cenxyz.dat",
#                       'scan_coords_file'  : '/mnt/shared_drive/CONFIG/PHII_SCREEN_SCAN_COORDS.DAT',
#                       #MongoDB
#                       'mongo-type'          : 'replicaset',
#                       'mongo-connection'    : 'remote,remote-c,rapd',
#                       'mongo-replicaset'    : 'rs0',
#                       'mongo-connection-string' : 'mongodb://remote,remote-c,rapd/?replicaSet=rs0',
#                       #alternative cluster information
#                       'cluster_stac'      : '164.54.212.165',   #uranium
#                       'cluster_strategy'  : False,
#                       'cluster_integrate' : False,
#                       #Redis database information
#                       'remote_redis_ip'        : '164.54.212.169',
#                       'remote_redis_port'      : 6379,
#                       'remote_redis_db'        : 0 ,
#                       #'cluster_strategy'  : '164.54.212.166',   #copper
#                       #'cluster_integrate' : '164.54.212.150',   #gadolinium
#                       #cloud information
#                       'cloud_interval'    : 0.0,                           #set to 0.0 if you want cloud monitoring turned off
#                       'local_ip_prefix'   : '164.54.212',
#                       'console_marcollect': '/mnt/shared_drive/CONFIG/id_e_marcollect',
#                       #'rastersnap_test_image' : '/gpfs5/users/necat/rapd/copper/trunk/test_data/raster_snap_test_0_001.img',
#                       #'rastersnap_test_dat' : '/gpfs5/users/necat/phii_raster_snap/out/phii_heartbeat.dat',
#                       'rastersnap_test_image' : '/gpfs5/users/necat/rapd/copper/trunk/test_data/raster_snap_test_0_001.img',
#                       'rastersnap_test_dat' : '/gpfs5/users/necat/phii_raster_snap/out/phii_heartbeat.dat',
#                       'file_source': 'Q315'}
#
# secret_settings_E.update(secret_settings_general)
#
# ################################################################################
#
# settings_T = { 'beamline'          : 'T',
#                'multiprocessing'   : 'True',
#                'spacegroup'        : 'None',
#                'sample_type'       : 'Protein',
#                'solvent_content'   : '0.55',
#                'susceptibility'    : '1.0',
#                'crystal_size_x'    : '100',
#                'crystal_size_y'    : '100',
#                'crystal_size_z'    : '100',
#                'a'                 : '0',
#                'b'                 : '0',
#                'c'                 : '0',
#                'alpha'             : '0',
#                'beta'              : '0',
#                'gamma'             : '0',
#                'work_dir_override' : 'False',
#                'work_directory'    : '/gpfs5/users/necat/rapd/uranium/trunk',
#                'beam_flip'         : 'False',
#                'x_beam'            : '0',
#                'y_beam'            : '0',
#                'index_hi_res'      : '0',
#                'strategy_type'     : 'best',
#                'best_complexity'   : 'none',
#                'mosflm_seg'        : '1',
#                'mosflm_rot'        : '0.0',
#                'mosflm_start'      : '0.0',
#                'mosflm_end'        : '360.0',
#                'min_exposure_per'  : '1' ,
#                'aimed_res'         : '0',
#                'beam_size_x'       : 'AUTO',
#                'beam_size_y'       : 'AUTO',
#                'integrate'         : 'rapd',
#                #Should we perform remote-access tasks?
#                'remote'            : True,
#                'connect_to_beamline' : True,
#                #Beam center formula for overiding center
#                'use_beam_formula'  : True,
#                'beam_center_date'  : 'August 20, 2010',
#                'beam_center_x_m'   : -0.004518,
#                'beam_center_x_b'   : 159.30,
#                'beam_center_y_m'   : -0.000300,
#                'beam_center_y_b'   : 156.02,
#                # Short circuits for scanning analysis
#                'analysis_shortcircuits' : ['/Users/fmurphy/workspace/remote/trunk/ui/test/phi_rastersnap_scan_data/0_0',
#                                            '/Users/fmurphy/workspace/remote/trunk/ui/test/phi_dfa_scan_data/0_0',
#                                            '/gpfs5/users/necat/phi_dfa_1/in/0_0',
#                                            '/gpfs5/users/necat/phi_dfa_2/in/0_0',
#                                            '/gpfs5/users/necat/phi_raster_snap/in/0_0',
#                                            '/gpfs5/users/necat/phi_rastersnap_scan_data/0_0',
#                                            '/gpfs5/users/necat/phi_dfa_scan_data/0_0',
#                                            '/gpfs5/users/necat/phi_ova_scan_data/0_0',
#                                            '/gpfs5/users/necat/rapd/uranium/trunk/test_data'],  # temporary for short-circuit testing
#                 }
#
#
# secret_settings_T = { 'beamline'            : 'T',
#                       'cluster_host'        : '164.54.212.150', #gadolinium
#                       #'cluster_host'       : '164.54.212.19',  #vertigo
#                       #'cluster_host'       : '164.54.212.165',  #uranium
#                       #'cluster_host'       : '164.54.212.166',  #copper
#                       #'cluster_host'       : '127.0.0.1',  #localhost
#                       'adsc_server'         :  'http://127.0.0.1:8001',
#                       'redis_ip'            : '127.0.0.1',
#                       'redis_ip2'           : '127.0.0.1',
#                       #Redis database information
#                       'remote_redis_ip'        : '127.0.0.1',
#                       'remote_redis_ip2'       : '127.0.0.1',
#                       'remote_redis_port'      : 6379,
#                       'remote_redis_db'        : 0 ,
#                       #alternative cluster information
#                       'cluster_stac'        : False,
#                       'cluster_strategy'    : False,
#                       'cluster_integrate'   : False,
#                       #'cluster_strategy'  : '164.54.212.166',   #copper
#                       #'cluster_integrate' : '164.54.212.150',   #gadolinium
#                       # MongoDB Information
#                       'mongo-type'          : 'single',
#                       'mongo-connection'    : '127.0.0.1',
#                       #'mongo-type'          : 'replicaset',
#                       #'mongo-connection'    : 'remote,remote-c,rapd',
#                       'mongo-replicaset'    : 'rs0',
#                       'mongo-connection-string' : 'mongodb://127.0.0.1',
#                       #cloud information
#                       'cloud_interval'      : 1.0,                           #set to 0.0 if you want cloud monitoring turned off
#                       'local_ip_prefix'     : '164.54.212',
#                       'scan_coords_file'    : '/Users/fmurphy/workspace/rapd_subclipse/PHI_SCREEN_SCAN_COORDS.DAT',
#                       'console_marcollect'  : '/tmp/id_c_marcollect',
#                       'diffcenter_test_image' : '/gpfs5/users/necat/rapd/uranium/trunk/images/dfa_test_1_001.img',
#                       'diffcenter_test_dat' :   '/gpfs5/users/necat/phi_dfa_1/out/dfa_heartbeat.dat',
#                       'rastersnap_test_dat' :   '/gpfs5/users/necat/phi_raster_snap/out/phi_heartbeat.dat',
#                       'rastersnap_test_image' : '/gpfs5/users/necat/rapd/uranium/trunk/test_data/test_raster_snap_test_0_0001.cbf',
#                       'file_source': 'Q315'}
#
# secret_settings_T.update(secret_settings_general)
#
# ######################################################################################
#
# beamline_settings = { 'C' : settings_C,
#                       'E' : settings_E,
#                       'T' : settings_T }
#
# secret_settings = { 'C' : secret_settings_C,
#                     'E' : secret_settings_E,
#                     'T' : secret_settings_T}
#
# ######################################################################################
#
# dataserver_settings = {#ID24-C
#                        'nec-pid.nec.aps.anl.gov'  : ('/usr/local/ccd_dist_md2b_rpc/tmp/marcollect','/usr/local/ccd_dist_md2b_rpc/tmp/xf_status','C'),
#                        #ID24-E
#                        'selenium.nec.aps.anl.gov' : ('/usr/local/ccd_dist_md2_rpc/tmp/marcollect','/usr/local/ccd_dist_md2_rpc/tmp/xf_status','E'),
#                        #DEFAULT
#                        'default'                  : ('/tmp/marcollect','/tmp/xf_status','T')
#                       }
#
#


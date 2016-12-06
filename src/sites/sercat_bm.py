"""Site description for SERCAT ID beamline"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

# Standar imports
import sys

# RAPD imports
from utils.site import read_secrets

# Site ID - limited to 12 characters by MySQL
ID = "SERCAT_BM"

# The secrets file - do not put in github repo!
SECRETS_FILE = "sites.secrets_sercat_bm"

# Copy the secrets attribute to the local scope
# Do not remove unless you know what you are doing!
try:
    read_secrets(SECRETS_FILE, sys.modules[__name__])
except:
    pass

# X-ray source characteristics
# Flux of the beam
BEAM_FLUX = 8E11
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
BEAM_CENTER_DATE = "2015-12-07"
# Beamcenter equation coefficients (b, m1, m2, m3, m4, m5, m6)
BEAM_CENTER_X = (153.94944895756946,
                 -0.016434436106566495,
                 3.5990848937868658e-05,
                 -8.2987834172005917e-08,
                 1.0732920112697317e-10,
                 -7.339858946384788e-14,
                 2.066312749407257e-17)
BEAM_CENTER_Y = (158.56546190593907,
                 0.0057578279496966192,
                 -3.9726067083100419e-05,
                 1.1458201832002297e-07,
                 -1.7875879553926729e-10,
                 1.4579198435694557e-13,
                 -4.7910792416525411e-17)

# Logging
# Linux should be /var/log/
LOGFILE_DIR = "/tmp/log"
LOG_LEVEL = 50

# Control process settings
# Process is a singleton? The file to lock to. False if no locking.
LOCK_FILE = "/tmp/lock/rapd_core.lock"
# Where files from UI are uploaded - should be visible by launch instance
UPLOAD_DIR = "/gpfs5/users/necat/rapd/uranium/trunk/uploads"

# Control settings
# Database to use for control operations. Options: "mysql"
CONTROL_DATABASE = "mysql"
CONTROL_DATABASE_DATA = "rapd_data"
CONTROL_DATABASE_USERS = "rapd_users"
CONTROL_DATABASE_CLOUD = "rapd_cloud"
# Redis databse
# Running in a cluster configuration - True || False
CONTROL_REDIS_CLUSTER = False

# Detector settings
# Must have a file in detectors that is all lowercase of this string
DETECTOR = "SERCAT_RAYONIX_MX300HS"
DETECTOR_SUFFIX = ""

# Launcher settings
LAUNCHER_LOCK_FILE = "/tmp/lock/launcher.lock"

# Directories to look for rapd agents
RAPD_AGENT_DIRECTORIES = ("sites.agents",
                          "agents")
# Queried in order, so a rapd_agent_echo.py in src/sites/agents will override
# the same file in src/agents


# Directories to look for launcher adapters
RAPD_LAUNCHER_ADAPTER_DIRECTORIES = ("launch.launcher_adapters",
                                     "sites.launcher_adapters")
# Queried in order, so a shell_simple.py in src/sites/launcher_adapters will override
# the same file in launch/launcher_adapters

# Cluster settings
CLUSTER_ADAPTER = "sites.cluster.sercat"
# Set to False if there is no cluster adapter

# Data gatherer settings
# The data gatherer for this site, in the src/sites/gatherers directory
GATHERER = "sercat.py"
GATHERER_LOCK_FILE = "/tmp/lock/gatherer.lock"

# Monitor for collected images
IMAGE_MONITOR = "sites.image_monitors.necat_e"
# Redis databse
# Running in a cluster configuration - True || False
IMAGE_MONITOR_REDIS_CLUSTER = CONTROL_REDIS_CLUSTER
# Images collected into following directories will be ignored
IMAGE_IGNORE_DIRECTORIES = ()
# Images collected containing the following string will be ignored
IMAGE_IGNORE_STRINGS = ("ignore", )

# Monitor for collected run information
RUN_MONITOR = "sites.run_monitors.necat_e"
# Running in a cluster configuration - True || False
RUN_MONITOR_REDIS_CLUSTER = CONTROL_REDIS_CLUSTER

# Cloud Settings
# The cloud monitor module
CLOUD_MONITOR = "cloud.rapd_cloud"
# Pause between checking the database for new cloud requests in seconds
CLOUD_INTERVAL = 10
# Directories to look for cloud handlers
CLOUD_HANDLER_DIRECTORIES = ("cloud.handlers", )

# For connecting to the site
SITE_ADAPTER = "sites.site_adapters.necat"
# Running in a cluster configuration - True || False
SITE_ADAPTER_REDIS_CLUSTER = False

# For connecting to the remote access system fr the site
REMOTE_ADAPTER = "sites.site_adapters.necat_remote"     # file name prefix for adapter in src/
REMOTE_ADAPTER_REDIS_CLUSTER = CONTROL_REDIS_CLUSTER


##
## Aggregators
## Be extra careful when modifying
CONTROL_DATABASE_SETTINGS = {
    "CONTROL_DATABASE":CONTROL_DATABASE,
    "DATABASE_NAME_DATA":CONTROL_DATABASE_DATA,
    "DATABASE_NAME_USERS":CONTROL_DATABASE_USERS,
    "DATABASE_NAME_CLOUD":CONTROL_DATABASE_CLOUD,
    "DATABASE_HOST":CONTROL_DATABASE_HOST,
    "DATABASE_PORT":CONTROL_DATABASE_PORT,
    "DATABASE_USER":CONTROL_DATABASE_USER,
    "DATABASE_PASSWORD":CONTROL_DATABASE_PASSWORD
}


LAUNCHER_SETTINGS = {
    "LAUNCHER_REGISTER":LAUNCHER_REGISTER,
    "LAUNCHER_SPECIFICATIONS":LAUNCHER_SPECIFICATIONS,
    "LOCK_FILE":LAUNCHER_LOCK_FILE,
    "RAPD_LAUNCHER_ADAPTER_DIRECTORIES":RAPD_LAUNCHER_ADAPTER_DIRECTORIES
}

LAUNCH_SETTINGS = {
    "RAPD_AGENT_DIRECTORIES":RAPD_AGENT_DIRECTORIES,
    "LAUNCHER":(LAUNCHER_REGISTER[0][0], LAUNCHER_SPECIFICATIONS[LAUNCHER_REGISTER[0][2]]["port"])
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
#    "LAUNCHER_IDS" : LAUNCHER_IDS,
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
# 	       'beam_center_date'  : 'December 7, 2015 (Q315)',
# 	       'beam_center_x_b': 153.94944895756946,
#                'beam_center_x_m1': -0.016434436106566495,
#                'beam_center_x_m2': 3.5990848937868658e-05,
#                'beam_center_x_m3': -8.2987834172005917e-08,
#                'beam_center_x_m4': 1.0732920112697317e-10,
#                'beam_center_x_m5': -7.339858946384788e-14,
#                'beam_center_x_m6': 2.066312749407257e-17,
# 	       'beam_center_y_b': 158.56546190593907,
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

# def NecatDetermineImageType(data,logger):
#     """
#     Determine the type of image that has been noticed by RAPD.
#
#     Current types:
#         data - user data image
#         diffcenter - diffraction-based centering image
#         beamcenter - direct beam shot for beam center calculations
#
#     data is currently expected to be a dict with a 'fullname' entry which is the full
#          name of the image file
#     """
#     logger.debug('NecatDetermineImageType %s' % str(data))
#
#     if (secret_settings_general['beamcenter_tag'] in data['fullname']):
#         image_type = 'beamcenter'
#     elif (secret_settings_general['diffcenter_tag'] in data['fullname']):
#         image_type = 'diffcenter'
#     elif (secret_settings_general['quickanalysis_test_tag'] in data['fullname']):
#         image_type = 'quickanalysis-test'
#     elif (secret_settings_general['quickanalysis_tag'] in data['fullname']):
#         image_type = 'quickanalysis'
#     elif (secret_settings_general['ignore_tag'] in data['fullname']):
#         image_type = 'ignore'
#     else:
#         image_type = 'data'
#
#     #output to the log
#     logger.debug('%s id %s' % (data['fullname'],image_type))
#
#     return(image_type)
#
# def GetDataRootDir(fullname,logger):
#     """
#     Derive the data root directory from the user directory
#
#     The logic will most likely be unique for each beamline, so this
#     finds its home in rapd_site.py
#     """
#     #isolate distinct properties of the images path
#     logger.info('GetRootDataDir %s', fullname)
#
#     path_split    = fullname.split(os.path.sep)
#     data_root_dir = False
#
#     gpfs   = False
#     users  = False
#     inst   = False
#     group  = False
#     images = False
#
#     if path_split[1].startswith('gpfs'):
#         gpfs = path_split[1]
#         if path_split[2] == 'users':
#             users = path_split[2]
#             if path_split[3]:
#                 inst = path_split[3]
#                 if path_split[4]:
#                     group = path_split[4]
#
#     if group:
#         data_root_dir = os.path.join('/',*path_split[1:5])
#     elif inst:
#         data_root_dir = os.path.join('/',*path_split[1:4])
#     else:
#         data_root_dir = False
#
#     #return the determined directory
#     return(data_root_dir)
#
#
#
# def GetDataRootDirNewStyle(fullname,logger):
#     """
#     Derive the data root directory from the user directory
#
#     The logic will most likely be unique for each beamline, so this
#     finds its home in rapd_site.py
#
#     As of Run 3 2012 NE-CAT has changed to the format
#     /gpfs6/users/run2012_3/24IDE/GU/Marnett_Oct12
#     """
#     #isolate distinct properties of the images path
#     logger.info('GetRootDataDir %s', fullname)
#
#     path_split    = fullname.split(os.path.sep)
#     data_root_dir = False
#
#     gpfs     = False
#     users    = False
#     run      = False
#     beamline = False
#     inst     = False
#     group    = False
#     images   = False
#
#     logger.info(path_split)
#
#     try:
#         if path_split[1].startswith('gpfs'):
#             gpfs = path_split[1]
#         if path_split[2] == 'users':
#             users = path_split[2]
#         if path_split[3].startswith('run'):
#             run = path_split[3]
#         if path_split[4].startswith('24'):
#             beamline = path_split[4]
#         if (path_split[5]):
#             inst = path_split[5]
#         if (path_split[6]):
#             group = path_split[6]
#
#         logger.info(group)
#
#         if group:
#             data_root_dir = os.path.join('/',*path_split[1:7])
#
#         elif inst:
#             data_root_dir = os.path.join('/',*path_split[1:6])
#         else:
#             data_root_dir = False
#
#     except:
#         data_root_dir = False
#
#     #return the determined directory
#     logger.info(data_root_dir)
#     return(data_root_dir)
#
# def TransferToBeamline(results,type='DIFFCENTER',logger=False):
#     """
#     Make the file to be read by console
#     """
#     if logger:
#         logger.info('TransferToBeamline %s' % type)
#
#
#     if (type == 'QUICKANALYSIS-TEST'):
#         logger.info('>>> %s <<<' % str(results))
#         output_file = results['outfile']
#         output = open(output_file,'w')
#         output.write("%f \n"%time.time());
#         output.close()
#
#     elif (type=='DIFFCENTER'):
#         if (logger) : logger.debug("Xfer diffcenter")
#         #output_file = results['fullname'].replace('in','out').replace('.img','.dat')
#         output_file = results['fullname'].replace('in','out').replace('0_0','').replace('.img','.dat').replace('.cbf','.dat')
#         if (logger) : logger.debug(output_file)
#         output = open(output_file,'w')
#         #output.write('%12.2f\r\n'%results['distl_res'])
#         #output.write('%12.2f\r\n'%results['labelit_res'])
#         output.write('%12.2f\r\n'%results.get('resolution_1',0))
#         output.write('%12.2f\r\n'%results.get('resolution_2',0))
#         output.write('%10d\r\n'%results.get('overloads',0))
#         output.write('%10d\r\n'%results.get('total_spots',0))
#         output.write('%10d\r\n'%results.get('good_b_spots',0))
#         output.write('%10d\r\n'%results.get('in_res_spots',0))
#         output.write('%12.2f\r\n'%results.get('signal_max',0))
#         output.write('%12.2f\r\n'%results.get('signal_mean',0))
#         output.write('%12.2f\r\n'%results.get('signal_min',0))
#         output.write('%12.2f\r\n'%results.get('total_signal',0))
#         output.write('%12.2f\r\n'%results.get('saturation_50',0))
#         #output.write('%12.2f\r\n'%int(results['saturation_max']))
#         #output.write('%12.2f\r\n'%int(results['saturation_mean']))
#         #output.write('%12.2f\r\n'%int(results['saturation_min']))
#         output.close()
#     elif (type=='QUICKANALYSIS'):
#         if (logger):
#            logger.debug('TransferToBeamline %s' % results['fullname'])
#         if results['fullname'] in ['/gpfs5/users/necat/rapd/uranium/trunk/test_data/test_raster_snap_test_0_0001.cbf']:
#             output_file = '/gpfs5/users/necat/phi_raster_snap/out/phi_heartbeat.dat'
#             output = open(output_file,'w')
#             output.write("%f \n"%time.time());
#             output.close()
#         else:
#             output_file = results['fullname'].replace('in','out').replace('0_0','').replace('.img','.dat').replace('.cbf','.dat')
#             output = open(output_file,'w')
#             if (logger):
#                logger.debug('  %s Opened for writing' % output_file)
#             #output.write('%12.2f\r\n'%results['distl_res'])
#             #output.write('%12.2f\r\n'%results['labelit_res'])
#             output.write('%12.2f\r\n'%results['resolution_1'])
#             output.write('%12.2f\r\n'%results['resolution_2'])
#             output.write('%10d\r\n'%results['overloads'])
#             output.write('%10d\r\n'%results['total_spots'])
#             output.write('%10d\r\n'%results['good_b_spots'])
#             output.write('%10d\r\n'%results['in_res_spots'])
#             output.write('%12.2f\r\n'%int(results['signal_max']))
#             output.write('%12.2f\r\n'%int(results['signal_mean']))
#             output.write('%12.2f\r\n'%int(results['signal_min']))
#             output.write('%12.2f\r\n'%int(results['total_signal']))
#             output.write('%12.2f\r\n'%int(results['saturation_50']))
#             """
#             output.write('%12.2f\r\n'%int(results['saturation_max']))
#             output.write('%12.2f\r\n'%int(results['saturation_mean']))
#             output.write('%12.2f\r\n'%int(results['saturation_min']))
#             """
#             output.close()
#         if (logger):
#            logger.debug('  Finished writing %s' % output_file)
#     return(True)
#
# def TransferPucksToBeamline(beamline,puck_contents):
#     """
#     Make puck files to be read by console
#     """
#     puck_dir = secret_settings_general['puck_dir'][beamline]
#     puck = puck_contents.keys()[0]
#     output_file = puck_dir+puck+'/puck_contents.txt'
#     print 'TransferPucksToBeamline dir: %s' % output_file
#     contents = puck_contents.values()[0]
#     output = open(output_file,'w')
#     if type(contents) is str:
#         for i in range(16):
#             output.write('%s\n%s\n'%(contents,contents))
#     else:
#         for i in range(16):
#             output.write('%s\n%s\n'%(contents[i]['CrystalID'],contents[i]['PuckID']))
#     output.close()
#
# def TransferMasterPuckListToBeamline(beamline,allpucks):
#     """
#     Make master list of all available pucks to be read by console
#     """
#     puck_dir = secret_settings_general['puck_dir'][beamline]
#     output_file = puck_dir+'/allpucks.txt'
#     print 'TransferMasterPuckListToBeamline dir: %s' % output_file
#     output = open(output_file,'w')
#     for puck in allpucks:
#         output.write('%s %s\n'%(puck['PuckID'],puck['select']))
#     output.close()
#
# def CopyToUser(root,res_type,result,logger):
#     """
#     Copy processed data to the user's area.
#
#     root - the data root directory for the trip
#     res_type - the type of data we are moving
#                integrate,sad,mr
#     result - the dict from the result
#     logger - instance of logger
#     """
#
#     logger.debug('CopyToUser dir:%s' % root)
#     logger.debug(result)
#
#     try:
#         if result['download_file']:
#             #files/directories
#             if (res_type == "integrate"):
#                 targetdir = os.path.join(root,'process','rapd','integrate',result['repr'])
#             elif (res_type == "sad"):
#                 targetdir = os.path.join(root,'process','rapd','sad',result['repr'])
#             elif (res_type == "mad"):
#                 targetdir = os.path.join(root,'process','rapd','mad',result['repr'])
#             elif (res_type == "mr"):
#                 targetdir = os.path.join(root,'process','rapd','mr',result['repr'])
#             elif (res_type == "smerge"):
#                 targetdir = os.path.join(root,'process','rapd','smerge',result['repr'])
#             elif (res_type == "raster_analysis"):
#                 targetdir = 'discard'
#             else:
#                 targetdir = os.path.join(root,'process','rapd',result['repr'])
#             targetfile = os.path.join(targetdir,os.path.basename(result['download_file']))
#
#             # Handle remote raster scanning
#             if (res_type == "raster_analysis"):
#                 targetfile = result.get('fullname')
#                 targetdir = os.path.dirname(targetfile)
#
#             #Make sure we aren't overwriting files
#             if os.path.exists(targetfile):
#                 counter = 1
#                 targetbase = targetfile+'_'
#                 while (counter < 1000):
#                     targetfile = targetbase+str(counter)
#                     if not os.path.exists(targetfile):
#                         break
#
#             #make sure the target directory exists
#             if not (os.path.exists(targetdir)):
#                 os.makedirs(targetdir)
#
#             #if targetfile already exists - remove
#             if (os.path.exists(targetfile)):
#                 os.remove(targetfile);
#
#             #now copy the file
#             shutil.copyfile(result['download_file'],targetfile)
#             logger.debug('Copied %s to %s'%(result['download_file'],targetfile))
#             if (res_type in ["sad", "mad"]):
#                 shutil.copyfile(result['shelx_tar'],targetfile.replace(os.path.basename(result['download_file']),os.path.basename(result['shelx_tar'])))
#
#             #return that we are successful
#             return(True)
#
#         else:
#             return(False)
#
#     except:
#
#         logger.exception('Error in CopyToUser')
#         return(False)
#
# def TransferToUI(type,settings,result,trip,logger):
#     """
#     Transfer files using pexpect and rsync to the UI Server.
#
#     type - single,pair,sad,mr
#     """
#
#     logger.debug('TransferToUI type:%s'%type)
#     logger.debug(result)
#
#     #Handle the transfer to ui being turned off
#     if (not settings['xfer_to_ui']):
#         logger.debug("Not transferring files to web server!")
#         return(False)
#
#     #import for decoding
#     import base64
#
#     #set up simpler versions of the host parameters
#     host     = settings['ui_host']
#     port     = settings['ui_port']
#     username = settings['ui_user']
#     password = base64.b64decode(settings['ui_password'])
#
#     #try:
#     #create the log file
#     import paramiko
#     paramiko.util.log_to_file('/tmp/paramiko.log')
#     #create the Transport instance
#     transport = paramiko.Transport((host, port))
#     #connect with username and password
#     transport.connect(username = username, password = password)
#     #establish sftp client
#     sftp = paramiko.SFTPClient.from_transport(transport)
#
#     #now transfer the files
#     if type == 'single':
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'single/')
#         if dest_dir:
#           if result.has_key('summary_short'):
#             if result['summary_short'] != 'None':
#                 counter = 0
#                 while (not os.path.exists(result['summary_short'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_short'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(secret_settings_general['filesystem_delay'])
#                 logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))+")")
#                 sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))
#
#                 if result.has_key('summary_long'):
#                     if result['summary_long'] != 'None':
#                         logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))+")")
#                         sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))
#
#                 if result.has_key('best_plots'):
#                     if result['best_plots'] not in (None,'None','FAILED'):
#                         logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php'])))+")")
#                         sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php'])))
#
#                 if result.has_key('image_raw'):
#                     if result['image_raw'] not in (None,'0'):
#                         #make sure the file is complete
#                         logger.debug("sftp.put("+str(result['image_raw'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))+")")
#                         sftp.put(result['image_raw'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))
#                         time.sleep(2)
#
#                 if result.has_key('image_preds'):
#                     if result['image_preds'] not in  (None,'0'):
#                         #make sure the file is complete
#                         logger.debug("sftp.put("+str(result['image_preds'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif'])))+")")
#                         sftp.put(result['image_preds'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif'])))
#
#         if result.has_key('summary_stac'):
#             if result['summary_stac'] != "None":
#                 logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))+")")
#                 sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))
#
#     elif type == 'single-orphan':
#         dest_dir = os.path.join(settings['ui_user_dir'],'orphans/single/')
#         if result.has_key('summary_short'):
#             if result['summary_short']:
#                 counter = 0
#                 while (not os.path.exists(result['summary_short'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_short'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))+")")
#                 sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))
#
#         if result.has_key('summary_long'):
#             if result['summary_long']:
#                 logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))+")")
#                 sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))
#
#         if result.has_key('summary_stac'):
#             if result['summary_stac'] not in (None,'None','FAILED'):
#                 logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))+")")
#                 sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))
#
#         if result.has_key('best_plots'):
#             if result['best_plots'] not in (None,'None','FAILED'):
#                 logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php'])))+")")
#                 sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php'])))
#
#         if result.has_key('image_raw'):
#             if result['image_raw'] not in (None,'0'):
#                 #make sure the file is complete
#                 while ((time.time() - os.stat(result['image_raw']).st_mtime) < 0.5):
#                     time.sleep(0.5)
#                 logger.debug("sftp.put("+str(result['image_raw'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))+")")
#                 sftp.put(result['image_raw'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))
#
#         if result.has_key('image_preds'):
#             if result['image_preds'] not in (None,'0'):
#                 #make sure the file is complete
#                 while ((time.time() - os.stat(result['image_preds']).st_mtime) < 0.5):
#                     time.sleep(0.5)
#                 logger.debug("sftp.put("+str(result['image_preds'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif'])))+")")
#                 sftp.put(result['image_preds'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif'])))
#
#     ##########################################################################################################################
#     elif type == 'pair':
#         logger.debug('Working on transferring a pair result')
#
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'pair/')
#         logger.debug('Destination: %s'%dest_dir)
#
#         if result.has_key('summary_short'):
#             if (result['summary_short'] not in (None,'None','0')):
#                 counter = 0
#                 while (not os.path.exists(result['summary_short'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_short'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))+")")
#                 sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))
#
#         if result.has_key('summary_long'):
#             if (result['summary_long'] not in (None,'None','0')):
#                 logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'long.php'])))+")")
#                 sftp.put(  result['summary_long'],  os.path.join(dest_dir,'_'.join((str(result['pair_result_id']),'long.php')))  )
#
#         if result.has_key('summary_stac'):
#             logger.debug('STAC summary: %s' % result['summary_stac'])
#             if (result['summary_stac'] not in (None,'None','0')):
#                 logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'stac.php'])))+")")
#                 sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'stac.php'])))
#
#         if result.has_key('best_plots'):
#             if (result['best_plots'] not in (None,'None','0')):
#                 logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php'])))+")")
#                 sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php'])))
#
#         if result.has_key('image_raw_1'):
#             if (result['image_raw_1'] not in (None,'None','0')):
#                 #make sure the file is complete
#                 logger.debug("sftp.put("+str(result['image_raw_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))+")")
#                 sftp.put(result['image_raw_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))
#
#         if result.has_key('image_preds_1'):
#             if (result['image_preds_1'] not in (None,'None','0')):
#                 #make sure the file is complete
#                 logger.debug("sftp.put("+str(result['image_preds_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif'])))+")")
#                 sftp.put(result['image_preds_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif'])))
#
#         if result.has_key('image_raw_2'):
#             if (result['image_raw_2'] not in  (None,'None','0')):
#                 #make sure the file is complete
#                 logger.debug("sftp.put("+str(result['image_raw_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))+")")
#                 sftp.put(result['image_raw_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))
#
#         if result.has_key('image_preds_2'):
#             if (result['image_preds_2'] not in  (None,'None','0')):
#                 #make sure the file is complete
#                 logger.debug("sftp.put("+str(result['image_preds_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif'])))+")")
#                 sftp.put(result['image_preds_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif'])))
#
#     elif type == 'pair-orphan':
#         dest_dir = os.path.join(settings['ui_user_dir'],'orphans/pair/')
#         if result.has_key('summary_short'):
#             if result['summary_short']:
#                 counter = 0
#                 while (not os.path.exists(result['summary_short'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_short'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))+")")
#                 sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))
#
#         if result.has_key('summary_long'):
#             if result['summary_long']:
#                 logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'long.php'])))+")")
#                 sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'long.php'])))
#
#         if result.has_key('summary_stac'):
#             if result['summary_stac'] != "None":
#                 logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))+")")
#                 sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))
#
#         if result.has_key('best_plots'):
#             if result['best_plots']:
#                 logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php'])))+")")
#                 sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php'])))
#
#         if result.has_key('image_raw_1'):
#             if result['image_raw_1'] not in  (None,'0'):
#                 #make sure the file is complete
#                 while ((time.time() - os.stat(result['image_raw_1']).st_mtime) < 0.5):
#                     time.sleep(0.5)
#                 logger.debug("sftp.put("+str(result['image_raw_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))+")")
#                 sftp.put(result['image_raw_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))
#
#         if result.has_key('image_preds_1'):
#             if result['image_preds_1'] not in  (None,'0'):
#                 #make sure the file is complete
#                 while ((time.time() - os.stat(result['image_preds_1']).st_mtime) < 0.5):
#                     time.sleep(0.5)
#                 logger.debug("sftp.put("+str(result['image_preds_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif'])))+")")
#                 sftp.put(result['image_preds_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif'])))
#
#         if result.has_key('image_raw_2'):
#             if result['image_raw_2'] not in  (None,'0'):
#                 #make sure the file is complete
#                 while ((time.time() - os.stat(result['image_raw_2']).st_mtime) < 0.5):
#                     time.sleep(0.5)
#                 logger.debug("sftp.put("+str(result['image_raw_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))+")")
#                 sftp.put(result['image_raw_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))
#
#         if result.has_key('image_preds_2'):
#             if result['image_preds_2'] not in  (None,'0'):
#                 #make sure the file is complete
#                 while ((time.time() - os.stat(result['image_preds_2']).st_mtime) < 0.5):
#                     time.sleep(0.5)
#                 logger.debug("sftp.put("+str(result['image_preds_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif'])))+")")
#                 sftp.put(result['image_preds_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif'])))
#
#     ##########################################################################################################################
#     elif type == 'xia2':
#
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'run/')
#
#         #XIA2 process has succeeded
#         if result['integrate_status'] == 'SUCCESS':
#             #The parsed file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['parsed'])):
#                     logger.debug('Waiting for %s to exist' % result['parsed'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
#                 sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
#             except:
#                 pass
#             #The XIA2 log file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['xia_log'])):
#                     logger.debug('Waiting for %s to exist' % result['xia_log'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
#                 sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
#             except:
#                 logger.exception('Could not transfer xia_log')
#                 logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
#             #The XSCALE log file
#             try:
#                 logger.debug("sftp.put("+str(result['xscale_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))+")")
#                 sftp.put(result['xscale_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))
#             except:
#                 logger.exception('Could not transfer xscale_log')
#             #The SCALA log file
#             try:
#                 logger.debug("sftp.put("+str(result['scala_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scala.log'])))+")")
#                 sftp.put(result['scala_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scale.log'])))
#             except:
#                 logger.exception('Could not transfer scala_log')
#             #The plots file
#             try:
#                 logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
#                 sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
#             except:
#                 logger.exception('Could not transfer plots')
#         #XIA2 process has failed
#         else:
#             #The XIA2 log file
#             logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
#             sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
#
#
#     elif type == 'xia2-orphan':
#         dest_dir = os.path.join(settings['ui_user_dir'],'orphans/run/')
#         #XIA2 process has succeeded
#         if result['integrate_status'] == 'SUCCESS':
#             #The parsed file
#             try:
#                 count = 0
#                 while (not os.path.exists(result['parsed'])):
#                     logger.debug('Waiting for %s to exist' % result['parsed'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
#                 sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
#             except:
#                 logger.exception('Error transferring parsed file')
#             #The XIA2 log file
#             try:
#                 logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
#                 sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
#             except:
#                 logger.exception('Could not transfer xia_log')
#             #The XSCALE log file
#             try:
#                 logger.debug("sftp.put("+str(result['xscale_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))+")")
#                 sftp.put(result['xscale_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))
#             except:
#                 logger.exception('Could not transfer XSCALE log file')
#             #The SCALA log file
#             try:
#                 logger.debug("sftp.put("+str(result['scala_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scala.log'])))+")")
#                 sftp.put(result['scala_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scale.log'])))
#             except:
#                 logger.exception('Could not transfer SCALA log file')
#             #The plots file
#             try:
#                 logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
#                 sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
#             except:
#                 logger.exception('Could not transfer plots file')
#         #XIA2 process has failed
#         else:
#             #The XIA2 log file
#             logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
#             sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
#
#     ###########################################################################################################################################################
#     elif type == 'integrate':
#
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'run/')
#
#         #fastintegrate process has succeeded
#         if result['integrate_status'] in ('SUCCESS','WORKING'):
#             #The parsed file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['parsed'])):
#                     logger.debug('Waiting for %s to exist' % result['parsed'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
#                 sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
#             except:
#                 pass
#             #The long summary file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['summary_long'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_long'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
#                 sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
#             except:
#                 pass
#             #The plots file
#             try:
#                 logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
#                 sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
#             except:
#                 logger.exception('Could not transfer plots')
#         #process has failed
#         else:
#             #The parsed file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['parsed'])):
#                     logger.debug('Waiting for %s to exist' % result['parsed'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
#                 sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
#             except:
#                 pass
#             #The long summary file
#             try:
#                 while (not os.path.exists(result['summary_long'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_long'])
#                     time.sleep(1)
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
#                 sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
#             except:
#                 pass
#
#     ###########################################################################################################################################################
#     elif type == 'integrate-orphan':
#
#         dest_dir = os.path.join(settings['ui_user_dir'],'orphans/run/')
#
#         #fastintegrate process has succeeded
#         if result['integrate_status'] in ('SUCCESS','WORKING'):
#             #The parsed file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['parsed'])):
#                     logger.debug('Waiting for %s to exist' % result['parsed'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
#                 sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
#             except:
#                 pass
#             #The long summary file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['summary_long'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_long'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
#                 sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
#             except:
#                 pass
#             #The plots file
#             try:
#                 logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
#                 sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
#             except:
#                 logger.exception('Could not transfer plots')
#         #process has failed
#         else:
#             #The parsed file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['parsed'])):
#                     logger.debug('Waiting for %s to exist' % result['parsed'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
#                 sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
#             except:
#                 pass
#             #The long summary file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['summary_long'])):
#                     logger.debug('Waiting for %s to exist' % result['summary_long'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
#                 sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
#             except:
#                 pass
#     ##########################################################################################################################
#     elif type == 'smerge':
#
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'merge/')
#
#         #fastintegrate process has succeeded
#         if result['merge_status'] in ('SUCCESS'):
#             #The parsed file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['summary'])):
#                     logger.debug('Waiting for %s to exist' % result['summary'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['summary'])+","+str(os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'short.php'])))+")")
#                 sftp.put(result['summary'],os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'short.php'])))
#             except:
#                 logger.exception('Could not transfer summary')
#             #The long summary file
#             try:
#                 counter = 0
#                 while (not os.path.exists(result['details'])):
#                     logger.debug('Waiting for %s to exist' % result['details'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result['details'])+","+str(os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'long.php'])))+")")
#                 sftp.put(result['details'],os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'long.php'])))
#             except:
#                 logger.exception('Could not transfer details')
#             #The plots file
#             try:
#                 logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'plots.php'])))+")")
#                 sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'plots.php'])))
#             except:
#                 logger.exception('Could not transfer plots')
#
#     ##########################################################################################################################
#     elif type == 'sad':
#
#         #the destination directory
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'structure/')
#
#         #Move file that should always exist
#         #The shelx summary
#         try:
#             counter = 0
#             while (not os.path.exists(result['shelx_html'])):
#                 logger.debug('Waiting for %s to exist' % result['shelx_html'])
#                 time.sleep(1)
#                 counter += 1
#                 if (counter > 100):
#                     break
#             time.sleep(1) #let the filesystem catch up
#             logger.debug("sftp.put("+str(result['shelx_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx.php'])))+")")
#             sftp.put(result['shelx_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx.php'])))
#         except:
#             logger.debug('Error transferring %s to %s' %(result['shelx_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx.php']))))
#
#         #The shelx plots
#         try:
#             logger.debug("sftp.put("+str(result['shelx_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx_plots.php'])))+")")
#             sftp.put(result['shelx_plots'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx_plots.php'])))
#         except:
#             logger.debug('Error transferring %s to %s' %(result['shelx_plots'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx_plots.php']))))
#
#         #The autosol results
#         try:
#             logger.debug("sftp.put("+str(result['autosol_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'autosol.php'])))+")")
#             sftp.put(result['autosol_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'autosol.php'])))
#         except:
#             logger.debug('Error transferring %s to %s' %(result['autosol_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'autosol.php']))))
#
#     ##########################################################################################################################
#     elif type == 'mad':
#
#         #the destination directory
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'structure/')
#
#         #Move file that should always exist
#         #The shelx summary
#         try:
#             counter = 0
#             while (not os.path.exists(result['shelx_html'])):
#                 logger.debug('Waiting for %s to exist' % result['shelx_html'])
#                 time.sleep(1)
#                 counter += 1
#                 if (counter > 100):
#                     break
#             time.sleep(1) #let the filesystem catch up
#             logger.debug("sftp.put("+str(result['shelx_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'shelx.php'])))+")")
#             sftp.put(result['shelx_html'],os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'shelx.php'])))
#         except:
#             logger.debug('Error transferring %s to %s' %(result['shelx_html'],os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'shelx.php']))))
#
#         #The shelx plots
#         try:
#             logger.debug("sftp.put("+str(result['shelx_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'shelx_plots.php'])))+")")
#             sftp.put(result['shelx_plots'],os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'shelx_plots.php'])))
#         except:
#             logger.debug('Error transferring %s to %s' %(result['shelx_plots'],os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'shelx_plots.php']))))
#
#         #The autosol results
#         try:
#             logger.debug("sftp.put("+str(result['autosol_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'autosol.php'])))+")")
#             sftp.put(result['autosol_html'],os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'autosol.php'])))
#         except:
#             logger.debug('Error transferring %s to %s' %(result['autosol_html'],os.path.join(dest_dir,'_'.join([str(result['mad_result_id']),'autosol.php']))))
#
#     ##########################################################################################################################
#     elif type == 'mr':
#
#         #the destination directory
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'structure/')
#
#         #Move file that should always exist
#         #The summary
#         try:
#             counter = 0
#             while (not os.path.exists(result['summary_html'])):
#                 logger.debug('Waiting for %s to exist' % result['summary_html'])
#                 time.sleep(1)
#                 counter += 1
#                 if (counter > 100):
#                     break
#             time.sleep(1) #let the filesystem catch up
#             logger.debug("sftp.put("+str(result['summary_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['mr_result_id']),'mr.php'])))+")")
#             sftp.put(result['summary_html'],os.path.join(dest_dir,'_'.join([str(result['mr_result_id']),'mr.php'])))
#         except:
#             logger.debug('Error transferring %s to %s' %(result['summary_html'],os.path.join(dest_dir,'_'.join([str(result['mr_result_id']),'mr.php']))))
#
#     ##########################################################################################################################
#     elif type == 'stats':
#
#         #the destination directory
#         dest_dir = os.path.join(settings["ui_user_dir"],trip["username"],str(trip["trip_id"]),"run/")
#
#         #Move file that should always exist
#         files = [("cell_sum","stats_cellsum.php"),
#                  ("xtriage_sum","stats_xtriagesum.php"),
#                  ("xtriage_plots","stats_xtriageplots.php"),
#                  ("molrep_sum","stats_molrepsum.php"),
#                  ("molrep_img","stats_molrep.jpg"),
#                  ("precession_sum","stats_precession.php"),
#                  ("precession_img0","stats_pp0.jpg"),
#                  ("precession_img1","stats_pp1.jpg"),
#                  ("precession_img2","stats_pp2.jpg")]
#
#         #The summary
#         for src,dest in files:
#             try:
#                 counter = 0
#                 while (not os.path.exists(result[src])):
#                     logger.debug('Waiting for %s to exist' % result[src])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result[src])+","+str(os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))+")")
#                 sftp.put(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))
#             except:
#                 logger.debug('Error transferring %s to %s' %(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest]))))
#
#
#     elif type == 'stats-orphan':
#
#         #the destination directory
#         dest_dir = os.path.join(settings["ui_user_dir"],"orphans/run/")
#
#         #Move file that should always exist
#         files = [("cell_sum","stats_cellsum.php"),
#                  ("xtriage_sum","stats_xtriagesum.php"),
#                  ("xtriage_plots","stats_xtriageplots.php"),
#                  ("molrep_sum","stats_molrepsum.php"),
#                  ("molrep_img","stats_molrep.jpg"),
#                  ("precession_sum","stats_precession.php"),
#                  ("precession_img0","pp0.jpg"),
#                  ("precession_img1","pp1.jpg"),
#                  ("precession_img2","pp2.jpg")]
#
#         #The summary
#         for src,dest in files:
#             try:
#                 counter = 0
#                 while (not os.path.exists(result[src])):
#                     logger.debug('Waiting for %s to exist' % result[src])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 time.sleep(1) #let the filesystem catch up
#                 logger.debug("sftp.put("+str(result[src])+","+str(os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))+")")
#                 sftp.put(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))
#             except:
#                 logger.debug('Error transferring %s to %s' %(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest]))))
#     ##########################################################################################################################
#     elif type == 'download':
#         dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'download/')
#         if result.has_key('archive'):
#             if result['archive']:
#                 counter = 0
#                 while (not os.path.exists(result['archive'])):
#                     logger.debug('Waiting for %s to exist' % result['archive'])
#                     time.sleep(1)
#                     counter += 1
#                     if (counter > 100):
#                         break
#                 logger.debug("sftp.put("+str(result['archive'])+","+str(os.path.join(dest_dir,os.path.basename(result['archive'])))+")")
#                 sftp.put(result['archive'],os.path.join(dest_dir,os.path.basename(result['archive'])))
#
#     ##########################################################################################################################
#     #close out the connection
#     sftp.close()
#     transport.close()
#     return(True)
#     """
#     except:
#         #close out the connection
#         sftp.close()
#         transport.close()
#         return(False)
#    """

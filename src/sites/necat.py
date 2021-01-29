"""
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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

# Site
SITE = 'NECAT'

#ID = "NECAT_T"
#ID = ("NECAT_T", 'NECAT_E')
ID = ("NECAT_C", 'NECAT_E')

#ID = ("T")
#BEAMLINE="T"

# The secrets file - do not put in github repo!
SECRETS = "sites.secrets_necat"
# Copy the secrets attribute to the local scope
# Do not remove unless you know what you are doing!
read_secrets(SECRETS, sys.modules[__name__])

# X-ray source characteristics
# Keyed to ID
BEAM_INFO = {
    "NECAT_C": {# Detector distance limits
                "DETECTOR_DISTANCE_MIN": 150.0,
                "DETECTOR_DISTANCE_MAX": 1000.0,
                # goniometer limit
                #"DELTA_OMEGA_MIN": 0.05,
                "DIFFRACTOMETER_OSC_MIN": 0.05,
                # shortest exposure time
                #"EXPOSURE_TIME_MIN": 0.05,
                "DETECTOR_TIME_MIN": 0.05,
                # Flux of the beam
                #"BEAM_FLUX":1.5E12,
                "BEAM_FLUX":5E12,
                # Max size of the beam in mm
                "BEAM_SIZE_X":0.07,
                "BEAM_SIZE_Y":0.03,
                # Shape of the beam - ellipse, rectangle
                "BEAM_SHAPE":"ellipse",
                # Shape of the attenuated beam - circle or rectangle
                "BEAM_APERTURE_SHAPE":"circle",
                # Gaussian description of the beam for raddose
                #"BEAM_GAUSS_X":0.03,
                #"BEAM_GAUSS_Y":0.01,
                # Beam center calibration
                'BEAM_CENTER_DATE' : "2020-09-20",
                # Beamcenter equation coefficients (b, m1, m2, m3)
                #'BEAM_CENTER_X' : (163.2757684023,
                #                 0.0003178917,
                #                 -5.0236657815e-06,
                #                5.8164218288e-09),
                #'BEAM_CENTER_Y' : (155.1904879862,
                #                 -0.0014631216,
                #                 8.60559283424e-07,
                #                 -2.5709929645e-10)
                #'BEAM_CENTER_X' : (217.89545788464195,
                #                -0.0095051886470180359,
                #                 4.5313419256785272e-05,
                #                -1.3544716298203249e-07),
                #'BEAM_CENTER_Y' : (222.69061623307075,
                #                 0.008371144274918689,
                #                 -6.6628778965267953e-05,
                #                 2.4131282311413717e-07)
                #'BEAM_CENTER_X' : (217.55864605,
                #                   -0.00199770779024,
                #                   1.16082561287e-06,
                #                   1.40862457675e-10),
                #'BEAM_CENTER_Y' : (225.078687367,
                #                   0.00130328024604,
                #                   -1.8128376189e-06,
                #                   1.3400233455e-09),
                #'BEAM_CENTER_X' : (217.354843551,
                #                    0.00196378671817,
                #                    -2.87273346253e-05,
                #                     1.10320981196e-07,
                #                    -2.05961860935e-10,
                #  ),
                #'BEAM_CENTER_Y' : (224.477413744,
                #                  0.0148281008073,
                #                  -0.000106235126328,
                #                  3.65071163955e-07,
                #                  -6.24373960251e-10
                #  ),
                #'BEAM_CENTER_X' : (217.700907892,
                #                   -0.00434379751074,
                #                   5.94813802004e-06,
                #                   -2.65697095373e-09,
                #
                #  ),
                #'BEAM_CENTER_Y' : (225.169717095,
                #                   0.0010451099971,
                #                   -1.19410360145e-06,
                #                   9.46106520609e-10,
                #  ),
                'BEAM_CENTER_X' : (165.09158876278738,
                                   -0.0029460905038690313,
                                   3.9960841330504456e-06,
                                   -1.6974268198852025e-09,
                  ),
                'BEAM_CENTER_Y' : (155.31742108875466,
                                   -0.000263232786706418,
                                   1.4696942274946312e-06,
                                   -4.749970048666142e-10,
                  ),
                
		},
		
		
    "NECAT_E": {# Detector distance limits
                "DETECTOR_DISTANCE_MIN": 150.0,
                "DETECTOR_DISTANCE_MAX": 1000.0,
                # goniometer limit
                #"DELTA_OMEGA_MIN": 0.05,
                "DIFFRACTOMETER_OSC_MIN": 0.05,
                # shortest exposure time
                #"EXPOSURE_TIME_MIN": 0.05,
                "DETECTOR_TIME_MIN": 0.05,
                # Flux of the beam
                #"BEAM_FLUX":1.5E12,
                "BEAM_FLUX":5E12,
                # Max size of the beam in mm
                "BEAM_SIZE_X":0.05,
                "BEAM_SIZE_Y":0.02,
                # Shape of the beam - ellipse, rectangle
                "BEAM_SHAPE":"ellipse",
                # Shape of the attenuated beam - circle or rectangle
                "BEAM_APERTURE_SHAPE":"circle",
                # Gaussian description of the beam for raddose
                #"BEAM_GAUSS_X":0.03,
                #"BEAM_GAUSS_Y":0.01,
                # Beam center calibration
                'BEAM_CENTER_DATE' : "2020-02-04",
                # Beamcenter equation coefficients (b, m1, m2, m3)
                'BEAM_CENTER_X' : (165.14276287567738,
                                   -0.0014361166886983285,
                                   -1.728236304090641e-06,
                                   3.2731939791152326e-09,
                 ),
                'BEAM_CENTER_Y' : (154.64591768967471,
                                   -0.002128702601888507,
                                   1.6853682723685666e-06,
                                   -6.0437162045712206e-10,
                 ),
                #
               # 
                #'BEAM_CENTER_X' : (165.515302163,
                #                   -0.00428244190922,
                #                   2.97724490799e-06,
                #                   7.48384066914e-10),
                #'BEAM_CENTER_Y' : (154.638326268,
                #                   -0.000168035275208,
                #                   -2.07093201008e-06,
                #                   1.46530757459e-09)
                #'BEAM_CENTER_X' : (164.72070756207401,
                #                   -0.0013409358206944552,
                #                   -2.29343913762685e-06,
                #                    3.4872750035666701e-09),
                #'BEAM_CENTER_Y' : (154.79725866966157,
                #                   -0.0015094308731870999,
                #                   7.3597978380100895e-07,
                #                   -1.4267298732928363e-10)
                #'BEAM_CENTER_X' : (164.72070756207401,
                #                   -0.0013409358206944552,
                #                   -2.29343913762685e-06,
                #                    3.4872750035666701e-09),
                #'BEAM_CENTER_Y' : (154.79725866966157,
                #                   -0.0015094308731870999,
                #                   7.3597978380100895e-07,
                #                   -1.4267298732928363e-10)
                #'BEAM_CENTER_DATE' : "2017-3-02",
                #'BEAM_CENTER_X' : (163.89684278768254,
                #                 -0.0015633263872817393,
                #                 -2.5624797406798966e-06,
                #                 3.9573203673686396e-09),
                #'BEAM_CENTER_Y' : (154.56630526168037,
                #                 -0.0004545100450374418,
                #                 -1.1274954741267088e-06,
                #                 8.4937063175024929e-10)
                #'BEAM_CENTER_X' : (163.2757684023,
                #                 0.0003178917,
                #                 -5.0236657815e-06,
                #                 5.8164218288e-09),
                #'BEAM_CENTER_Y' : (155.1904879862,
                #                 -0.0014631216,
                #                 8.60559283424e-07,
                #                 -2.5709929645e-10)
                },
             }
# Copy E to T for testing
#BEAM_INFO.update({"NECAT_T": BEAM_INFO["NECAT_E"]})

################ Logging #################
# Linux should be /var/log/
#LOGFILE_DIR = "/share/apps/necat/tmp2"
LOGFILE_DIR = "/gpfs6/users/necat/rapd2/logs"
LOG_LEVEL = 50

################ Directories ################
# Where files are exchanged between plugins and control
EXCHANGE_DIR = "/gpfs6/users/necat/rapd2/exchange_dir"
# Where files from UI are uploaded - should be visible by launch instance
#UPLOAD_DIR = "/gpfs5/users/necat/rapd/uranium/trunk/uploads"

################# Lock file locations so only one instance can run. False if no locking.################
# Launcher Manager to sort out where to send jobs
#LAUNCHER_MANAGER_LOCK_FILE = "/tmp/rapd2/lock/launcher_manager.lock"
# Launcher settings
LAUNCHER_LOCK_FILE = "/tmp/rapd2/lock/launcher.lock"
# dataset gatherer lock
GATHERER_LOCK_FILE = "/tmp/rapd2/lock/gatherer.lock"
# Control process settings
CONTROL_LOCK_FILE = "/tmp/rapd2/lock/rapd_core.lock"


################# Adapters################
# RAPD cluster adapter location
CLUSTER_ADAPTER = "sites.cluster.necat"

#Directories to look for launcher adapters
# Queried in order, so a shell_simple.py in src/sites/launcher_adapters will override
# the same file in launch/launcher_adapters
RAPD_LAUNCHER_ADAPTER_DIRECTORIES = ("launch.launcher_adapters",
                                     "sites.launcher_adapters")
# Directories to look for rapd plugins
# Queried in order, so a rapd_agent_echo.py in src/sites/agents will override
# the same file in src/agents
RAPD_PLUGIN_DIRECTORIES = ("sites.plugins",
                           "plugins")

# rapd.python path
RAPD_PYTHON_PATH = '/gpfs6/users/necat/Jon/Programs/RAPD2/RAPD/bin/rapd2.python'

# Method RAPD uses to track groups
#   uid -- the uid of data root directory corresponds to session.group_id
#GROUP_ID = "uid"
GROUP_ID = None

# The field name in groups collection that matches the property described in GROUP_ID
#   uidNumber
#GROUP_ID_FIELD = "uidNumber"

# Data gatherer settings
# The data gatherer for this site, in the src/sites/gatherers directory
GATHERER = "necat.py"
#GATHERER = "necat_t.py"

# Control settings
# Port for core process to listen on
#CORE_PORT = 50001
#CONTROL_PORT = 50001

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
#DETECTOR = "NECAT_DECTRIS_EIGER16M"
DETECTOR = False
#DETECTOR_SUFFIX = ".img"
DETECTOR_SUFFIX = ".cbf"
# Keyed to ID
DETECTORS = {"NECAT_C":("NECAT_DECTRIS_EIGER2_16M", ""),
             #"NECAT_C":("NECAT_DECTRIS_PILATUS6MF", ""),
             "NECAT_E":("NECAT_DECTRIS_EIGER16M", ""),
             "NECAT_T":("NECAT_DECTRIS_EIGER16M", "")}

# Monitor for collected images
#IMAGE_MONITOR = "sites.image_monitors.necat_e"
#IMAGE_MONITOR = "sites.monitors.image_monitors.necat_e"
IMAGE_MONITOR = "monitors.image_monitors.redis_image_monitor"

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
    "/gpfs5/users/necat/rapd/uranium/trunk/test_data",
    "/gpfs5/users/necat/phi_dfa_1/in",
    "/gpfs5/users/necat/phi_dfa_2/in",
    "/gpfs5/users/necat/phi_raster_snap/in",
    "/gpfs5/users/necat/phi_rastersnap_scan_data",
    "/gpfs5/users/necat/phi_dfa_scan_data",
    "/gpfs5/users/necat/phi_ova_scan_data",
    "/epu/rdma/gpfs5/users/necat/phii_dfa_1/in",
    "/epu/rdma/gpfs5/users/necat/phii_dfa_2/in",
    "/epu/rdma/gpfs5/users/necat/phii_raster_snap/in",
    "/epu/rdma/gpfs5/users/necat/phii_rastersnap_scan_data",
    "/epu/rdma/gpfs5/users/necat/phii_dfa_scan_data",
    "/epu/rdma/gpfs5/users/necat/phii_ova_scan_data",
    "/epu/rdma/gpfs5/users/necat/rapd/uranium/trunk/test_data",
    "/epu2/rdma/gpfs5/users/necat/phii_dfa_1/in",
    "/epu2/rdma/gpfs5/users/necat/phii_dfa_2/in",
    "/epu2/rdma/gpfs5/users/necat/phii_raster_snap/in",
    "/epu2/rdma/gpfs5/users/necat/phii_rastersnap_scan_data",
    "/epu2/rdma/gpfs5/users/necat/phii_dfa_scan_data",
    "/epu2/rdma/gpfs5/users/necat/phii_ova_scan_data",
    "/epu2/rdma/gpfs5/users/necat/rapd/uranium/trunk/test_data",
    )
# Images collected containing the following string will be ignored
IMAGE_IGNORE_STRINGS = ("ignore",
                        "priming_shot",
                        )

# If image is not present, look in long term storage location.
# Runs function detector.get_alt_path() to get new path
# Set to False if not using.
#ALT_IMAGE_LOCATION = True

# If processing images in NFS shared RAMDISK with different path 
# than long-term storage that was passed in. Check if they exist.
ALT_IMAGE_LOCATION = True
# Name of class in detector file that runs as server.
# Set to False if not using server 
ALT_IMAGE_SERVER_NAME = 'FileLocation'

# Monitor for collected run information
#RUN_MONITOR = "sites.monitors.run_monitors.necat_e"
RUN_MONITOR = "monitors.run_monitors.redis_run_monitor"

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
#SITE_ADAPTER = False
# Running in a cluster configuration - True || False
#SITE_ADAPTER_REDIS_CLUSTER = False
SITE_ADAPTER_REDIS_CLUSTER = REDIS_CLUSTER

# For connecting to the remote access system fr the site
REMOTE_ADAPTER = "sites.site_adapters.necat_remote"     # file name prefix for adapter in src/
REMOTE_ADAPTER_REDIS_CLUSTER = REDIS_CLUSTER

##
## Aggregators
## Be extra careful when modifying
CONTROL_DATABASE_SETTINGS = {
    # MongoDB
    "CONTROL_DATABASE":     CONTROL_DATABASE,
    "DATABASE_STRING":      MONGO_CONNECTION_STRING,
    "DATABASE_HOST":        DB_HOST,
    "DATABASE_USER":        DB_USER,
    "DATABASE_PASSWORD":    DB_PASSWORD,
    #"DATABASE_NAME_DATA":   "rapd_data",
    #"DATABASE_NAME_USERS":  "rapd_users",
    #"DATABASE_NAME_CLOUD":  "rapd_cloud",

    # Redis
    "REDIS_CONNECTION":     REDIS_CONNECTION,
    "REDIS_HOST":           REDIS_HOST,
    "REDIS_PORT":           REDIS_PORT,
    "REDIS_DB":             REDIS_DB,
    "REDIS_PASSWORD":       REDIS_PASSWORD,
    #"REDIS_SENTINEL_HOSTS": SENTINEL_HOSTS,
    "REDIS_MASTER_NAME":    REDIS_MASTER_NAME,
}

LAUNCHER_SETTINGS = {
    "LAUNCHER_SPECIFICATIONS":LAUNCHER_SPECIFICATIONS,
    "LOCK_FILE":LAUNCHER_LOCK_FILE,
    "RAPD_LAUNCHER_ADAPTER_DIRECTORIES":RAPD_LAUNCHER_ADAPTER_DIRECTORIES
}

LAUNCH_SETTINGS = {
    "RAPD_PLUGIN_DIRECTORIES":RAPD_PLUGIN_DIRECTORIES,
    "LAUNCHER_SPECIFICATIONS":LAUNCHER_SPECIFICATIONS,
}

IMAGE_MONITOR_SETTINGS = {
    "REDIS_CONNECTION":     REDIS_CONNECTION,
    #"REDIS_SENTINEL_HOSTS": SENTINEL_HOSTS,
    "REDIS_MASTER_NAME":    REDIS_MASTER_NAME,
    "REDIS_HOST":           REDIS_HOST,
    "REDIS_PORT":           REDIS_PORT,
    "REDIS_DB":             REDIS_DB,
}

RUN_MONITOR_SETTINGS = {
    "REDIS_CONNECTION":     REDIS_CONNECTION,
    #"REDIS_SENTINEL_HOSTS": SENTINEL_HOSTS,
    "REDIS_MASTER_NAME" :   REDIS_MASTER_NAME,
    "REDIS_HOST":           REDIS_HOST,
    "REDIS_PORT":           REDIS_PORT,
    "REDIS_DB":             REDIS_DB
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
        #"UI_HOST":UI_HOST,
        #"UI_PORT":UI_PORT,
        #"UI_USER":UI_USER,
        #"UI_PASSWORD":UI_PASSWORD,
        #"UPLOAD_DIR":UPLOAD_DIR
        }

#SITE_ADAPTER_SETTINGS = {"ID":ID,
#                         "REDIS_HOST":SITE_REDIS_IP,
#                         "REDIS_PORT":SITE_REDIS_PORT,
#                         "REDIS_DB":SITE_REDIS_DB}
SITE_ADAPTER_SETTINGS = {"NECAT_E": {"ID":                   ID,
                                     "REDIS_CONNECTION":     E_REDIS_CONNECTION,
                                     "REDIS_HOST":           E_REDIS_IP,
                                     "REDIS_PORT":           E_REDIS_PORT,
                                     "REDIS_DB":             E_REDIS_DB,
                                     "REDIS_PASSWORD":       E_REDIS_PASSWORD,
                                     "REDIS_SENTINEL_HOSTS": E_SENTINEL_HOSTS,
                                     "REDIS_MASTER_NAME":    E_REDIS_MASTER_NAME,},
                         "NECAT_C": {"ID":                   ID,
                                     "REDIS_CONNECTION":     C_REDIS_CONNECTION,
                                     "REDIS_HOST":           C_REDIS_IP,
                                     "REDIS_PORT":           C_REDIS_PORT,
                                     "REDIS_DB":             C_REDIS_DB,
                                     "REDIS_PASSWORD":       C_REDIS_PASSWORD,
                                     "REDIS_SENTINEL_HOSTS": C_SENTINEL_HOSTS,
                                     "REDIS_MASTER_NAME":    C_REDIS_MASTER_NAME,},
                           }

REMOTE_ADAPTER_SETTINGS = {
    "ID":                      ID,
    "MONGO_CONNECTION_STRING": MONGO_CONNECTION_STRING,
    'REDIS_CONNECTION':        REDIS_CONNECTION,
    #"REDIS_SENTINEL_HOSTS":    SENTINEL_HOSTS,
    "REDIS_MASTER_NAME":       REDIS_MASTER_NAME,
    "REDIS_HOST":              REDIS_HOST,
    "REDIS_PORT":              REDIS_PORT,
    "REDIS_DB":                REDIS_DB,
}

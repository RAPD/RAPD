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

# Site
SITE = 'NECAT'

#ID = "NECAT_T"
ID = ("NECAT_T", 'NECAT_E')

#ID = ("T")
#BEAMLINE="T"

# The secrets file - do not put in github repo!
SECRETS = "sites.secrets_necat_t"
# Copy the secrets attribute to the local scope
# Do not remove unless you know what you are doing!
read_secrets(SECRETS, sys.modules[__name__])

# X-ray source characteristics
# Keyed to ID
BEAM_INFO = {
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
                "BEAM_FLUX":1.5E12,
                # Size of the beam in mm
                "BEAM_SIZE_X":0.05,
                "BEAM_SIZE_Y":0.02,
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
                },
    #"NECAT_T": BEAM_INFO["NECAT_E"],
             }
BEAM_INFO.update({"NECAT_T": BEAM_INFO["NECAT_E"]})
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

# RAPD cluster adapter location
CLUSTER_ADAPTER = "sites.cluster.necat"

# Launcher Manager to sort out where to send jobs
LAUNCHER_MANAGER_LOCK_FILE = "/tmp/rapd2/lock/launcher_manager.lock"

# Launcher settings
LAUNCHER_LOCK_FILE = "/tmp/rapd2/lock/launcher.lock"
# Launcher to send jobs to
# The value should be the key of the launcher to select in LAUNCHER_SPECIFICATIONS
#LAUNCHER_TARGET = 1
# Directories to look for launcher adapters
RAPD_LAUNCHER_ADAPTER_DIRECTORIES = ("launch.launcher_adapters",
                                     "sites.launcher_adapters")
# Queried in order, so a shell_simple.py in src/sites/launcher_adapters will override
# the same file in launch/launcher_adapters

# Data gatherer settings
# The data gatherer for this site, in the src/sites/gatherers directory
#GATHERER = "necat.py"
GATHERER = "necat_t.py"
GATHERER_LOCK_FILE = "/tmp/rapd2/lock/gatherer.lock"

# Directories to look for rapd plugins
RAPD_PLUGIN_DIRECTORIES = ("sites.plugins",
                           "plugins")

# Queried in order, so a rapd_agent_echo.py in src/sites/agents will override
# the same file in src/agents

# Control process settings
# Process is a singleton? The file to lock to. False if no locking.
CONTROL_LOCK_FILE = "/tmp/rapd2/lock/rapd_core.lock"

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
    "/gpfs5/users/necat/rapd/uranium/trunk/test_data",
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
    #"LAUNCHER_REGISTER":LAUNCHER_REGISTER,
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

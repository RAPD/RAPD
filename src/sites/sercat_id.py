"""Site description for SERCAT ID beamline"""

__license__ = """
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

# Standard imports
import sys

# RAPD imports
from utils.site import read_secrets

# Site ID
ID = "SERCAT_ID"
DESCRIPTION = ""

# The secrets file - do not put in github repo!
SECRETS_FILE = "sites.secrets_sercat_id"

# Copy the secrets attribute to the local scope
# Do not remove unless you know what you are doing!
read_secrets(SECRETS_FILE, sys.modules[__name__])

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
CONTROL_LOCK_FILE = "/tmp/lock/rapd_core.lock"
# Where files from UI are uploaded - should be visible by launch instance
UPLOAD_DIR = "/gpfs5/users/necat/rapd/uranium/trunk/uploads"

# Control settings
# Database to use for control operations. Options: "mysql"
CONTROL_DATABASE = "mongodb"
CONTROL_DATABASE_DATA = "rapd_data"
CONTROL_DATABASE_USERS = "rapd_users"
CONTROL_DATABASE_CLOUD = "rapd_cloud"
# Redis databse
# Running in a cluster configuration - True || False
CONTROL_REDIS_CLUSTER = False

# Detector settings
# Must have a file in detectors that is all lowercase of this string
DETECTOR = "SERCAT_RAYONIX_MX300HS"
# DETECTOR_SUFFIX = ""

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
IMAGE_MONITOR = "sites.image_monitors.redis_image_monitor"
# Redis databse
# Running in a cluster configuration - True || False
IMAGE_MONITOR_REDIS_CLUSTER = CONTROL_REDIS_CLUSTER
# Images collected into following directories will be ignored
IMAGE_IGNORE_DIRECTORIES = ()
# Images collected containing the following string will be ignored
IMAGE_IGNORE_STRINGS = ("ignore", )

# Monitor for collected run information
RUN_MONITOR = "sites.run_monitors.necat_e"
# Expected time limit for a run to be collected in minutes (0 = forever)
RUN_WINDOW = 60
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
                          "SENTINEL_HOST" : IMAGE_MONITOR_SENTINEL_HOSTS,
                          "SENTINEL_PORT" : IMAGE_MONITOR_SENTINEL_PORT,
                          "REDIS_MASTER_NAME" : IMAGE_MONITOR_REDIS_MASTER_NAME}

RUN_MONITOR_SETTINGS = {"REDIS_HOST" : RUN_MONITOR_REDIS_HOST,
                        "REDIS_PORT" : RUN_MONITOR_REDIS_PORT,
                        "REDIS_CLUSTER" : RUN_MONITOR_REDIS_CLUSTER,
                        "SENTINEL_HOST" : RUN_MONITOR_SENTINEL_HOSTS,
                        "SENTINEL_PORT" : RUN_MONITOR_SENTINEL_PORT,
                        "REDIS_MASTER_NAME" : RUN_MONITOR_REDIS_MASTER_NAME}

CLOUD_MONITOR_SETTINGS = {
    "CLOUD_HANDLER_DIRECTORIES" : CLOUD_HANDLER_DIRECTORIES,
#    "LAUNCHER_IDS" : LAUNCHER_IDS,
    "DETECTOR_SUFFIX" : DETECTOR[1],
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

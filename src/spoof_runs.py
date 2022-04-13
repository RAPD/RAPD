import os, sys
import importlib
import json
import time

from multiprocessing import Queue, Process
import logging
import logging.handlers

from utils.processes import local_subprocess, mp_pool
#from utils.xutils import convert_unicode
import utils.xutils as xutils
import utils.log

# Path to first image in dataset
filename = "/gpfs2/users/mdanderson/tainer_E_5319/images/aleem/runs/NE50_15/NE50_15_1_000001.cbf"
# site_tag
site_tag = "NECAT_E"
# Total number of images to process
total = '50'


# Set up logging
logger = utils.log.get_logger(logfile_dir="/gpfs6/users/necat/Jon/RAPD_test/Output",
                              logfile_id="rapd_int",
                              level=1,
                              #console=commandline_args.test
                              console=False)

# Setup cluster
import sites.necat as site
from utils.modules import load_module
#cluster_launcher = load_module(site.CLUSTER_ADAPTER)
#launcher = cluster_launcher.process_cluster
detector = load_module("sites.detectors.%s"%site.DETECTORS.get(site_tag)[0].lower())

# Setup redis
redis_database = importlib.import_module('database.redis_adapter')
#redis_database = redis_database.Database(settings=site.CONTROL_DATABASE_SETTINGS)
red = redis_database.Database(settings=site.CONTROL_DATABASE_SETTINGS)
#redis = redis_database.connect_to_redis()

# Have to create "run_info_E" dict that is normally created by RAPD1.rapd_console.ConsoleRediMonitor
# runid,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp
header = detector.read_header(input_file=filename)
if not header.get("energy", False):
    # Convert wavelength to E
    #header["energy"] = str((header.get("wavelength")/(6.626e-34 * 3.0e8) * 1.602176634e-19 ))
    header["energy"] = str(12398.0/float(header.get("wavelength")))

sep = "_"
l = [str(header.get("run_number")), 
     str(header.get("image_number")), 
     total,
     str(header.get("distance")),
     str(round(float(header.get("energy")), 2)),
     str(header.get("transmission")),
     str(header.get("osc_start")),
     str(header.get("osc_range")),
     str(round(float(header.get("time")),2)),
     str(header.get("date")),
     ]
cur_run = json.dumps(sep.join(l))
# lpush run info to redis
red.lpush("run_info_%s"%site_tag[-1], cur_run)
time.sleep(3)

#### The directory comes from beamline redis and that is not correct so it won't launch run!!

"""
red.lpush('images_collected:%s'%site_tag, filename)
for i in range(2):
    nr = int(filename[filename.rfind('_')+1:filename.rfind('.')])
    new_nr = str(nr+1).zfill(6)
    filename = "%s%s.cbf" %(filename[:filename.rfind('_')+1], new_nr)
    red.lpush('images_collected:%s'%site_tag, filename)
    time.sleep(0.05)
"""


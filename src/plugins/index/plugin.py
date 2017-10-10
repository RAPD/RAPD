"""
An autoindex & strategy rapd_plugin
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2017, Cornell University
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
__created__ = "2009-07-14"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

# This is an active rapd plugin
RAPD_PLUGIN = True
# This plugin's types
DATA_TYPE = "MX"
PLUGIN_TYPE = "INDEX"
PLUGIN_SUBTYPE = "CORE"
# A unique ID for this handler (uuid.uuid1().hex[:4])
ID = "3b34"
# Version of this plugin
VERSION = "2.0.0"

# Standard imports
from bson.objectid import ObjectId
from collections import OrderedDict
from distutils.spawn import find_executable
import functools
# import glob
import json
import logging
from multiprocessing import Process, Event
from multiprocessing import Queue as mp_Queue
from Queue import Queue
from threading import Thread
import numpy
import os
from pprint import pprint
import re
import shutil
import signal
import subprocess
import sys
import time
import importlib
import stat

# RAPD imports
import info
import plugins.subcontractors.parse as Parse
import plugins.subcontractors.best as best
import plugins.subcontractors.labelit as labelit
from plugins.subcontractors.xoalign import RunXOalign
import utils.credits as rcredits
from utils.r_numbers import try_int, try_float
#from utils.communicate import rapd_send
import utils.exceptions as exceptions
import utils.global_vars as global_vars
from utils.processes import local_subprocess, mp_pool
import utils.xutils as xutils

DETECTOR_TO_BEST = {
    "ADSC": "q315",
    "ADSC-Q315": "q315",
    "ADSC-HF4M": "hf4m",
    "Pilatus-6M": "pilatus6m",
    "PILATUS": "pilatus6m",
    "raxis":"raxis",
    "rayonix_mx225": "mar225",
    "rayonix_mx300": "mx300",
    "rayonix_mx300hs": "mx300hs",
    "mar300": "mar300",
    "ray300": "ray300",
    "Dectris Eiger 9M": "eiger9m",
    "Eiger-9M": "eiger9m",
    "Eiger-16M": "eiger16m",
    }

VERSIONS = {
    "best": (
        "Version 3.2.0",
        "Version 3.4.4"
    ),
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    ),
    "ipmosflm": (
        "version 7.2.1",
    ),
    "labelit": (),
    "raddose": (),
}

class RapdPlugin(Process):
    """
    command format
    {
        "command":"INDEX+STRATEGY",
        "directories":
            {
                "work":""                           # Where to perform the work
            },
        "header1":{},                               # Image information
        ["header2":{},]                             # 2nd image information
        "site_parameters":{}                        # Site data
        "preferences":{}                            # Settings for calculations
        "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    # Connection to redis
    redis = None

    # For testing individual modules (Will not run in Test mode on cluster!! Can be set at end of
    # __init__.)
    test = False

    # Removes junk files and directories at end. (Will still clean on cluster!! Can be set at end of
    #  __init__.)
    clean = False

    # Runs in RAM (slightly faster), but difficult to debug.
    ram = False

    # Will not use RAM if self.cluster_use=True since runs would be on separate nodes. Slower
    # (>10%).
    cluster_use = False

    # Switch for verbose
    verbose = True

    # Number of Labelit iterations to run.
    iterations = 6

    # This is where I place my overall folder settings.
    working_dir = False
    #auto_summary = False
    labelit_log = {}
    labelit_results = {}
    labelit_proc = False
    #labelit_summary = False
    labelit_failed = False
    labelit_cell = False
    labelit_sym = False
    distl_log = []
    distl_queue = Queue()
    distl_results = []
    distl_summary = False
    raddose_file = False
    raddose_results = {}
    raddose_summary = False
    best_log = []
    best_results = False
    best_summary = False
    best1_summary = False
    best_summary_long = False
    best_anom_log = []
    best_anom_results = False
    best_anom_summary = False
    best1_anom_summary = False
    best_anom_summary_long = False
    best_failed = False
    best_anom_failed = False
    rerun_best = False
    mosflm_strat_log = []
    mosflm_strat_anom_log = []
    mosflm_strat_results = {}
    mosflm_strat_anom_results = {}
    mosflm_strat_summary = False
    mosflm_strat1_summary = False
    mosflm_strat_summary_long = False
    mosflm_strat_anom_summary = False
    mosflm_strat1_anom_summary = False
    mosflm_strat_anom_summary_long = False
    plots = {}
    # Labelit settings
    index_number = False
    ignore_user_SG = False
    pseudotrans = False
    # Raddose settings
    volume = False
    calc_num_residues = False
    # Mosflm settings
    prev_sg = False
    # Extra features for BEST
    high_dose = False
    crystal_life = None
    iso_B = False
    # Dicts for running the Queues
    jobs = {}

    # The results of the plugin
    results = {"_id":str(ObjectId())}

    def __init__(self, site, command, tprint=False, logger=False):
        """
        Initialize the plugin

        Keyword arguments
        site -- full site settings
        command -- dict of all information for this plugin to run
        """

        # For debugging
        # pprint(command)
        # sys.exit()

        # Save the start time
        self.start_time= time.time()

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(*args, **kwargs):
                """Dummy function"""
                pass
            self.tprint = func

        # Some logging
        self.logger.info(site)
        self.logger.info(command)
        #pprint(command)

        # Store passed-in variables
        self.site = site
        self.command = command

        # Setting up data input
        self.setup = self.command["directories"]
        self.header = self.command["header1"]
        self.header2 = self.command.get("header2", False)
        # get the default preferences and update what was sent in...
        self.preferences = info.DEFAULT_PREFERENCES#.update(self.command.get("preferences", {}))
        self.preferences.update(self.command.pop("preferences", {}))
        self.site_parameters = self.command.get("site_parameters", False)

        # Assumes that Core sent job if present. Overrides values for clean and test from top.
        if self.site_parameters != False:
            self.gui = True
            self.test = False
            self.clean = False
        else:
            # If running from command line, site_parameters is not in there. Needed for BEST.
            if self.site:
                self.site_parameters = self.site.BEAM_INFO.get(
                    xutils.get_site(self.header['fullname'], False)[1])
            else:
                self.site_parameters = self.preferences.get("site_parameters", False)
                # Sets settings so I can view the HTML output on my machine (not in the RAPD GUI),
                # and does not send results to database.
                self.gui = False

        # Setup the appropriate launcher
        if self.cluster_use:
            cluster_launcher = xutils.load_cluster_adapter(self)
            self.launcher = cluster_launcher.process_cluster
            # Based on the command, pick a batch queue on the cluster. Added to input kwargs
            self.batch_queue = {'batch_queue': cluster_launcher.check_queue(self.command["command"])}
            self.kill_job = cluster_launcher.kill_job
        else:
            self.launcher = local_subprocess
            self.batch_queue = {}
            self.kill_job = xutils.kill_children

        # Setup a multiprocessing.Pool for running jobs (8 will be full speed)
        # If set to 1, then everything is run sequentially
        #self.pool = mp_pool(self.preferences.get('nproc', 8))

        # Set timer for distl. "False" will disable.
        if self.header2:
            self.distl_timer = 60
        else:
            self.distl_timer = 30

        # Set strategy timer. "False" disables.
        self.strategy_timer = 60

        # Set timer for XOAlign. "False" will disable.
        self.xoalign_timer = 30

        # Turns on multiprocessing for everything
        # Turns on all iterations of Labelit running at once, sorts out highest symmetry solution,
        # then continues...(much better!!)
        self.multiproc = self.preferences.get("multiprocessing", True)

	    # Set for Eisenberg peptide work.
        self.sample_type = self.preferences.get("sample_type", "Protein").lower()
        if self.sample_type == "peptide":
            self.peptide = True
        else:
            self.peptide = False

        # BEST is default and if it fails Mosflm results are shown as backup.
        # Setting to 'mosflm' will force it to show Mosflm results regardless.
        self.strategy = self.preferences.get("strategy_type", "best")

        # Check to see if XOALign should run.
        if self.header.has_key("mk3_phi") and self.header.has_key("mk3_kappa"):
            self.minikappa = True
        else:
            self.minikappa = False

        # Check to see if multi-crystal strategy is requested.
        if self.preferences.get("reference_data_id") in (None, 0):
            self.multicrystalstrat = False
        else:
            self.multicrystalstrat = True
            self.strategy = "mosflm"

        # Settings for all programs
        #self.beamline = self.header.get("beamline")
        self.time = self.header.get("time", 0.2)
        self.wavelength = self.header.get("wavelength")
        self.transmission = self.header.get("transmission", 10.0)
        #self.transmission = self.header.get("transmission", 0.1)
        # self.aperture = str(self.header.get("md2_aperture"))
        self.spacegroup = self.preferences.get("spacegroup", False)
        #self.flux = str(self.header.get("flux", '3E10'))
        self.solvent_content = self.preferences.get("solvent_content", 0.55)

        Process.__init__(self, name="AutoindexingStrategy")
        # self.start() is called by the initiator of this script

    def construct_results(self):
        """Create the self.results dict"""

        # Container for actual results
        self.results["results"] = {}

        # Copy over details of this run
        self.results["command"] = self.command #.get("command")
        self.results["header1"] = self.header
        self.results["header2"] = self.header2

        # Temporary cover for missing basename
        for version in (1, 2):
            if self.results["header%d" % version]:
                self.results["header%d" % version]["basename"] = \
                    os.path.basename(self.results["header%d" % version]["fullname"])
        self.results["preferences"] = self.preferences

        # Describe the process
        self.results["process"] = self.command.get("process", {})
        # Status is now 1 (starting)
        self.results["process"]["status"] = 1
        # Process type is plugin
        self.results["process"]["type"] = "plugin"
        # Assign the text representation for this result
        if not self.header2:
            self.results["process"]["repr"] = os.path.basename(self.header["fullname"])
        else:
            self.results["process"]["repr"] = re.sub(r"\?\?*", "?", self.header["image_template"])\
                .replace("?", "%d+%d" % (self.header["image_number"], self.header2["image_number"]))

        # Describe plugin
        self.results["plugin"] = {
            "data_type":DATA_TYPE,
            "type":PLUGIN_TYPE,
            "subtype":PLUGIN_SUBTYPE,
            "id":ID,
            "version":VERSION
        }

    def run(self):
        """
        Convoluted path of modules to run.
        """

        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::run")

        self.tprint(arg=0, level="progress")
        # Check if h5 file is input and convert to cbf's.
        if self.header["fullname"][-3:] == ".h5":
            if self.convert_images() == False:
                # If conversion fails, kill the job.
                self.postprocess()

        self.preprocess()

        self.tprint(arg="\nStarting indexing procedures", level=98, color="blue")

        if self.minikappa:
            self.process_xoalign()
        else:

            # Run Labelit
            self.start_labelit()

            # Sorts labelit results by highest symmetry.
            self.labelit_sort()
          
            # Run Distl
            self.process_distl()

            # If there is a solution, then calculate a strategy.
            if self.labelit_failed == False:
                if self.multiproc == False:
                    self.postprocess_distl()
                self.preprocess_raddose()
                self.process_raddose()
                self.process_strategy()
                self.run_queue()

                # Get the distl_results
                if self.multiproc:
                    self.postprocess_distl()

            # Pass back results, and cleanup.
            self.postprocess()

    def connect_to_redis(self):
        """Connect to the redis instance"""
        # Create a pool connection
        redis_database = importlib.import_module('database.rapd_redis_adapter')

        self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        if self.site.CONTROL_DATABASE_SETTINGS['REDIS_CONNECTION'] == 'pool':
            # For a Redis pool connection
            self.redis = self.redis_database.connect_redis_pool()
        else:
            # For a Redis sentinal connection
            self.redis = self.redis_database.connect_redis_manager_HA()

    def preprocess(self):
        """
        Setup the working dir in the RAM and save the dir where the results will go at the end.
        """
        self.logger.debug("AutoindexingStrategy::preprocess")

        # Construct the results
        self.construct_results()
        # pprint(self.results)

        # Let everyone know we are working on this
        if self.preferences.get("run_mode") == "server":
            if not self.redis:
                self.connect_to_redis()
            self.logger.debug("Sending back on redis")
            json_results = json.dumps(self.results)
            self.redis.lpush("RAPD_RESULTS", json_results)
            self.redis.publish("RAPD_RESULTS", json_results)

        # Determine detector vendortype
        self.vendortype = xutils.get_vendortype(self.header)
        self.dest_dir = self.setup.get("work")
        if self.test or self.cluster_use:
            self.working_dir = self.dest_dir
        elif self.ram:
            self.working_dir = "/dev/shm/%s" % self.dest_dir[1:]
        else:
            self.working_dir = self.dest_dir
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)

        # Add flux info to header
        #self.header =

        # Setup event for job control on cluster (Only works at NE-CAT using DRMAA for
        # job submission)
        if self.cluster_use:
            self.running = Event()
            self.running.set()

        # Check for dependency problems
        self.check_dependencies()

    def check_dependencies(self):
        """Make sure dependencies are all available"""

        # If no best, switch to mosflm for strategy
        if self.strategy == "best":
            if not find_executable("best"):
                self.tprint("Executable for best is not present, using Mosflm for strategy",
                            level=30,
                            color="red")
                self.strategy = "mosflm"

        # If no gnuplot turn off printing
        if self.preferences.get("show_plots", True) and (not self.preferences.get("json", False)):
            if not find_executable("gnuplot"):
                self.tprint("\nExecutable for gnuplot is not present, turning off plotting",
                            level=30,
                            color="red")
                self.preferences["show_plots"] = False

        # If no labelit.index, dead in the water
        if not find_executable("labelit.index"):
            self.tprint("Executable for labelit.index is not present, exiting",
                        level=30,
                        color="red")
            self.results["process"]["status"] = -1
            self.results["error"] = "Executable for labelit.index is not present"
            self.write_json(self.results)
            raise exceptions.MissingExecutableException("labelit.index")

        # If no mosflm, dead in the water
        if not find_executable("ipmosflm"):
            self.tprint("Executable for mosflm is not present, exiting",
                        level=30,
                        color="red")
            self.results["process"]["status"] = -1
            self.results["error"] = "Executable for mosflm is not present"
            self.write_json(self.results)
            raise exceptions.MissingExecutableException("ipmosflm")

        # If no raddose, should be OK
        if not find_executable("raddose"):
            self.tprint("\nExecutable for raddose is not present - will continue",
                        level=30,
                        color="red")

    def preprocess_raddose(self):
        """
        Create the raddose.com file which will run in process_raddose. Several beamline specific
        entries for flux and aperture size passed in from rapd_site.py
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::preprocess_raddose")

        # try:
        #print self.site_parameters
        beam_size_x = self.header.get('x_beam_size', self.site_parameters.get('BEAM_SIZE_X', False))
        beam_size_y = self.header.get('y_beam_size', self.site_parameters.get('BEAM_SIZE_Y', False))
        #beam_size_x = self.site_parameters.get('BEAM_SIZE_X', False)
        #beam_size_y = self.site_parameters.get('BEAM_SIZE_Y', False)
        gauss_x = self.site_parameters.get('BEAM_GAUSS_X', False)
        gauss_y = self.site_parameters.get('BEAM_GAUSS_Y', False)
        flux = self.header.get('flux', self.site_parameters.get('BEAM_FLUX', 1E10 ))

        # Get unit cell
        #cell = self.get_labelit_cell_sym()
        #nres = xutils.calcTotResNumber(self, self.volume)
        nres = xutils.calc_tot_res_number(self.volume, self.sample_type, self.solvent_content)

        # Adding these typically does not change the Best strategy much, if it at all.
        patm = False
        satm = False
        if self.sample_type == "ribosome":
            crystal_size_x = 1.0
            crystal_size_y = 0.5
            crystal_size_z = 0.5
        else:
            # crystal dimensions (default 0.1 x 0.1 x 0.1 from rapd_site.py)
            crystal_size_x = self.preferences.get("crystal_size_x", 100.0)/1000.0
            crystal_size_y = self.preferences.get("crystal_size_y", 100.0)/1000.0
            crystal_size_z = self.preferences.get("crystal_size_z", 100.0)/1000.0

        self.raddose_file = os.path.join(self.labelit_dir, "raddose.com")
        raddose = open(self.raddose_file, "w+")
        setup = '#!/bin/sh\n'
        setup += "raddose << EOF\n"
        if beam_size_x and beam_size_y:
            setup += "BEAM %s %s\n" % (beam_size_x, beam_size_y)
        # Full-width-half-max of the beam (for non-uniform beams)
        if gauss_x and gauss_y:
            setup += "GAUSS %.2f %.2f\n" % (gauss_x, gauss_y)
        setup += "IMAGES 1\n"
        setup += "PHOSEC %d\n" % flux
        #setup += "EXPOSURE %.2f\n" % self.time
        setup += "EXPOSURE 1.0\n" # set to 1s so dose result is Gy per S.
        if self.labelit_cell:
            setup += "CELL %s %s %s %s %s %s\n" % (self.labelit_cell[0],
                                                   self.labelit_cell[1],
                                                   self.labelit_cell[2],
                                                   self.labelit_cell[3],
                                                   self.labelit_cell[4],
                                                   self.labelit_cell[5])
        else:
            self.logger.debug("Could not get unit cell from bestfile.par")

        # Set default solvent content based on sample type. User can override.
        if self.solvent_content == 0.55:
            if self.sample_type == "protein":
                setup += "SOLVENT 0.55\n"
            else:
                setup += "SOLVENT 0.64\n"
        else:
            setup += "SOLVENT %.2f\n"%self.solvent_content
        # Sets crystal dimensions. Input from dict (0.1 x 0.1 x 0.1 mm), but user can override.
        if crystal_size_x and crystal_size_y and crystal_size_z:
            setup += "CRYSTAL %.1f %.1f %.1f\n" % (crystal_size_x, crystal_size_y, crystal_size_z)
        if self.wavelength:
            setup += "WAVELENGTH %.4f\n" % self.wavelength
        setup += "NMON 1\n"
        if self.sample_type == "protein":
            setup += "NRES %d\n" % nres
        elif self.sample_type == "dna":
            setup += "NDNA %d\n" % nres
        else:
            setup += "NRNA %d\n" % nres
        if patm:
            setup += "PATM %d\n" % patm
        if satm:
            setup += "SATM %d\n" % satm
        setup += "END\nEOF\n"
        raddose.writelines(setup)
        raddose.close()
        os.chmod(self.raddose_file, stat.S_IRWXU)

        # except:
            # self.logger.exception("**ERROR in preprocess_raddose**")

    def start_labelit(self):
        """
        Initiate Labelit runs.
        """

        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::runLabelit")

        #self.tprint(arg="  Starting Labelit runs", level=99, color="white", newline=False)
        self.tprint(arg="  Starting Labelit runs", level=99, color="white")

        # try:
        # Setup queue for getting labelit log and results in labelit_sort.
        self.labelitQueue = Queue()

        params = {}
        params["test"] = self.test
        params["launcher"] = self.launcher
        params["verbose"] = self.verbose
        params["batch_queue"] = self.batch_queue
        params["vendortype"] = self.vendortype
        params['kill_job'] = self.kill_job
        if self.working_dir == self.dest_dir:
            command = self.command
        else:
            command = self.command.copy()
            command["directories"]["work"] = self.working_dir
        command['preferences'] = self.preferences

        # Launch labelit
        Thread(target=RunLabelit,
              args=(command,
                    self.labelitQueue,
                    params,
                    self.tprint,
                    self.logger)).start()
        #self.labelit_proc.start()

    def process_xds_bg(self):
        """
        Calculate the BKGINIT.cbf for the background calc on the Pilatus. This is
        used in BEST.
        Gleb recommended this but it does not appear to make much difference except take longer.
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::process_xds_bg")

        try:
            name = str(self.header.get("fullname"))
            temp = name[name.rfind("_")+1:name.rfind(".")]
            new_name = name.replace(name[name.rfind("_")+1:name.rfind(".")], len(temp)*"?")
            #range = str(int(temp))+" "+str(int(temp))
            command = "JOB=XYCORR INIT\n"
            #xutils.calcXDSbc Does not exist anymore
            command += xutils.calcXDSbc(self)
            command += "DETECTOR_DISTANCE=%s\n" % self.header.get("distance")
            command += "OSCILLATION_RANGE=%s\n" % self.header.get("osc_range")
            command += "X-RAY_WAVELENGTH=%.4f\n" % self.wavelength
            command += "NAME_TEMPLATE_OF_DATA_FRAMES=%s\n" % new_name
            #command += "BACKGROUND_RANGE="+range+"\n"
            #command += "DATA_RANGE="+range+"\n"
            command += "BACKGROUND_RANGE=%s %s\n" % (int(temp), int(temp))
            command += "DATA_RANGE=%s %s\n" % (int(temp), int(temp))
            command += "DIRECTION_OF_DETECTOR_Y-AXIS=0.0 1.0 0.0\n"
            command += "DETECTOR=PILATUS         MINIMUM_VALID_PIXEL_VALUE=0  OVERLOAD=1048500\n"
            command += "SENSOR_THICKNESS=0.32        !SILICON=-1.0\n"
            command += "NX=2463 NY=2527 QX=0.172  QY=0.172  !PILATUS 6M\n"
            command += "DIRECTION_OF_DETECTOR_X-AXIS= 1.0 0.0 0.0\n"
            command += "TRUSTED_REGION=0.0 1.05 !Relative radii limiting trusted detector region\n"
            command += "UNTRUSTED_RECTANGLE= 487  493     0 2528\n"
            command += "UNTRUSTED_RECTANGLE= 981  987     0 2528\n"
            command += "UNTRUSTED_RECTANGLE=1475 1481     0 2528\n"
            command += "UNTRUSTED_RECTANGLE=1969 1975     0 2528\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464   195  211\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464   407  423\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464   619  635\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464   831  847\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464  1043 1059\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464  1255 1271\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464  1467 1483\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464  1679 1695\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464  1891 1907\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464  2103 2119\n"
            command += "UNTRUSTED_RECTANGLE=   0 2464  2315 2331\n"
            command += "ROTATION_AXIS= 1.0 0.0 0.0\n"
            command += "INCIDENT_BEAM_DIRECTION=0.0 0.0 1.0\n"
            command += "FRACTION_OF_POLARIZATION=0.99 !default=0.5 for unpolarized beam\n"
            command += "POLARIZATION_PLANE_NORMAL= 0.0 1.0 0.0\n"
            f = open("XDS.INP", "w")
            f.writelines(command)
            f.close()
            Process(target=xutils.processLocal, args=("xds_par", self.logger)).start()

        except:
            self.logger.exception("**Error in process_xds_bg.**")

    def process_distl(self):
        """
        Setup Distl for multiprocessing if enabled.
        """
        if self.verbose and self.logger:
            self.logger.debug('AutoindexingStrategy::process_distl')

        self.distl_output = []
        l = ["", "2"]
        f = 1
        if self.header2:
            f = 2
        for i in range(0, f):
            if self.test:
                job = Thread(target=local_subprocess,
                             kwargs={"command": 'ls'})
            else:
                command = "distl.signal_strength %s" % eval("self.header%s" % l[i]).get("fullname")
                job = Thread(target=local_subprocess,
                             kwargs={"command": command,
                                     "result_queue": self.distl_queue,
                                     "logfile": os.path.join(os.getcwd(), "distl%s.log" % i),
                                   },)
            job.start()
            self.distl_output.append(job)

    def process_raddose(self):
        """
        Run Raddose.
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::process_raddose")

        # Setup queue for results
        queue = Queue()
        # Run the command
        inp_kwargs = {'command': self.raddose_file,
                      'result_queue': queue}
        Thread(target=local_subprocess, kwargs=inp_kwargs).start()
        # Save the results
        raddose = Parse.ParseOutputRaddose(queue.get()["stdout"].splitlines())
        self.raddose_results = {"raddose_results" : raddose}

    def check_best(self, iteration=0, best_version="3.2.0"):
        """
        Run all the Best runs at the same time.
        Reduce resolution limit and rerun Mosflm to calculate new files.
        """

        self.logger.debug("check_best")

        # try:
        self.folders_strategy(iteration)
        #print os.getcwd()
        if iteration != 0:
            f = '%s/%s/%s_res%s'%(self.labelit_dir, iteration, self.index_number, iteration)
            if self.test == False:
                temp = []
                orig = os.path.join(self.labelit_dir, self.index_number)
                with open(orig, "r") as raw:
                    for x, line in enumerate(raw):
                        temp.append(line)
                        #if line.count("ipmosflm"):
                        #    newline = line.replace(self.index_number, '%s/%s/%s'%(self.labelit_dir, iteration, self.index_number))
                        #    temp.remove(line)
                        #    temp.insert(x, newline)
                        if line.startswith("RESOLUTION"):
                            temp.remove(line)
                            temp.append("RESOLUTION %s\n" % str(float(line.split()[1]) + iteration))
                new = open(f, "w")
                new.writelines(temp)
                new.close()
                os.chmod(f, stat.S_IRWXU)
                #subprocess.Popen(f).wait()
                local_subprocess(command=f)
        self.process_best(iteration, best_version)

    def process_best(self, iteration=0, best_version="3.2.0", runbefore=False):
        """
        Construct the Best command and run. Passes back dict with PID:anom.

        Best versions known 3.2.0, 3.4.4
        """

        self.logger.debug("AutoindexingStrategy::process_best %s", best_version)

        # Get image numbers
        try:
            counter_depth = self.header["image_template"].count("?")
        except KeyError:
            raise Exception("Header information missing image_template")

        # Look for the correct hkl file
        for test_depth in (3, 4, 5, 6):
            test_file = "%s_%s.hkl" % (self.index_number, ("%0"+str(test_depth)+"d") % self.header["image_number"])
            if os.path.exists(test_file):
                counter_depth = test_depth
                break

        image_number_format = "%0"+str(counter_depth)+"d"
        image_number = [image_number_format % self.header["image_number"],]
        if self.header2:
            image_number.append(image_number_format % self.header2["image_number"])

        # Tell Best if two-theta is being used.
        if self.header.get("twotheta", 0.0) != 0.0:
            xutils.fix_bestfile()

        # If Raddose failed, here are the defaults.
        dose = self.raddose_results["raddose_results"].get('dose', 100000)
        #exp_dose_lim = self.raddose_results.get("raddose_results", 300).get('exp dose limit', 300)

        # Set how many frames a crystal will last at current exposure time.
        # Warning in the GUI if flux is too high
        #self.crystal_life = str(int(float(exp_dose_lim) / self.time))
        #if self.crystal_life == '0':
        #    self.crystal_life = '1'
        
        # Adjust dose for ribosome crystals.
        if self.sample_type == 'ribosome':
            dose = 500001

        # Put together the command for labelit.index
        best_detector = DETECTOR_TO_BEST.get(self.header.get("detector"), False)
        if not best_detector:
            self.tprint(arg="RAPD does not have a BEST definition for your detector type %s"
                        % self.header.get("detector"),
                        level=30,
                        color="red")
            return
        command = "best -f %s" % best_detector

        # Binning
        if str(self.header.get('binning')) == '2x2':
            command += '-2x'
        command += " -t %.2f" % self.time
        #if self.high_dose:
        #    command += ' -t 1.0'
        #else:
        #    command += " -t %.2f" % self.time
        command += ' -e %s -sh %.1f' % (self.preferences.get('best_complexity', 'none'),\
                                        self.preferences.get('shape', 2.0))
        if self.preferences.get('aimed_res') != 0.0:
            command += ' -r %.1f' % self.preferences.get('aimed_res')
        if best_version >= "3.4":
            command += ' -Trans %.1f' % self.transmission
        # Set minimum rotation width per frame. Different for PAR and CCD detectors.
        if self.site_parameters.get("DIFFRACTOMETER_OSC_MIN", False):
            command += ' -w %s' % self.site_parameters.get("DIFFRACTOMETER_OSC_MIN")
        # Set minimum exposure time per frame.
        if self.site_parameters.get("DETECTOR_TIME_MIN", False):
            command += ' -M %s' % self.site_parameters.get("DETECTOR_TIME_MIN")
        # Set min and max detector distance
        if best_version >= "3.4" and self.site_parameters.get("DETECTOR_DISTANCE_MAX", False):
            command += ' -DIS_MAX %s' % self.site_parameters.get("DETECTOR_DISTANCE_MAX") 
        if best_version >= "3.4" and self.site_parameters.get("DETECTOR_DISTANCE_MIN", False):
            command += ' -DIS_MIN %s'% self.site_parameters.get("DETECTOR_DISTANCE_MIN")
        # Fix bug in BEST for PAR detectors. Use the cumulative completeness of 99% instead of all
        # bin.
        #if self.vendortype in ('Pilatus-6M', 'ADSC-HF4M'):
        if best_detector in ('pilatus6m', 'hf4m', 'eiger9m', 'eiger16m'):
            if best_version != "3.2.0":
                command += " -low never"
            command += " -su %.1f" % self.preferences.get("susceptibility", 1.0)
        else:
            # Set the I/sigI to 0.75 like Mosflm res in Labelit.
            command += ' -i2s 0.75 -su 1.5'
        # set dose  and limit, else set time
        if best_version >= "3.4":
            #command += ' -GpS %s -DMAX 30000000'%dose
            command += ' -GpS %s'%dose
        else:
            command += ' -T 185'
        if runbefore:
            command += ' -p %s %s' % (runbefore[0], runbefore[1])
        command1 = command
        command1 += ' -a -o best_anom.plt -dna best_anom.xml'
        command += ' -o best.plt -dna best.xml'
        # print image_number, image_number[0]
        end = ' -mos bestfile.dat bestfile.par %s_%s.hkl ' % (self.index_number, image_number[0])
        # print end
        """
        if self.pilatus:
          if os.path.exists(os.path.join(self.working_dir,'BKGINIT.cbf')):
            end = ' -MXDS bestfile.par BKGINIT.cbf %s_%s.hkl ' % (self.index_number,image_number[0])
        """
        if self.header2:
            end += '%s_%s.hkl' % (self.index_number, image_number[1])
        command += end
        command1 += end

        d = {}
        jobs = {}
        l = [(command, ''), (command1, '_anom')]
        st = 0
        end1 = 2
        if runbefore:
            st = runbefore[2]
            end1 = runbefore[3]

        # print l
        for i in range(st, end1):
            log = os.path.join(os.getcwd(), "best%s.log" % l[i][1])
            if self.verbose and self.logger:
                self.logger.debug(l[i][0])
            # Save the path of the log
            d.update({'log'+l[i][1]:log})
            if self.test == False:
                inp_kwargs = {'command': l[i][0],
                              'logfile': log}
                # Update batch queue info if using a compute cluster
                inp_kwargs.update(self.batch_queue)

                #Launch the job
                jobs[str(i)] = Thread(target=self.launcher,
                                       kwargs=inp_kwargs)
                jobs[str(i)].start()

        # Check if Best should rerun since original Best strategy is too long for Pilatus using
        # correct start and end from plots. (Way around bug in BEST.)
        if best_version > "3.4" and self.test == False:
            if runbefore == False:
                counter = 2
                while counter > 0:
                    for job in jobs.keys():
                        if jobs[job].is_alive() == False:
                            del jobs[job]
                            start, _ = self.find_best_strat(d['log'+l[int(job)][1]].replace('log', 'plt'))
                            if start != False:
                                pass
                                # self.process_best(iteration, (start, ran, int(job), int(job)+1))
                            counter -= 1
                    time.sleep(0.1)

    def process_mosflm(self):
        """
        Creates Mosflm executable for running strategy and run. Passes back dict with PID:logfile.
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::process_mosflm")

        #try:
        # Change to the correct directory
        xutils.folders2(self, self.labelit_dir)
        l = [("mosflm_strat", "", ""), ("mosflm_strat_anom", "_anom", "ANOMALOUS")]
        # Opens file from Labelit/Mosflm autoindexing and edit it to run a strategy.
        mosflm_rot = self.preferences.get("mosflm_rot", 0.0)
        mosflm_seg = self.preferences.get("mosflm_seg", 1)
        mosflm_st = self.preferences.get("mosflm_start", 0.0)
        mosflm_end = self.preferences.get("mosflm_end", 360.0)

        # Does the user request a start or end range?
        range1 = False
        if mosflm_st != 0.0:
            range1 = True
        if mosflm_end != 360.0:
            range1 = True
        if range1:
            if mosflm_rot == 0.0:
                # mosflm_rot = str(360/float(xutils.symopsSG(self,xutils.getMosflmSG(self))))
                #mosflm_rot = str(360/float(xutils.symopsSG(self, xutils.getLabelitCell(self, "sym"))))
                #mosflm_rot = str(360/float(xutils.symopsSG(self, self.get_labelit_cell("sym"))))
                mosflm_rot = 360.0/(xutils.sg_to_nsymops(self.labelit_sym))
        # Save info from previous data collections.
        if self.multicrystalstrat:
            ref_data = self.preferences.get("reference_data")
            if self.spacegroup == False:
                self.spacegroup = ref_data[0][-1]
                # LG should have been checked in labelit_sort
                xutils.fixMosflmSG(self)
                # For posting in summary
                self.prev_sg = True
        else:
            ref_data = False

        # Run twice for regular and anomalous strategies.
        for i in range(0, 2):
            #shutil.copy(self.index_number, l[i][0])
            temp = []
            # Read the Mosflm input file from Labelit and use only the top part.
            #for x, line in enumerate(open(l[i][0], "r").readlines()):
            #for x, line in enumerate(open(self.index_number, "r").readlines()):
            with open(os.path.join(self.labelit_dir, self.index_number), "r") as raw:
                for x, line in enumerate(raw):
                    temp.append(line)
                    if line.count("ipmosflm"):
                        newline = line.replace('> %s.out'%self.index_number,'')
                        temp.remove(line)
                        temp.insert(x, newline)
                    if line.count("FINDSPOTS"):
                        im = line.split()[-1]
                    if line.startswith("MATRIX"):
                        fi = x

            # Load the image as per Andrew Leslie for Mosflm bug.
            new_line = "IMAGE %s\nLOAD\nGO\n" % im

            # New lines for strategy calculation
            if ref_data:
                for x in range(len(ref_data)):
                    new_line += "MATRIX %s\nSTRATEGY start %s end %s PARTS %s\nGO\n" %  d(ref_data[x][0], ref_data[x][1], ref_data[x][2], len(ref_data)+1)
                new_line += "MATRIX %s.mat\n"%self.index_number
            if range1:
                new_line += "STRATEGY START %.2f END %.2f\nGO\n" % (mosflm_st, mosflm_end)
                new_line += "ROTATE %.2f SEGMENTS %d %s\n" % (mosflm_rot, mosflm_seg, l[i][2])
            else:
                if mosflm_rot == 0.0:
                    new_line += "STRATEGY AUTO %s\n"%l[i][2]
                elif mosflm_seg != "1":
                    new_line += "STRATEGY AUTO ROTATE %.2f SEGMENTS %d %s\n" % (mosflm_rot, mosflm_seg, l[i][2])
                else:
                    new_line += "STRATEGY AUTO ROTATE %.2f %s\n" % (mosflm_rot, l[i][2])
            new_line += "GO\nSTATS\nEXIT\neof\n"
            inp = os.path.join(self.labelit_dir, l[i][0])
            log = inp+".out"
            if self.test == False:
                new = open(inp, "w")
                new.writelines(temp[:fi+1])
                new.writelines(new_line)
                new.close()
                
                os.chmod(inp, stat.S_IRWXU)
                inp_kwargs = {'command': inp,
                              'logfile': log}
                # Update batch queue info if using a compute cluster
                inp_kwargs.update(self.batch_queue)
                
                #Launch the job
                Process(target=self.launcher,
                        kwargs=inp_kwargs).start()

    def check_best_detector(self, detector):
        """Check that the detector we need is in the BEST configuration file"""

        # print "check_best_detector", detector

        best_executable = subprocess.check_output(["which", "best"])
        detector_info = os.path.join(os.path.dirname(best_executable),
                                     "detector-inf.dat")

        # Read the detector info file to see if the detector is in it
        lines = open(detector_info, "r").readlines()
        found = False
        for line in lines:
            # print line.rstrip()
            if line.startswith(detector+" "):
                found = True
                break
            elif line.startswith("end"):
                break

        if not found:
            self.tprint(arg="Detector %s missing from the BEST detector information file" %
                        detector,
                        level=30,
                        color="red")
            self.tprint(arg="Add \"%s\" \n to file %s \n to get BEST running" %
                        (info.BEST_INFO[detector], detector_info),
                        level=30,
                        color="red")

    def process_strategy(self, iteration=False):
        """
        Initiate all the strategy runs using multiprocessing.

        Keyword arguments
        iteration -- (default False)
        """

        self.logger.debug("process_strategy")
        # print "process_strategy", iteration

        if iteration:
            st = iteration
            end = iteration+1
        else:
            st = 0
            end = 5
            if self.strategy == "mosflm":
                st = 4
            else:
                # Only check best info if we are going to use best
                # Get the Best version for this machine
                best_version = xutils.get_best_version()
                # Make sure that the BEST install has the detector
                self.check_best_detector(DETECTOR_TO_BEST.get(self.header.get("detector"), None))
            
            if self.multiproc == False:
                end = st+1

        for i in range(st, end):
            # Print for 1st BEST run
            if i == 1:
                self.tprint(arg="  Starting BEST runs", level=98, color="white")
            # Run Mosflm for strategy
            if i == 4:
                self.tprint(arg="  Starting Mosflm runs", level=98, color="white")
                job = Process(target=self.process_mosflm, name="mosflm%s" % i)
            # Run BEST
            else:
                # Reduces resolution and reruns Mosflm to calc new files, then runs Best.
                job = Process(target=self.check_best, name="best%s" % i, args=(i, best_version))
            job.start()
            self.jobs[str(i)] = job

    def process_xoalign(self):
        """
        Run XOalign using rapd_plugin_xoalign.py
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::process_xoalign")

        try:
            params = {}
            params["xoalign_timer"] = self.xoalign_timer
            params["test"] = self.test
            params["gui"] = self.gui
            params["dir"] = self.dest_dir
            params["clean"] = self.clean
            params["verbose"] = self.verbose
            Process(target=RunXOalign, args=(self.input, params, self.logger)).start()

        except:
            self.logger.exception("**ERROR in process_xoalign**")

    def postprocess_distl(self):
        """
        Send Distl log to parsing and make sure it didn't fail. Save output dict.
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::postprocess_distl")

        # try:
        timer = 0
        while len(self.distl_output) != 0:
            for job in self.distl_output:
                if job.is_alive() == False:
                    self.distl_output.remove(job)
            time.sleep(0.2)
            timer += 0.2
            if self.verbose and self.logger:
                number = round(timer % 1, 1)
                if number in (0.0, 1.0):
                    pass
                    # print "Waiting for Distl to finish %s seconds" % timer
            if self.distl_timer:
                if timer >= self.distl_timer:
                    #job.terminate()
                    self.distl_output.remove(job)
                    self.distl_log.append("Distl timed out\n")
                    if self.verbose and self.logger:
                        self.tprint(arg="Distl timed out", level=30, color="red")
                        self.logger.error("Distl timed out.")

        # Count frames
        if self.header2:
            frame_count = 2
        else:
            frame_count = 1

        # Parse out distl results for the frame(s)
        for frame_number in range(frame_count):
            log = self.distl_queue.get()['stdout'].splitlines()
            # Read in the log
            #log = open("distl%s.log" % frame_number, "r").readlines()
            # Store the logs in one
            self.distl_log.extend(log)
            # Parse and put the distl results into storage
            self.distl_results.append(Parse.ParseOutputDistl(self, log))

        # Debugging
        # pprint(self.distl_results)

        # Print DISTL results to commandline - verbose only
        self.tprint(arg="\nDISTL analysis results", level=30, color="blue")
        if len(self.distl_results) == 2:
            self.tprint(arg="  %21s  %8s  %8s" % ("", "image 1", "image 2"), level=30, color="white")
            format_string = "  %21s: %8s  %8s"
            default_result = ["-", "-"]
        else:
            format_string = "  %21s: %s"
            default_result = ["-",]

        distl_labels = OrderedDict([
            ("spots_total", "Total Spots"),
            ("spots_in_res", "Spots in Resolution"),
            ("spots_good_bragg", "Good Bragg Spots"),
            ("overloads", "Overloaded Spots"),
            ("distl_res", "DISTL Resolution"),
            ("labelit_res", "Labelit Resolution"),
            ("max_cell", "Max Cell"),
            ("ice_rings", "Ice Rings"),
            ("signal_min", "Min Signal Strength"),
            ("signal_max", "Max Signal Strength"),
            ("signal_mean", "Mean Intensity Signal"),
            ])

        for key, val in distl_labels.iteritems():
            result = []
            for distl_result in self.distl_results:
                result.append(distl_result.get(key))
            if not result:
                result = default_result
            vals = tuple([val] + result)
            self.tprint(arg=format_string % vals, level=30, color="white")

    def error_best_post(self, iteration, error, anom=False):
        """
        Post error to proper log in postprocess_best.
        """
        if self.verbose and self.logger:
            self.logger.debug('error_best_post')
        # try:
        if anom:
            j = ['ANOM', '_anom']
        else:
            j = ['', '']
        if self.verbose and self.logger:
            self.logger.debug(error)
        if iteration >= 3:
            line = 'After 3 tries, Best %s failed. Will run Mosflm %s strategy'%(j[0], j[0])
            if self.verbose and self.logger:
                self.logger.debug(line)
        else:
            iteration += 1
            back_counter = 4 - iteration
            line = 'Error in Best %s strategy. Retrying Best %s more time(s)'%(j[0], back_counter)
            if self.verbose and self.logger:
                self.logger.debug(line)
        eval('self.best%s_log'%j[1]).append('\n%s' % line)

    def postprocess_best(self, inp, runbefore=False):
        """
        Send Best log to parsing and save output dict. Error check the results and
        rerun if neccessary.

        Keyword arguments
        inp --
        runbefore -- (default False)
        """

        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::postprocess_best")

        # print inp

        # Read in log files
        xml = "None"
        anom = False
        if inp.count("anom"):
            anom = True
        log = open(inp, "r").readlines()

        if os.path.exists(inp.replace("log", "xml")):
            xml = open(inp.replace("log", "xml"), "r").readlines()
        iteration = os.path.dirname(inp)[-1]
        if anom:
            self.best_anom_log.extend(log)
        else:
            self.best_log.extend(log)

        # Parse the best results
        data = Parse.ParseOutputBest(self, (log, xml), anom)
        #pprint(data)

        # Set directory for future use
        #data["directory"] = os.path.dirname(inp)

        if self.labelit_results["labelit_results"]:
            # Best error checking. Most errors caused by B-factor calculation problem.
            # If no errors...
            if isinstance(data, dict):
                # Set directory for future use
                data["directory"] = os.path.dirname(inp)

                # data.update({"directory":os.path.dirname(inp)})
                if anom:
                    self.best_anom_results = {"best_results_anom":data}
                else:
                    self.best_results = {"best_results_norm":data}

                # Print to terminal
                if anom:
                    self.tprint(arg="\nBEST strategy ANOMALOUS", level=98, color="blue")
                else:
                    self.tprint(arg="\n\nBEST strategy NORMAL", level=98, color="blue")
                # Header lines
                self.tprint(arg="  " + "-" * 85, level=98, color="white")
                self.tprint(arg="  " + " N |  Omega_start |  N.of.images | Rot.width |  Exposure | \
Distance | % Transmission", level=98, color="white")
                self.tprint(arg="  " + "-" * 85, level=98, color="white")
                for sweep in data["sweeps"]:
                    self.tprint(
                        arg="  %2d |    %6.2f    |   %6d     |   %5.2f   |   %5.2f   | %5.1f  |     %3.2f      |" %
                            (sweep["run_number"],
                             sweep["phi_start"],
                             sweep["number_of_images"],
                             sweep["phi_width"],
                             sweep["exposure_time"],
                             sweep["distance"],
                             sweep["transmission"]
                            ),
                        level=98,
                        color="white")
                self.tprint(arg="  " + "-" * 85, level=98, color="white")

                return "OK"
            # BEST has failed
            else:
                if self.multiproc == False:
                    out = {"None":"No Best Strategy.",
                           "neg B":"Adjusting resolution",
                           "isotropic B":"Isotropic B detected"}
                    if out.has_key(data):
                        self.error_best_post(iteration, out[data], anom)
                self.tprint(arg="BEST unable to calculate a strategy", level=30, color="red")

                # print data
                return "FAILED"

    def postprocess_mosflm(self, inp):
        """
        Pass Mosflm log into parsing and save output dict.

        Keyword argument
        inp -- name of log file to interrogate
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::postprocess_mosflm %s" % inp)

        # print "postprocess_mosflm"

        try:
            if os.path.basename(inp).count("anom"):
                anom = True
                l = ["ANOM", "self.mosflm_strat_anom", "Mosflm ANOM strategy results"]
            else:
                anom = False
                l = ["", "self.mosflm_strat", "Mosflm strategy results"]
            out = open(inp, "r").readlines()
            eval("%s_log" % l[1]).extend(out)
        except:
            self.logger.exception("**ERROR in postprocess_mosflm**")

        data = Parse.ParseOutputMosflm_strat(self, out, anom)

        # Print to terminal
        #pprint(data)
        #if "run_number" in data:
        if anom == False:
            flag = "strategy "
            self.tprint(arg="\nMosflm strategy standard", level=98, color="blue")
        else:
            flag = "strategy anom "
            self.tprint(arg="\nMosflm strategy ANOMALOUS", level=98, color="blue")
        # Header lines
        self.tprint(arg="  " + "-" * 69, level=98, color="white")
        self.tprint(arg="  " + " N |  Omega_start |  N.of.images | Rot.width |  Exposure | Distance ", level=98, color="white")
        self.tprint(arg="  " + "-" * 69, level=98, color="white")

        for i in range(len(data[flag+"run number"])):
            self.tprint(
                arg="  %2d |    %6.2f    |   %6d     |   %5s   |   %5.2f   | %7s  " %
                    (
                        int(data[flag+"run number"][i]),
                        float(data[flag+"phi start"][i]),
                        int(data[flag+"num of images"][i]),
                        data[flag+"delta phi"],
                        float(data[flag+"image exp time"]),
                        str(data[flag+"distance"])
                    ),
                level=98,
                color="white")
        self.tprint(arg="  " + "-" * 69, level=98, color="white")

        if data == None:
            if self.verbose and self.logger:
                self.logger.debug("No Mosflm %s strategy.", l[0])
            eval("%s_results"%l[1]).update({l[2]:"FAILED"})
        elif data == "sym":
            if self.verbose and self.logger:
                self.logger.debug("dataset symmetry not compatible with autoindex symmetry")
            self.tprint(arg="Dataset symmetry not compatible with autoindex symmetry", level=30, color="red")
            eval("%s_results"%l[1]).update({l[2]:"SYM"})
        else:
            eval("%s_results" % l[1]).update({l[2]:data})

    def run_queue(self):
        """
        run_queue for strategy.
        """

        self.logger.debug("AutoindexingStrategy::run_queue")
        self.tprint(arg="\nStarting strategy calculations", level=98, color="blue")
        self.tprint(75, level="progress")

        # try:
        def set_best_results(i, x):
            # Set Best output if it failed after 3 tries
            if i == 3:
                if x == 0:
                    self.best_results = {"best_results_norm":"FAILED"}
                    self.best_failed = True
                else:
                    self.best_anom_results = {"best_results_anom":"FAILED"}
                    self.best_anom_failed = True


        try:
            st = 0
            if self.strategy == "mosflm":
                st = 4
            # dict = {}
            # Run twice for regular(0) and anomalous(1) strategies
            l = ["", "_anom"]
            first_print = False
            for x in range(0, 2):
                for i in range(st, 5):
                    timed_out = False
                    timer = 0
                    job = self.jobs[str(i)]
                    while 1:
                        # print "<<< x=%d, i=%d" % (x, i)
                        if job.is_alive() == False:
                            if i == 4:
                                log = os.path.join(self.labelit_dir, "mosflm_strat%s.out" % l[x])
                            else:
                                log = os.path.join(self.labelit_dir, str(i))+"/best%s.log" % l[x]
                            break
                        time.sleep(1)
                        timer += 1
                        if self.verbose and self.logger:
                            number = round(timer % 1, 1)
                            if number in (0.0, 1.0):
                                if first_print:
                                    self.tprint(arg=".",
                                                level=10,
                                                color="white",
                                                newline=False)
                                else:
                                    first_print = True
                                    self.tprint(arg="    Waiting for strategy to finish",
                                                level=10,
                                                color="white",
                                                newline=False)
                        if self.strategy_timer:
                            if timer >= self.strategy_timer:
                                timed_out = True
                                # print "Timed out"
                                job.terminate()
                                break
                    if timed_out:
                        self.tprint(arg="  Strategy calculation timed out", level=30, color="red")
                        set_best_results(i, x)
                        if i < 4:
                            if self.multiproc == False:
                                self.process_strategy(i+1)
                    else:
                        if i == 4:
                            self.postprocess_mosflm(log)
                        else:
                            job1 = self.postprocess_best(log)
                            if job1 == "OK":
                                break
                            # If Best failed...
                            else:
                                if self.multiproc == False:
                                    self.process_strategy(i+1)
                                set_best_results(i, x)
        except KeyboardInterrupt:
            pass

        if self.test == False:
            if self.multiproc:
                if self.cluster_use:
                    # kill child process on DRMAA job causes error on cluster.
                    # turn off multiprocessing.event so any jobs still running on cluster are terminated.
                    self.running.clear()
                else:
                    # kill all the remaining running jobs
                    for i in range(st, 5):
                        if self.jobs[str(i)].is_alive():
                            if self.verbose and self.logger:
                                self.logger.debug("terminating job: %s" % self.jobs[str(i)])
                            xutils.kill_children(self.jobs[str(i)].pid, self.logger)

    def labelit_cell_sym(self):
      """
      Get unit cell from Labelit results.
      """
      if self.verbose:
        self.logger.debug('AutoindexingStrategy::labelit_cell_sym')

      for line in open(os.path.join(self.labelit_dir,'bestfile.par'),'r').readlines():
            if line.startswith('CELL'):
                if len(line.split()) == 7:
                    self.labelit_cell = line.split()[1:]
            if line.startswith('SYMMETRY'):
                if len(line.split()) == 2:
                    self.labelit_sym = line.split()[1]

      #Sometimes bestfile.par is corrupt so I have backups to get cell and sym.
      # Only gets here if bestfile.par is corrupt
      if self.labelit_cell == False:
          for line in open('%s.mat'%os.path.join(self.labelit_dir,self.index_number),'r').readlines():
              if len(line.split()) == 6:
                  self.labelit_cell = line.split()
      if self.labelit_sym == False:
        for line in open(os.path.join(self.labelit_dir, self.index_number),'r').readlines():
          if line.startswith('SYMMETRY'):
            self.labelit_sym = line.split()[1]

    def labelit_sort(self):
        """
        Sort out which iteration of Labelit has the highest symmetry and choose that solution. If
        Labelit does not find a solution, finish up the pipeline.
        """

        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::labelit_sort")

        rms_list1 = []
        sg_list1 = []
        metric_list1 = []
        volumes = []
        sg_dict = {}
        sol_dict = {}
        sym = 0

        try:
            # Get the results and logs
            self.labelit_results = self.labelitQueue.get()
            self.labelit_log = self.labelitQueue.get()
        except KeyboardInterrupt:
            sys.exit()

        # print "labelit_results"
        # pprint(self.labelit_results)
        # print "labelit_log"
        # pprint(self.labelit_log)

        # All runs in error state
        error_count = 0
        for iteration, result in self.labelit_results.iteritems():
            # print "RESULT"
            # pprint(result)
            if result["labelit_results"] in ("ERROR", "TIMEOUT", "FAILED"):
                error_count += 1
        if error_count == len(self.labelit_results):
            # print "Unsuccessful indexing run. Exiting."
            # TODO
            sys.exit(9)

        # Run through all the results - compile them
        for iteration, result in self.labelit_results.iteritems():
            if isinstance(result["labelit_results"], dict):
                labelit_result = result.get("labelit_results")
                # Check for pseudotranslation in any Labelit run
                if labelit_result.get("pseudotrans") == True:
                    self.pseudotrans = True
                my_spacegroup, rms, metric, volume = labelit.get_labelit_stats(
                    labelit_results=labelit_result,
                    simple=True)
                spacegroup_num = xutils.convert_spacegroup(my_spacegroup)
                sg_dict[iteration] = spacegroup_num
                sg_list1.append(float(spacegroup_num))
                rms_list1.append(rms)
                metric_list1.append(metric)
                volumes.append(volume)
            else:
                # If Labelit failed, set dummy params
                sg_dict[iteration] = 0
                sg_list1.append(0)
                rms_list1.append(100)
                metric_list1.append(100)
                volumes.append(0)
        # pprint(sg_dict)
        # pprint(sg_list1)
        # pprint(rms_list1)
        # pprint(metric_list1)
        # pprint(volumes)

        for index in range(len(sg_list1)):
            if sg_list1[index] == numpy.amax(sg_list1):
                # If its P1 look at the Mosflm RMS, else look at the Labelit metric.
                if sg_list1[index] == 1.0:
                    sol_dict[rms_list1[index]] = self.labelit_results.keys()[index]
                else:
                    sol_dict[metric_list1[index]] = self.labelit_results.keys()[index]

        # print "sol_dict"
        # pprint(sol_dict)

        sol_dict_keys = sol_dict.keys()
        sol_dict_keys.sort()

        # Best Labelit_results key
        highest = sol_dict[sol_dict_keys[0]]
        # Since iter 5 cuts res, it is often the best. Only choose if its the
        # only solution.
        if len(sol_dict_keys) > 1:
            if highest == 5:
                highest = sol_dict[sol_dict_keys[1]]

        # symmetry of best solution
        sym = sg_dict[highest]

        # If there is a solution...
        if sym != 0:
            self.logger.debug("The sorted labelit solution was #%s", highest)

            # Save best results in corect place.
            self.labelit_results = self.labelit_results[highest]

            # Set self.volume for best solution
            self.volume = volumes[highest]

            # Set self.labelit_dir and go to it.
            self.labelit_dir = os.path.join(self.working_dir, str(highest))
            self.index_number = self.labelit_results.get("labelit_results").get("mosflm_index")
            os.chdir(self.labelit_dir)

            # Parse out additional information from labelit-created files
            """
            bestfile_lines = open("bestfile.par", "r").readlines()
            mat_lines = open("%s.mat" % self.index_number, "r").readlines()
            sub_lines = open("%s" % self.index_number, "r").readlines()
            # Parse the file for unit cell information
            labelit_cell, labelit_sym = labelit.parse_labelit_files(bestfile_lines,
                                                                    mat_lines,
                                                                    sub_lines)
            """
            # Save the self.Labelit_cell and self.Labelit_sym
            self.labelit_cell_sym()
            
            self.labelit_results["labelit_results"]["best_cell"] = self.labelit_cell
            self.labelit_results["labelit_results"]["best_sym"] = self.labelit_sym
            # pprint(self.labelit_results)

            # Handle the user-set spacegroup
            if self.spacegroup != False:
                check_lg = xutils.checkSG(self, sym)
                if self.spacegroup != sym:
                    fix_spacegroup = False
                    for line in check_lg:
                        if line == self.spacegroup:
                            fix_spacegroup = True
                    if fix_spacegroup:
                        xutils.fixMosflmSG(self)
                        xutils.fixBestSG(self)
                    #else:
                         # Used for telling user that SG is not compatible with cell
                    #    self.ignore_user_SG = True

            # Print Labelit results to commandline
            self.tprint(arg="\nHighest symmetry Labelit result",
                        level=98,
                        color="blue",
                        newline=False)

            for line in self.labelit_results["labelit_results"]["output"][5:]:
                self.tprint(arg="  %s" % line.rstrip(), level=98, color="white")
            # pprint(self.labelit_results["labelit_results"]["output"])

        # No Labelit solution
        else:
            self.logger.debug("No solution was found when sorting Labelit results.")
            self.tprint(arg="\n  Labelit failed to index", level=30, color="red")
            self.labelit_failed = True
            self.labelit_results = {"labelit_results":"FAILED"}
            self.labelit_dir = os.path.join(self.working_dir, "0")
            os.chdir(self.labelit_dir)
            self.process_distl()
            self.postprocess_distl()
            #   if os.path.exists("DISTL_pickle"):
              #   self.makeImages(2)
            self.best_failed = True
            self.best_anom_failed = True

        # except:
        #     self.logger.exception("**ERROR in labelit_sort**")

    def folders_strategy(self, iteration=0):
        """
        Sets up new directory for programs.
        """
        if self.verbose:
            self.logger.debug('Utilities::foldersStrategy')

        copy = False
        new_folder = os.path.join(self.labelit_dir,str(iteration))
        if os.path.exists(new_folder) == False:
            copy = True
        # Go to new_folder
        xutils.folders2(self, new_folder)
        if copy:
            if iteration == 0:
                # Copy files Mosflm generates for BEST
                os.system('cp %s/bestfile* %s/%s*.hkl .'%(self.labelit_dir,self.labelit_dir,self.index_number))
            # Copy other files required by BEST
            shutil.copy(os.path.join(self.labelit_dir,'%s.mat'%self.index_number),new_folder)
            if self.header2:
                shutil.copy(os.path.join(self.labelit_dir,'%s_S.mat'%self.index_number),new_folder)
            #For Pilatis background calc. (NOT USED because it takes too long and doent make much difference)
            if self.vendortype in ('Pilatus-6M','ADSC-HF4M'):
                if os.path.exists(os.path.join(self.working_dir,'BKGINIT.cbf')):
                    shutil.copy(os.path.join(self.working_dir,'BKGINIT.cbf'),new_folder)

    def find_best_strat(self, inp):
        """
        Find the BEST strategy according to the plots.
        """

        if self.verbose and self.logger:
            self.logger.debug('AutoindexingStrategy::find_best_strat')

        def getBestRotRange(inp):
            """
            Parse lines from XML file.
            """
            try:
                p_s = []
                p_e = False
                for line in inp:
                    if line.count('"phi_start"'):
                        p_s.append(line[line.find('>')+1:line.rfind('<')])
                    if line.count('"phi_end">'):
                        p_e = line[line.find('>')+1:line.rfind('<')]
                # If BEST failed...
                if p_e == False:
                    return 'FAILED'
                else:
                    return int(round(float(p_e)-float(p_s[0])))
            except:
                self.logger.exception('**Error in getBestRotRange**')
                return 'FAILED'

        try:
            phi_st = []
            phi_rn = []
            st = False
            end = False
            run = False
            if os.path.exists(inp):
                f = open(inp, 'r').readlines()
                for x, line in enumerate(f):
                    if line.startswith("% linelabel  = 'compl -99.%'"):
                        st = x
                    if line.startswith("% linelabel  = 'compl -95.%'"):
                        end = x
                if st and end:
                    for line in f[st:end]:
                        if len(line.split()) == 2:
                            phi_st.append(line.split()[0])
                            phi_rn.append(int(line.split()[1]))
                    min1 = min(phi_rn)
                    # If xml exists, check if new strategy is at least 5 degrees less rotation range.
                    if os.path.exists(inp.replace('.plt', '.xml')):
                        orig_range = getBestRotRange(open(inp.replace('.plt', '.xml'), 'r').readlines())
                        if orig_range != 'FAILED':
                            if orig_range - min1 >= 5:
                                run = True
                    else:
                        run = True
            if run:
                return (str(phi_st[phi_rn.index(min1)]), str(min1))
            else:
                return (False, False)

        except:
            self.logger.exception('**Error in find_best_strat**')
            return (False, False)

    def write_json(self, results):
        """Write a file with the JSON version of the results"""

        json_string = json.dumps(results) #.replace("\\n", "")

        # Output to terminal?
        if self.preferences.get("json", False):
            print json_string

        # Always write a file
        os.chdir(self.working_dir)
        with open("result.json", "w") as outfile:
            outfile.writelines(json_string)

    def print_credits(self):
        """
        Print information regarding programs utilized by RAPD
        """

        self.tprint(rcredits.HEADER,
                    level=99,
                    color="blue")

        programs = ["CCTBX", "BEST", "MOSFLM", "RADDOSE"]
        info_string = rcredits.get_credits_text(programs, "    ")

        self.tprint(info_string, level=99, color="white")

    def print_plots(self):
        """Display plots on the commandline"""

        # Plot as long as JSON output is not selected
        if self.preferences.get("show_plots", True) and \
           (not self.preferences.get("json", False)):

            # Determine the open terminal size
            term_size = os.popen('stty size', 'r').read().split()

            titled = False

            for plot_type in ("osc_range", "osc_range_anom"):

                if plot_type in self.plots:

                    if not titled:
                        self.tprint(arg="\nPlots from BEST",
                                    level=98,
                                    color="blue")
                        titled = True

                    tag = {"osc_range":"standard",
                           "osc_range_anom":"ANOMALOUS"}[plot_type]

                    plot_data = self.plots[plot_type]

                    # Determine y max
                    y_array = numpy.array(plot_data["y_data"][0]["data"])
                    y_max = y_array.max() + 10
                    y_min = 0

                    gnuplot = subprocess.Popen(["gnuplot"],
                                               stdin=subprocess.PIPE)
                    gnuplot.stdin.write(
                        """set term dumb %d,%d
                           set key outside
                           set title 'Minimal Oscillation Ranges %s'
                           set xlabel 'Starting Angle'
                           set ylabel 'Rotation Range' rotate by 90 \n""" % \
                           (min(180, int(term_size[1])),
                            max(30, int(int(term_size[0])/3)),
                            tag))

                    # Create the plot string
                    plot_string = "plot [0:180] [%d:%d] " % (y_min, y_max)
                    for i in range(min(5, len(plot_data["y_data"]))):
                        plot_string += "'-' using 1:2 title '%s' with lines," % \
                        plot_data["y_data"][i]["label"]
                    plot_string = plot_string.rstrip(",") + "\n"
                    gnuplot.stdin.write(plot_string)

                    # Run through the data and add to gnuplot
                    for i in range(min(5, len(plot_data["y_data"]))):
                        y_series = plot_data["y_data"][i]["data"]
                        x_series = plot_data["x_data"]
                        for i, j in zip(x_series, y_series):
                            gnuplot.stdin.write("%f %f\n" % (i, j))
                        gnuplot.stdin.write("e\n")

                    # Now plot!
                    gnuplot.stdin.flush()
                    time.sleep(3)
                    gnuplot.terminate()

    def postprocess(self):
        """
        Make all the HTML files, pass results back, and cleanup.
        """
        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::postprocess")

        output = {}

        # Set up the results for return
        self.results["process"]["status"] = 100
        # self.results["directories"] = self.setup
        # self.results["information"] = self.header
        # self.results["preferences"] = self.preferences

        if self.labelit_failed == False:
            if self.strategy == "mosflm":
                pass
            else:
                if self.best_failed:
                    if self.best_anom_failed:
                        pass
                    else:
                        self.html_best_plots()
                elif self.best_anom_failed:
                    self.html_best_plots()
                else:
                    self.html_best_plots()
                    self.print_plots()

        # Save path for files required for future STAC runs.
        # try:
        if self.labelit_failed == False:
            os.chdir(self.labelit_dir)
            # files = ["DNA_mosflm.inp", "bestfile.par"]
            # files = ["mosflm.inp", "%s.mat"%self.index_number]
            files = ["%s.mat" % self.index_number, "bestfile.par"]
            for index, file_to_copy in enumerate(files):
                shutil.copy(file_to_copy, self.working_dir)
                if os.path.exists(os.path.join(self.working_dir, file_to_copy)):
                    output["STAC file%s" % str(index+1)] = os.path.join(self.dest_dir,
                                                                        file_to_copy)
                else:
                    output["STAC file%s" % str(index+1)] = "None"
        else:
            output["STAC file1"] = "None"
            output["STAC file2"] = "None"
        # except:
        #     self.logger.exception("**Could not update path of STAC files**")
        #     output["STAC file1"] = "FAILED"
        #     output["STAC file2"] = "FAILED"

        # # Pass back paths for html files
        # if self.gui:
        #     suffix = ".php"
        # else:
        #     suffix = ".html"
        # l = [("best_plots%s" % suffix, "Best plots html"),
        #      ("jon_summary_long%s" % suffix, "Long summary html"),
        #      ("jon_summary_short%s" % suffix, "Short summary html")]
        # for i in range(len(l)):
        #     try:
        #         path = os.path.join(self.working_dir, l[i][0])
        #         path2 = os.path.join(self.dest_dir, l[i][0])
        #         if os.path.exists(path):
        #             output[l[i][1]] = path2
        #         else:
        #             output[l[i][1]] = "None"
        #     except:
        #         self.logger.exception("**Could not update path of %s file.**" % l[i][0])
        #         output[l[i][1]] = "FAILED"

        # Put all output files into a singe dict to pass back.
        output_files = {"Output files" : output}

        # Put all the result dicts from all the programs run into one resultant dict and pass back.
        results = {}
        if self.labelit_results:
            results.update(self.labelit_results)
        if self.distl_results:
            results["distl_results"] = self.distl_results
        if self.raddose_results:
            results.update(self.raddose_results)
        if self.best_results:
            results.update(self.best_results)
        if self.best_anom_results:
            results.update(self.best_anom_results)
        if self.mosflm_strat_results:
            results.update(self.mosflm_strat_results)
        if self.mosflm_strat_anom_results:
            results.update(self.mosflm_strat_anom_results)

        results["plots"] = self.plots

        # if self.gui:
        self.results["results"] = results

        self.logger.debug(self.results)

        # Print results to screen in JSON format
        # json_output = json.dumps(self.results).replace("\\n", "")
        # if self.preferences.get("json", False):
        #     print json_output
        # del self.results['command']['site']
        #pprint(self.results)
        self.write_json(self.results)

        if self.preferences.get("run_mode") == "server":
            if not self.redis:
                self.connect_to_redis()
            self.logger.debug("Sending back on redis")
            json_results = json.dumps(self.results)
            self.redis.lpush("RAPD_RESULTS", json_results)
            self.redis.publish("RAPD_RESULTS", json_results)

        self.tprint(arg=100, level="progress")

        # Cleanup my mess.
        try:
            os.chdir(self.working_dir)
            if self.clean:
                if self.test == False:
                    if self.verbose and self.logger:
                        self.logger.debug("Cleaning up files and folders")
                    os.system("rm -rf labelit_iteration* dataset_preferences.py")
                    for i in range(0, self.nrun):
                        os.system("rm -rf %s" % i)
        except:
            self.logger.exception("**Could not cleanup**")

        # Move files from RAM to destination folder
        try:
            if self.working_dir == self.dest_dir:
                pass
            else:
                if self.gui:
                    if os.path.exists(self.dest_dir):
                        shutil.rmtree(self.dest_dir)
                    shutil.move(self.working_dir, self.dest_dir)
                else:
                    os.system("cp -R * %s" % self.dest_dir)
                    os.system("rm -rf %s" % self.working_dir)
        except:
            self.logger.exception("**Could not move files from RAM to destination dir.**")

        # Print out recognition of the programs being used
        self.print_credits()

        # Say job is complete.
        t = round(time.time() - self.start_time)
        self.logger.debug("-------------------------------------")
        self.logger.debug("RAPD autoindexing/strategy complete.")
        self.logger.debug("Total elapsed time: %s seconds", t)
        self.logger.debug("-------------------------------------")
        self.tprint(arg="\nRAPD autoindexing & strategy complete", level=98, color="green")
        self.tprint(arg="Total elapsed time: %s seconds" % t, level=10, color="white")

    def html_best_plots(self):
        """
        generate plots html/php file
        """

        self.tprint(arg="Generating plots from Best", level=10, color="white")

        if self.verbose and self.logger:
            self.logger.debug("AutoindexingStrategy::html_best_plots")

        # Debugging
        # pprint(self.best_results)

        # try:
        # run = True
        plot = {}
        plotanom = {}
        new_plot = {}
        new_plotanom = {}

        norm_res_dir = self.best_results.get("best_results_norm").get("directory", False)
        anom_res_dir = self.best_anom_results.get("best_results_anom").get("directory", False)

        # Get the parsed results for reg and anom results and put them into a single dict.
        if norm_res_dir:
            # Read the raw best plots output
            raw = open(os.path.join(norm_res_dir, "best.plt"), "r").readlines()
            # Parse the plot file
            new_plot = best.parse_best_plots(raw)

            if anom_res_dir:
                # Read the raw best plots output
                raw = open(os.path.join(anom_res_dir, "best_anom.plt"), "r").readlines()
                # Parse the plot file
                new_plotanom = best.parse_best_plots(raw)
                new_plot.update({"osc_range_anom": new_plotanom.get("osc_range")})

        elif anom_res_dir:
            # Read the raw best plots output
            raw = open(os.path.join(anom_res_dir, "best.plt"), "r").readlines()
            # Parse the plot file
            new_plotanom = best.parse_best_plots(raw)
            new_plot.update({"osc_range_anom": new_plotanom.pop("osc_range")})
        else:
            run = False

        # Best failed?
        if self.best_failed:
            self.plots = False
        # Best success
        else:
            self.plots = new_plot

        # except:
        #     self.logger.exception("**ERROR in html_best_plots**")


class RunLabelit(Thread):
    
    # Holder of PID's or JobID's
    jobids = {}
    # Holder for the job threads
    jobs = {}
    # Holder for errors
    tracker = {}
    # Holder for results
    results = {}
    # Holder for the logs
    log = {}
    # For handling print_warning (future?)
    errors_printed = False

    def __init__(self, command, output, params, tprint=False, logger=None):
        """
        input >> command
        #New minimum input
        {   'command': 'INDEX+STRATEGY',
            'directories': {   'work': '/home/schuerjp/temp/beamcenter/800.0'},
            'header1': {   'beam_center_x': 149.871,
      		'beam_center_y': 145.16,
      		'distance': 800.0,
      		'fullname': '/home/schuerjp/temp/beamcenter/SER-9_Pn0.0020',
      		'spacegroup': 'None',
      		'vendortype': 'MARCCD'},
            'preferences': {   'a': 0.0,
      		     'alpha': 0.0,
      		     'b': 0.0,
      		     'beam_flip': 'False',
      		     'beta': 0.0,
      		     'c': 0.0,
      		     'gamma': 0.0,
      		     'multiprocessing': 'True',
      		     'sample_type': 'protein'},
            'return_address': ('127.0.0.1', 50000)}
        """
        Thread.__init__(self)
        self.start_time= time.time()

        # Passed-in vars
        self.command = command
        #self.input = command
        self.output = output
        self.logger = logger

        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        # Setting up data input
        self.setup = command["directories"]
        self.header = command["header1"]
        self.header2 = command.get("header2", False)
        self.preferences = command["preferences"]
        self.site_parameters = command.get("site_parameters", {})

        # Set input params
        # Run in debug mode
        self.test = params.get("test", False)

        # Pass int the multiprocessing.Pool for job submission
        self.kill_job = params.get("kill_job")

        # Get the correct laucher, (already loaded)
        # Will not use RAM if cluster_use=True since runs would be on separate nodes. Adds
        # overhead of 1-3s to total run time if all nodes same speed.
        self.launcher = params.get("launcher", local_subprocess)

        # If self.cluster_use == True, you can specify a batch queue on your cluster.
        self.batch_queue = params.get("batch_queue", {})
        # I don't like this so I may move this later!!
        if not len(self.batch_queue.keys()):
            # Setup a Queue.Queue for local_subprocess
            self.queue_type = ''
        else:
            # Setup a multiprocessing.Queue for cluster submission. This solves threading issue in DRMAA.
            self.queue_type = 'mp_'

        # Get detector vendortype for settings. Defaults to ADSC.
        self.vendortype = params.get("vendortype", "ADSC")

        # Turn on verbose output
        self.verbose = params.get("verbose", False)

        # 'all' means run all the Labelit runs
        # an int would say to just run that particular run.
        self.nrun = params.get("iterations", 'all')
        if isinstance(self.nrun, int):
            self.tot_runs = 1
        else:
            # Get the total number of Labelit runs
            self.tot_runs = self.get_labelit_settings('total')

        # Display results in UI
        self.gui = True

        # Set times for processes. "False" to disable.
        if self.header2:
            self.labelit_timer = 180
        else:
            self.labelit_timer = 120
        # Turns on multiprocessing for everything
        # Turns on all iterations of Labelit running at once, sorts out highest symmetry solution,
        # then continues...(much better and faster!!)
        self.multiproc = self.preferences.get("multiprocessing", True)

        self.sample_type = self.preferences.get("sample_type", "protein").lower()

        self.spacegroup = self.preferences.get("spacegroup", False)
        if self.spacegroup != False:
            self.tprint(arg="Spacegroup is set to %s" % self.spacegroup, level=10, color="white")

        # For results passing
        self.indexing_results_queue = eval('%sQueue()'%self.queue_type)

        # This is where I place my overall folder settings.
        self.working_dir = self.setup.get("work")

        #Process.__init__(self, name="RunLabelit")
        self.start()

    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug("RunLabelit::run")

        self.preprocess()

        # Make the initial dataset_prefernces.py file
        self.preprocess_labelit()

        if self.tot_runs == 1:
            # This is used for beam center plugin
            self.labelit_timer = 300
            # Sets the dataset_preferences.py and launches Labelit
            self.get_labelit_settings(self.nrun)
        else:
            # Normal mode: running all the Labelit runs
            for i in range(self.tot_runs):
                self.get_labelit_settings(i)

        # Watch for returns
        self.labelit_run_queue()

        if self.nrun == 'all':
            # Put the logs together
            self.condense_logs()

        # send results and logs back to main process
        self.postprocess()

    def preprocess(self):
        """
        Setup the working dir in the RAM and save the dir where the results will go at the end.
        """
        if self.verbose and self.logger:
            self.logger.debug("RunLabelit::preprocess")
        xutils.create_folder(self.working_dir)
        if self.test:
            if self.nrun == 'all':
                self.logger.debug("TEST IS ON")
                self.tprint(arg="TEST IS ON", level=10, color="white")

    def preprocess_labelit(self):
        """
        Setup extra parameters for Labelit if turned on. Will always set beam center from image header.
        Creates dataset_preferences.py file for editing later in the Labelit error iterations if needed.
        """

        if self.verbose and self.logger:
            self.logger.debug('RunLabelit::preprocess_labelit')

        twotheta = self.header.get("twotheta", 0.0)
        x_beam = self.header.get("x_beam")
        y_beam = self.header.get("y_beam")

        # If an override beam center is provided, use it
        if self.preferences.get("x_beam", False):
            x_beam = self.preferences["x_beam"]
            y_beam = self.preferences["y_beam"]
            self.tprint("  Using override beam center %s, %s" % (x_beam, y_beam),
                        10,
                        "white",
                        newline=False)

        binning = True
        if self.header.has_key('binning'):
            binning = self.header.get('binning')

        if self.test == False:
            # Setup the dataset_preferences.py file for Labelit.
            preferences = open('dataset_preferences.py', 'w')
            preferences.write('#####Base Labelit settings#####\n')
            preferences.write('best_support=True\n')
            # Set Mosflm RMSD tolerance larger
            preferences.write('mosflm_rmsd_tolerance=4.0\n')

            # If binning is off. Force Labelit to use all pixels(MAKES THINGS WORSE).
            # Increase number of spots to use for indexing.
            if binning == False:
                preferences.write('distl_permit_binning=False\n')
                preferences.write('distl_maximum_number_spots_for_indexing=600\n')

            # If user wants to change the res limit for autoindexing.
            if self.preferences.get('index_hi_res', 0.0) != 0.0:
                #preferences.write('distl.res.outer='+index_hi_res+'\n')
                preferences.write('distl_highres_limit=%.2f\n' % self.preferences.get('index_hi_res'))

            # Always specify the beam center.
            # If Malcolm flips the beam center in the image header...
            if self.preferences.get("beam_flip", False):
                preferences.write("autoindex_override_beam=(%.2f, %.2f)\n" % (y_beam, x_beam))
            else:
                preferences.write("autoindex_override_beam=(%.2f, %.2f)\n" % (x_beam, y_beam))

            # If two-theta is being used, specify the angle and distance correctly.
            if twotheta == 0.0:
                preferences.write('beam_search_scope=%.2f\n' %
                                  self.preferences.get("beam_search", 0.2))
            else:
                # Have to increase the beam_search_scope when 2theta is in use.
                preferences.write('beam_search_scope=0.5\n')
                preferences.write('autoindex_override_twotheta=%.2f\n'%twotheta)
                # preferences.write('autoindex_override_distance='+distance+'\n')
            preferences.close()

    def correct_labelit(self, iteration, overrides):
        """
        Perform Labelit corrections - called from process_labelit after directory creation and
        relocation
        """

        # Try to run with generic
        if overrides.get("no_solution"):
            # print ">>> NO SOLUTION", iteration
            sys.exit()

        # Correct error by decreasing the good spots requirement
        if overrides.get("min_good_spots"):
            good_spots = labelit.decrease_good_spot_requirements(overrides.get("min_good_spots"))
            self.log[iteration].append("\nSetting min number of good bragg spots to %d and \
rerunning.\n" % good_spots)

        # Correct error by increasing Mosflm resolution
        if overrides.get("decrease_mosflm_resolution"):
            new_res = labelit.decrease_mosflm_resolution(iteration)
            self.log[iteration].append("\nDecreasing integration resolution to %.1f and \
rerunning.\n" % new_res)

        # Decrease the number of spots required
        if overrides.get("min_spots"):
            spot_count = labelit.decrease_spot_requirements(overrides.get("min_spots"))
            #self.log[iteration].extend("\nDecreasing spot requirments to %d and \
            self.log[iteration].append("\nDecreasing spot requirments to %d and \
rerunning.\n" % spot_count)

        # Get rid of bumpiness
        if overrides.get("bumpiness"):
            removed = labelit.no_bumpiness()
            if removed:
                #self.log[iteration].extend("\nProfile bumpiness removed and rerunning.\n")
                self.log[iteration].append("\nProfile bumpiness removed and rerunning.\n")
            else:
                pass

        return True

    def get_labelit_settings(self, iteration=0):
        """
        Set/reset setting in dataset_preferences.py according to run iteration.
        Commented out things were tried before.
        """
    
        self.logger.debug('Utilities::errorLabelit')
        
        # If iteration is string, return the total number of iterations in the funnction.
        if isinstance(iteration, str):
            return 6
    
        # Create separate folders for Labelit runs.
        if self.multiproc == False:
            iteration += 1
        # Change to the correct folder (create it if necessary).
        #foldersLabelit(self, iteration)
        xutils.create_folders_labelit(self.working_dir, iteration)
    
        preferences = open('dataset_preferences.py','a')
    
        preferences.write('\n#iteration %s\n' % iteration)
    
        if iteration == 0:
            preferences.close()
            self.log[iteration] = ['\nUsing default parameters.\n']
            self.tprint("\n  Using default parameters", level=30, color="white", newline=False)
            self.logger.debug('Using default parameters.')
    
        if iteration == 1:
            # Seemed to pick stronger spots on Pilatis
            if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
                preferences.write('distl.minimum_spot_area=3\n')
                preferences.write('distl.minimum_signal_height=4\n')
            elif "Eiger" in self.vendortype:
                preferences.write('distl.minimum_spot_area=3\n')
                preferences.write('distl.minimum_signal_height=5.5\n')
            else:
                preferences.write('distl.minimum_spot_area=6\n')
                preferences.write('distl.minimum_signal_height=4.3\n')
            preferences.close()
            self.log[iteration] = ['\nLooking for long unit cell.\n']
            self.tprint("\n  Looking for long unit cell", level=30, color="white", newline=False)
            self.logger.debug('Looking for long unit cell.')
    
        elif iteration == 2:
            # Change it up and go for larger peaks like small molecule.
            preferences.write('distl.minimum_spot_height=6\n')
            preferences.close()
            self.log[iteration] = ['\nChanging settings to look for stronger peaks (ie. small molecule).\n']
            self.tprint("\n  Looking for stronger peaks (ie. small molecule)", level=30, color="white", newline=False)
            self.logger.debug("Changing settings to look for stronger peaks (ie. small molecule).")
    
        elif iteration == 3:
            if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
                preferences.write('distl.minimum_spot_area=2\n')
                preferences.write('distl.minimum_signal_height=2.3\n')
            elif "Eiger" in self.vendortype:
                preferences.write('distl.minimum_spot_area=3\n')
                preferences.write('distl.minimum_signal_height=2.6\n')
            else:
                preferences.write('distl.minimum_spot_area=7\n')
                preferences.write('distl.minimum_signal_height=1.2\n')
            preferences.close()
            self.log[iteration] = ['\nLooking for weak diffraction.\n']
            self.tprint("\n  Looking for weak diffraction", level=30, color="white", newline=False)
            self.logger.debug('Looking for weak diffraction.')
    
        elif iteration == 4:
            if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
                preferences.write('distl.minimum_spot_area=3\n')
                self.log[iteration] = ['\nSetting spot picking level to 3.\n']
                area = 3
            elif "Eiger" in self.vendortype:
                preferences.write('distl.minimum_spot_area=3\n')
                self.log[iteration] = ['\nSetting spot picking level to 3.\n']
                area = 3
            else:
                preferences.write('distl.minimum_spot_area=8\n')
                self.log[iteration] = ['\nSetting spot picking level to 8.\n']
                area = 8
            preferences.close()
            self.tprint("\n  Setting spot picking level to %d" % area, level=30, color="white", newline=False)
            self.logger.debug('Setting spot picking level to 3 or 8.')
    
        elif iteration == 5:
            if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
                preferences.write('distl.minimum_spot_area=2\n')
                preferences.write('distl_highres_limit=5\n')
                self.log[iteration] = ['\nSetting spot picking level to 2 and resolution to 5.\n']
                setting = (2, 5)
            elif "Eiger" in self.vendortype:
                preferences.write('distl.minimum_spot_area=2\n')
                preferences.write('distl_highres_limit=4\n')
                self.log[iteration] = ['\nSetting spot picking level to 2 and resolution to 4.\n']
                setting = (2, 4)
            else:
                preferences.write('distl.minimum_spot_area=6\n')
                preferences.write('distl_highres_limit=5\n')
                self.log[iteration] = ['\nSetting spot picking level to 6 and resolution to 5.\n']
                setting = (6, 5)
            preferences.close()
            self.tprint("\n  Setting spot picking level to %d and hires limit to %d" % setting, level=30, color="white", newline=False)
            self.logger.debug('Setting spot picking level to 2 or 6.')
    
        return self.process_labelit(iteration)

    def process_labelit(self, iteration=0, inp=False, overrides={}, error=False):
        """
        Construct the labelit command and run. Passes back dict with PID:iteration.
        """
        self.logger.debug("RunLabelit::process_labelit")
        # print "process_labelit %d %s" % (iteration, inp)

        # try:
        labelit_input = []

        # Check if user specific unit cell
        unit_cell_defaults = dict(zip(["a", "b", "c", "alpha", "beta", "gamma"], [False]*6))
        counter = 0
        for parameter in unit_cell_defaults:
            parameter_pref = self.preferences.get(parameter, 0.0)
            if parameter_pref != 0:
                unit_cell_defaults[parameter] = parameter_pref
                counter += 1

        # Can't set less than 6 unit cell parameters
        if counter != 6:
            unit_cell_defaults = False

        # Put together the command for labelit.index
        command = 'labelit.index '

        # Fix some errors
        if overrides:
            self.correct_labelit(iteration, overrides)

        # Multiple possible spacegroups
        if overrides.get("fix_cell"):
            add_to_command = labelit.fix_multiple_cells(
                lattice_group=overrides.get("lattice_group"),
                labelit_solution=overrides.get("labelit_solution")
            )
            #print add_to_command
            command += add_to_command

        # If first labelit run errors because not happy with user specified cell or SG then
        # ignore user input in the rerun.
        #if not self.ignore_user_cell and not overrides.get("ignore_user_cell"):
        if not overrides.get("ignore_user_cell"):
            user_cell = self.preferences.get("unitcell", False)
            if user_cell:
                command += 'known_cell=%s,%s,%s,%s,%s,%s ' % tuple(user_cell)
        #if not self.ignore_user_SG and not overrides.get("ignore_user_SG"):
        if not overrides.get("ignore_user_SG"):
            if self.spacegroup != False:
                command += 'known_symmetry=%s ' % self.spacegroup
        if overrides.get("ignore_sublattice"):
            command += 'sublattice_allow=False '

        # For peptide crystals. Doesn't work that much.
        if self.sample_type == 'peptide':
            command += 'codecamp.maxcell=80 codecamp.minimum_spot_count=10 '
        if inp:
            command += '%s ' % inp
        command += '%s ' % self.header.get('fullname')

        # If pair of images
        if self.header2:
            command += "%s " % self.header2.get("fullname")

        # Save the command to the top of log file, before running job.
        self.log[iteration].extend([command])
        print '\n%s'%command

        # Don't launch job if self.test = True
        if self.test:
            run = "junk%s" % iteration
        # Not testing
        else:
            log = os.path.join(os.getcwd(), "labelit.log")

            # queue to retrieve the PID or JobIB once submitted.
            pid_queue = eval('%sQueue()'%self.queue_type)

            # setup input kwargs
            inp_kwargs = {"command": command,
                          "logfile": log,
                          "pid_queue": pid_queue,
                          "result_queue": self.indexing_results_queue,
                          "tag": iteration}
            # Add batch queue info if launching on cluster
            inp_kwargs.update(self.batch_queue)

            # Launch the job
            run = Thread(target=self.launcher,
                         name=iteration,
                         kwargs=inp_kwargs)
            run.start()

            # Save the jobs for monitoring status
            self.jobs[iteration] = run

            # Save the PID for killing the job later if needed.
            self.jobids[iteration] = pid_queue.get()

            # Save the number of times a job was run to stop a loop
            self.tracker.setdefault(iteration, {'nruns':0})
            self.tracker[iteration]['nruns'] += 1

        # return the job
        return run

    def postprocess_labelit(self, raw_result):
        """
        Sends Labelit log for parsing and error checking for rerunning Labelit. Save output dicts.
        """
        # Set defaults
        ex = False
        er = "Labelit failed to find solution."
        failed = False
        
        iteration = raw_result["tag"]
        stdout = raw_result["stdout"]

        # Add to log
        self.log[iteration].append("\n\n")
        self.log[iteration].extend(stdout.split("\n"))

        # Couldn't index
        # elif "No_Indexing_Solution: (couldn't find 3 good basis vectors)" in stdout:
        #     error = "No_Indexing_Solution: (couldn't find 3 good basis vectors)"

        parsed_result = labelit.parse_output(stdout, iteration)
        # Save the return into the shared var
        self.results[iteration] = {"labelit_results": parsed_result}

        # Do error checking and send to correct place according to iteration.
        potential_problems = {
            # Base command to rerun job
            "run_command": functools.partial(self.process_labelit, iteration=iteration),

            "bad_input": {
                "error": "Labelit did not like your input unit cell dimensions or SG.",
                "execute1": {"ignore_sublattice": True},
                "execute2": {"ignore_user_cell": True},
                "execute3": {"ignore_user_cell": True, 
                             "ignore_user_SG": True}},
            "bumpiness": {
                "error": "Labelit settings need to be adjusted.",
                "execute1": {"bumpiness": True}
                },
            "mosflm_error": {
                "error": "Mosflm could not integrate your image.",
                "execute1": {"decrease_mosflm_resolution": True}
                },
            "min_good_spots": {
                "error": "Labelit did not have enough spots to find a solution",
                "execute1": True
                },
            "min_spots": {
              "error": "Labelit did not have enough spots to find a solution",
              "execute1": True
                },
            "fix_cell": {
                "error": "Labelit had multiple choices for user SG and failed.",
                "execute1": True,
                },

            # No fix for these errors
            "fix_labelit": {
                "error": "Distance is not getting read correctly from the image header."},
            "no_pair": {
                "error": "Images are not a pair."},
            "failed": {
                "error": "Autoindexing failed to find a solution"},
            "eiger_cbf_error": {
                "error": "IOTBX needs patched for Eiger CBF files"},
        }

        # If Labelit results are OK, then...
        if isinstance(parsed_result, dict):
            problem_flag = False

        # Otherwise deal with fixing and rerunning Labelit
        elif isinstance(parsed_result, tuple):
            problem_flag = parsed_result[0]
        else:
            problem_flag = parsed_result

        if problem_flag:
            # Change to the correct folder for rerunning.
            xutils.create_folders_labelit(self.working_dir, iteration)
            
            # Check if there is a fix... 
            problem_actions = potential_problems.get(problem_flag, False)
            if problem_actions:
                # Keep track of how many times the specific errors have come up.
                self.tracker[iteration].setdefault(problem_flag,  0)
                self.tracker[iteration][problem_flag] += 1
                # Shortcuts
                ex = problem_actions.get("execute%s"%self.tracker[iteration][problem_flag], False)
                er = problem_actions.get('error')

            # Failure to index due to too few spots
            if problem_flag == "min_spots":
                spot_count = parsed_result[1]
                # If only run once and more than 25 spots
                if spot_count > 25 and ex:
                    potential_problems['run_command'](overrides={"min_spots": spot_count})
                else:
                    # Failed since not enough spots 
                    failed = True

            # When Labelit works, but Mosflm step fails. Rerun forcing Mosflm to work.
            elif problem_flag == "min_good_spots":
                if ex:
                    potential_problems['run_command'](overrides={"min_good_spots": parsed_result[1]})
                else:
                    failed = True

            # Multiple solutions possible with similar cell dimensions
            elif problem_flag == "fix_cell":
                if ex:
                    potential_problems['run_command'](overrides={"fix_cell": True,
                                                                 "ignore_user_cell": True,
                                                                 "ignore_user_SG": True,
                                                                 "lattice_group": parsed_result[1],
                                                                 "labelit_solution": parsed_result[2]})
                else:
                    failed = True

            # Rest of the problems
            elif problem_flag in potential_problems:
                if ex:
                    potential_problems['run_command'](overrides=ex)
                else:
                    failed = True

            # No solution
            else:
                failed = True

            # If failed, save the log and results
            if failed:
                self.log[iteration].append("\n%s\n" % er)
                self.results[iteration] = {"labelit_results": "FAILED"}

    def print_warning(self, warn_type):
        """ """

        if warn_type == "Eiger CBF":
            self.tprint("\nThe installation of Phenix you are running needs patched to be used for \
Eiger HDF5 files that have been converted to CBFs.\nInstructions for patching are in \
$RAPD_HOME/install/sources/cctbx/README.md\n",
                        level=50,
                        color="red")

    def postprocess(self):
        """
        Send back the results and logs.
        """
        if self.verbose and self.logger:
            self.logger.debug("RunLabelit::postprocess")

        # Pass back output
        self.output.put(self.results)
        # Pass back the logs
        if self.nrun == 'all':
            self.output.put(self.log)

    def labelit_run_queue(self):
        """
        Run Queue for Labelit.
        """
        self.logger.debug('RunLabelit::labelit_run_queue')

        kill_jobs = True
        timer = 0
        start_time = time.time()

        ellapsed_time = time.time() - start_time
        current_progress = 0

        while ellapsed_time < global_vars.LABELIT_TIMEOUT:
            prog = int(7*ellapsed_time / 50)
            if prog > current_progress:
                self.tprint(prog*10, "progress")
                current_progress = prog
            if not self.indexing_results_queue.empty():
                result = self.indexing_results_queue.get(False)
                # join the Process
                self.jobs[result["tag"]].join()
                # Remove jobid from running jobs
                del self.jobids[result["tag"]]
                # Postprocess the labelit job
                self.postprocess_labelit(raw_result=result)
                # All jobs have finished
                if not len(self.jobids.keys()):
                    # print "All jobs done"
                    kill_jobs = False
                    break
            if self.tot_runs == 1:
                # For beam center plugin, slow it down
                time.sleep(1)
            else:
                time.sleep(0.1)
            ellapsed_time = time.time() - start_time

        if kill_jobs:
            # Make sure all jobs are killed
            for i, pid in self.jobids.iteritems():
                self.results[i] = {"labelit_results": "FAILED"}
                self.kill_job(pid, self.logger)


    def condense_logs(self):
        """Put the Labelit logs together"""

        self.logger.debug("RunLabelit::condense_logs")

        for iteration in range(self.tot_runs):
            # pprint(self.log[iteration])
            if iteration in self.log:
                header_line = "-------------------------\nLABELIT ITERATION %s\n-------------------\
------\n" % iteration
                if iteration == 0:
                    self.log["run1"] = ["\nRun 1\n"]
                self.log["run1"].append(header_line)
                self.log["run1"].extend(self.log[iteration])
                self.log["run1"].append("\n")
            else:
                self.log["run1"].append("\nLabelit iteration %s FAILED\n" % iteration)

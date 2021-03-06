"""
An autoindex & strategy rapd_agent
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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

# This is an active rapd agent
RAPD_AGENT = True

# This handler's request type
AGENT_TYPE = "AUTOINDEX+STRATEGY"
AGENT_SUBTYPE = "CORE"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "3b3448aee4a811e59c0aac87a3333966"
VERSION = "2.0.0"

# Standard imports
from collections import OrderedDict
import logging
from multiprocessing import Process, Queue, Event
import numpy
import os
from pprint import pprint
import shutil
import subprocess
import sys
import time

# RAPD imports
import subcontractors.parse as Parse
import subcontractors.summary as Summary
from subcontractors.xoalign import RunXOalign
from utils.communicate import rapd_send
from utils.modules import load_module
import utils.xutils as Utils
from utils.text import json
from bson.objectid import ObjectId

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

BEST_LINES = {

}

class RapdAgent(Process):
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

    # For testing individual modules (Will not run in Test mode on cluster!! Can be set at end of __init__.)
    test = False

    # Removes junk files and directories at end. (Will still clean on cluster!! Can be set at end of __init__.)
    clean = False

    # Runs in RAM (slightly faster), but difficult to debug.
    ram = False

    # Will not use RAM if self.cluster_use=True since runs would be on separate nodes. Slower (>10%).
    cluster_use = False

    # Switch for verbose
    verbose = True

    # Number of Labelit iterations to run.
    iterations = 6

    # This is where I place my overall folder settings.
    working_dir = False
    auto_summary = False
    labelit_log = {}
    labelit_results = {}
    labelit_summary = False
    labelit_failed = False
    distl_log = []
    distl_results = {}
    distl_summary = False
    raddose_results = False
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
    vips_images = {}

    # The results of the agent
    results = {}

    def __init__(self, site, command, tprint=False, logger=False):
        """
        Initialize the agent

        Keyword arguments
        site -- full site settings
        command -- dict of all information for this agent to run
        """
        # Save the start time
        self.st = time.time()

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
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        # Some logging
        self.logger.info(site)
        self.logger.info(command)

        # Store passed-in variables
        self.site = site
        self.command = command
        self.reply_address = self.command["return_address"]

        # Setting up data input
        self.setup = self.command["directories"]
        self.header = self.command["header1"]
        self.header2 = self.command.get("header2", False)
        self.site_parameters = self.command.get("site_parameters", False)
        self.preferences = self.command.get("preferences", {})
        self.controller_address = self.reply_address

        # pprint(self.preferences)

        # Assumes that Core sent job if present. Overrides values for clean and test from top.
        if self.site_parameters != False:
            self.gui = True
            self.test = False
            self.clean = False
        else:
            # If running from command line, site_parameters is not in there. Needed for BEST.
            if self.site:
                self.site_parameters = self.site.BEAM_INFO.get(
                    Utils.get_site(self.header['fullname'],
                    False)[1])
            else:
                self.site_parameters = self.preferences.get("site_parameters", False)
                # Sets settings so I can view the HTML output on my machine (not in the RAPD GUI),
                # and does not send results to database.
                self.gui = False

	    # Load the appropriate cluster adapter or set to False
        if self.cluster_use:
            self.cluster_adapter = Utils.load_cluster_adapter(self)
            self.cluster_queue = self.cluster_adapter.check_queue(self.command["command"])
        else:
            self.cluster_adapter = False
            self.cluster_queue = False

        # Set timer for distl. "False" will disable.
        if self.header2:
            self.distl_timer = 60
        else:
            self.distl_timer = 30

        # Set strategy timer. "False" disables.
        self.strategy_timer = False

        # Set timer for XOAlign. "False" will disable.
        self.xoalign_timer = 30

        # Turns on multiprocessing for everything
        # Turns on all iterations of Labelit running at once, sorts out highest symmetry solution,
        # then continues...(much better!!)
        self.multiproc = self.preferences.get("multiprocessing", True)

	    # Set for Eisenberg peptide work.
        self.sample_type = self.preferences.get("sample_type", "Protein")
        if self.sample_type == "Peptide":
            self.peptide     = True
        else:
            self.peptide     = False

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
        """
        # This is where I place my overall folder settings.
        self.working_dir                        = False
        # This is where I have chosen to place my results
        self.auto_summary                       = False
        self.labelit_log                        = {}
        self.labelit_results                    = {}
        self.labelit_summary                    = False
        self.labelit_failed                     = False
        self.distl_log                          = []
        self.distl_results                      = {}
        self.distl_summary                      = False
        self.raddose_results                    = False
        self.raddose_summary                    = False
        self.best_log                           = []
        self.best_results                       = False
        self.best_summary                       = False
        self.best1_summary                      = False
        self.best_summary_long                  = False
        self.best_anom_log                      = []
        self.best_anom_results                  = False
        self.best_anom_summary                  = False
        self.best1_anom_summary                 = False
        self.best_anom_summary_long             = False
        self.best_failed                        = False
        self.best_anom_failed                   = False
        self.rerun_best                         = False
        self.mosflm_strat_log                   = []
        self.mosflm_strat_anom_log              = []
        self.mosflm_strat_results               = {}
        self.mosflm_strat_anom_results          = {}
        self.mosflm_strat_summary               = False
        self.mosflm_strat1_summary              = False
        self.mosflm_strat_summary_long          = False
        self.mosflm_strat_anom_summary          = False
        self.mosflm_strat1_anom_summary         = False
        self.mosflm_strat_anom_summary_long     = False
        # Labelit settings
        self.index_number                       = False
        self.ignore_user_SG                     = False
        self.pseudotrans                        = False
        # Raddose settings
        self.volume                             = False
        self.calc_num_residues                  = False
        # Mosflm settings
        self.prev_sg                            = False
        # Extra features for BEST
        self.high_dose                          = False
        self.crystal_life                       = None
        self.iso_B                              = False
        # Dicts for running the Queues
        self.jobs                               = {}
        self.vips_images                        = {}
        """
        # Settings for all programs
        #self.beamline = self.header.get("beamline")
        self.time = str(self.header.get("time", "1.0"))
        self.wavelength = str(self.header.get("wavelength"))
        self.transmission = str(self.header.get("transmission", 10))
        # self.aperture = str(self.header.get("md2_aperture"))
        self.spacegroup = self.preferences.get("spacegroup", False)
        self.flux = str(self.header.get("flux",'3E10'))
        self.solvent_content = str(self.preferences.get("solvent_content", 0.55))

        Process.__init__(self, name="AutoindexingStrategy")

        self.start()

    def run(self):
        """
        Convoluted path of modules to run.
        """

        if self.verbose:
            self.logger.debug("AutoindexingStrategy::run")

        self.tprint(arg="\nStarting indexing procedures", level=99, color="blue")

        # Check if h5 file is input and convert to cbf's.
        if self.header["fullname"][-3:] == ".h5":
            if self.convert_images() == False:
                # If conversion fails, kill the job.
                self.postprocess()

        self.preprocess()

        if self.minikappa:
            self.processXOalign()
        else:

            # Run Labelit
            self.processLabelit()

      	    # Sorts labelit results by highest symmetry.
            self.labelitSort()

            # If there is a solution, then calculate a strategy.
            if self.labelit_failed == False:

                # Start distl.signal_strength for the correct labelit iteration
                self.processDistl()
                if self.multiproc == False:
                    self.postprocessDistl()
                self.preprocessRaddose()
                self.processRaddose()
                self.processStrategy()
                self.run_queue()

                # Get the distl_results
                if self.multiproc:
                    self.postprocessDistl()

            # Pass back results, and cleanup.
            self.postprocess()

    def preprocess(self):
        """
        Setup the working dir in the RAM and save the dir where the results will go at the end.
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::preprocess")

        # Determine detector vendortype
        self.vendortype = Utils.getVendortype(self, self.header)
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

        # Setup event for job control on cluster (Only works at NE-CAT using DRMAA for
        # job submission)
        if self.cluster_adapter:
            self.running = Event()
            self.running.set()

    def preprocessRaddose(self):
        """
        Create the raddose.com file which will run in processRaddose. Several beamline specific entries for flux and
        aperture size passed in from rapd_site.py
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::preprocessRaddose")

        # try:
        beam_size_x = False
        beam_size_y = False
        gauss_x = False
        gauss_y = False

        # Get unit cell
        cell = Utils.getLabelitCell(self)
        nres = Utils.calcTotResNumber(self,self.volume)
        # Adding these typically does not change the Best strategy much, if it at all.
        patm = False
        satm = False
        if self.sample_type == "Ribosome":
            crystal_size_x = "1"
            crystal_size_y = "0.5"
            crystal_size_z = "0.5"
        else:
            # crystal dimensions (default 0.1 x 0.1 x 0.1 from rapd_site.py)
            crystal_size_x = str(float(self.preferences.get("crystal_size_x", 100))/1000.0)
            crystal_size_y = str(float(self.preferences.get("crystal_size_y", 100))/1000.0)
            crystal_size_z = str(float(self.preferences.get("crystal_size_z", 100))/1000.0)
        if self.header.has_key("flux"):
            beam_size_x = str(self.header.get("beam_size_x"))
            beam_size_y = str(self.header.get("beam_size_y"))
            gauss_x     = str(self.header.get("gauss_x"))
            gauss_y     = str(self.header.get("gauss_y"))
        raddose = open("raddose.com", "w+")
        setup = "raddose << EOF\n"
        if beam_size_x and beam_size_y:
            setup += "BEAM %s %s\n" % (beam_size_x, beam_size_y)
        # Full-width-half-max of the beam
        if gauss_x and gauss_y:
            setup += "GAUSS %s %s\nIMAGES 1\n" % (gauss_x, gauss_y)
        setup += "PHOSEC %s\n" % self.flux
        setup += "EXPOSURE %s\n" % self.time
        if cell:
            setup += "CELL %s %s %s %s %s %s\n" % (cell[0], cell[1], cell[2], cell[3], cell[4], cell[5])
        else:
            self.logger.debug("Could not get unit cell from bestfile.par")

        # Set default solvent content based on sample type. User can override.
        if self.solvent_content == "0.55":
            if self.sample_type == "Protein":
                setup += "SOLVENT 0.55\n"
            else:
                setup += "SOLVENT 0.64\n"
        else:
            setup += "SOLVENT %s\n"%self.solvent_content
        # Sets crystal dimensions. Input from dict (0.1 x 0.1 x 0.1 mm), but user can override.
        if crystal_size_x and crystal_size_y and crystal_size_z:
            setup += "CRYSTAL %s %s %s\n" % (crystal_size_x, crystal_size_y, crystal_size_z)
        if self.wavelength:
            setup += "WAVELENGTH %s\n" % self.wavelength
        setup += "NMON 1\n"
        if self.sample_type == "Protein":
            setup += "NRES %s\n" % nres
        elif self.sample_type == "DNA":
            setup += "NDNA %s\n" % nres
        else:
            setup += "NRNA %s\n" % nres
        if patm:
            setup += "PATM %s\n" % patm
        if satm:
            setup += "SATM %s\n" % satm
        setup += "END\nEOF\n"
        raddose.writelines(setup)
        raddose.close()

        # except:
            # self.logger.exception("**ERROR in preprocessRaddose**")

    def processLabelit(self):
        """
        Initiate Labelit runs.
        """

        if self.verbose:
            self.logger.debug("AutoindexingStrategy::runLabelit")

        self.tprint(arg="  Starting Labelit runs", level=99, color="white")

        try:
            # Setup queue for getting labelit log and results in labelitSort.
            self.labelitQueue = Queue()
            params = {}
            params["test"] = self.test
            params["cluster"] = self.cluster_adapter
            params["verbose"] = self.verbose
            params["cluster_queue"] = self.cluster_queue
            params["vendortype"] = self.vendortype
            if self.working_dir == self.dest_dir:
                command = self.command
            else:
                command = self.command.copy()
                command["directories"]["work"] = self.working_dir

            # Launch labelit
            Process(target=RunLabelit, args=(command, self.labelitQueue, params, self.tprint, self.logger)).start()

        except:
            self.logger.exception("**Error in processLabelit**")

    def processXDSbg(self):
        """
        Calculate the BKGINIT.cbf for the background calc on the Pilatus. This is
        used in BEST.
        Gleb recommended this but it does not appear to make much difference except take longer.
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::processXDSbg")

        try:
            name = str(self.header.get("fullname"))
            temp = name[name.rfind("_")+1:name.rfind(".")]
            new_name = name.replace(name[name.rfind("_")+1:name.rfind(".")],len(temp)*"?")
            #range = str(int(temp))+" "+str(int(temp))
            command  = "JOB=XYCORR INIT\n"
            command += Utils.calcXDSbc(self)
            command += "DETECTOR_DISTANCE=%s\n" % self.header.get("distance")
            command += "OSCILLATION_RANGE=%s\n" % self.header.get("osc_range")
            command += "X-RAY_WAVELENGTH=%s\n" % self.wavelength
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
            Process(target=Utils.processLocal, args=("xds_par", self.logger)).start()

        except:
            self.logger.exception("**Error in ProcessXDSbg.**")

    def processDistl(self):
        """
        Setup Distl for multiprocessing if enabled.
        """
        if self.verbose:
            self.logger.debug('AutoindexingStrategy::processDistl')
        try:
            self.distl_output = []
            l = ["", "2"]
            f = 1
            if self.header2:
                f = 2
            for i in range(0, f):
                if self.test:
                    inp = "ls"
                    job = Process(target=Utils.processLocal, args=(inp, self.logger))
                else:
                    inp = "distl.signal_strength %s" % eval("self.header%s" % l[i]).get("fullname")
                    job = Process(target=Utils.processLocal,args=((inp, "distl%s.log" % i), self.logger))
                job.start()
                self.distl_output.append(job)

        except:
            self.logger.exception("**Error in ProcessDistl**")

    def processRaddose(self):
        """
        Run Raddose.
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::processRaddose")

        self.raddose_log = []
        try:
            self.raddose_log.append("tcsh raddose.com\n")
            output = subprocess.Popen("tcsh raddose.com", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output.wait()
            for line in output.stdout:
                self.raddose_log.append(line)

        except:
            self.logger.exception("**ERROR in processRaddose**")

        raddose = Parse.ParseOutputRaddose(self, self.raddose_log)
        self.raddose_results = {"raddose_results":raddose}
        if self.raddose_results["raddose_results"] == None:
            self.raddose_results = {"raddose_results":"FAILED"}
            if self.verbose:
                self.logger.debug("Raddose failed")

    def processBest(self, iteration=0, best_version="3.2.0", runbefore=False):
        """
        Construct the Best command and run. Passes back dict with PID:anom.

        Best versions known 3.2.0, 3.4.4
        """

        # print "processBest"

        if self.verbose:
            self.logger.debug("AutoindexingStrategy::processBest %s", best_version)

        # try:
        max_dis = self.site_parameters.get("DETECTOR_DISTANCE_MAX")
        min_dis = self.site_parameters.get("DETECTOR_DISTANCE_MIN")
        min_d_o = self.site_parameters.get("DIFFRACTOMETER_OSC_MIN")
        min_e_t = self.site_parameters.get("DETECTOR_TIME_MIN")

        # Get image numbers
        try:
            counter_depth = self.header["image_template"].count("?")
        except KeyError:
            raise Exception("Header information missing image_template")

        # Make sure that the file from labelit is properly named
        print "Checking for hkl files"
        if not os.path.exists("%s_%s.hkl" % (self.index_number, (("%0"+str(counter_depth)+"d") % image_number))):
            print "Missing hkl file for counter_depth %d" % counter_depth
            for attempted_counter_depth in (3, 4, 5, 6):
                if os.path.exists("%s_%s.hkl" % (self.index_number, (("%0"+str(attempted_counter_depth)+"d") % image_number))):
                    print "Found hkl file at counter depth of %d" % attempted_counter_depth
                    counter_depth = attempted_counter_depth
                    break

        image_number_format = "%0"+str(counter_depth)+"d"
        image_number = [image_number_format % self.header["image_number"],]
        # image_number.append(self.header.get('fullname')[self.header.get('fullname').rfind('_')+1:self.header.get('fullname').rfind('.')])
        if self.header2:
            image_number.append(image_number_format % self.header2["image_number"])
            # image_number.append(self.header2.get('fullname')[self.header2.get('fullname').rfind('_')+1:self.header2.get('fullname').rfind('.')])

        print self.header["image_template"], counter_depth
        print image_number_format, image_number

        # Tell Best if two-theta is being used.
        if int(float(self.header.get("twotheta", 0))) != 0:
            Utils.fixBestfile(self)

        # If Raddose failed, here are the defaults.
        dose = 100000.0
        exp_dose_lim = 300
        if self.raddose_results:
            if self.raddose_results.get("raddose_results") != 'FAILED':
                dose = self.raddose_results.get("raddose_results").get('dose per image')
                exp_dose_lim = self.raddose_results.get("raddose_results").get('exp dose limit')

        # Set how many frames a crystal will last at current exposure time.
        self.crystal_life = str(int(float(exp_dose_lim) / float(self.time)))
        if self.crystal_life == '0':
            self.crystal_life = '1'
        # Adjust dose for ribosome crystals.
        if self.sample_type == 'Ribosome':
            dose = 500001
        # If dose is too high, warns user and sets to reasonable amount and reruns Best but give warning.
        if dose > 500000:
            dose = 500000
            exp_dose_lim = 100
            self.high_dose = True
            if iteration == 1:
                dose = 100000.0
                exp_dose_lim = 300
            if iteration == 2:
                dose = 100000.0
                exp_dose_lim = False
            if iteration == 3:
                dose = False
                exp_dose_lim = False

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
        if self.high_dose:
            command += ' -t 1.0'
        else:
            command += " -t %s" % self.time
        command += ' -e %s -sh %s -su %s' % (self.preferences.get('best_complexity', 'none'),\
                                             self.preferences.get('shape', '2.0'), self.preferences.get('susceptibility', '1.0'))
        if self.preferences.get('aimed_res') != 0.0:
            command += ' -r %s' % self.preferences.get('aimed_res')
        if best_version >= "3.4":
            command += ' -Trans %s' % self.transmission
        # Set minimum rotation width per frame. Different for PAR and CCD detectors.
        command += ' -w %s' % min_d_o
        # Set minimum exposure time per frame.
        command += ' -M %s' % min_e_t
        # Set min and max detector distance
        if best_version >= "3.4":
            command += ' -DIS_MAX %s -DIS_MIN %s' % (max_dis, min_dis)
        # Fix bug in BEST for PAR detectors. Use the cumulative completeness of 99% instead of all bin.
        if self.vendortype in ('Pilatus-6M', 'ADSC-HF4M'):
            command += ' -low never'
        # set dose  and limit, else set time
        if best_version >= "3.4" and dose:
            command += ' -GpS %s -DMAX 30000000'%dose
        else:
            command += ' -T 185'
        if runbefore:
            command += ' -p %s %s' % (runbefore[0], runbefore[1])
        command1 = command
        command1 += ' -a -o best_anom.plt -dna best_anom.xml'
        command += ' -o best.plt -dna best.xml'
        print image_number, image_number[0]
        end = ' -mos bestfile.dat bestfile.par %s_%s.hkl ' % (self.index_number, image_number[0])
        print end
        """
        if self.pilatus:
          if os.path.exists(os.path.join(self.working_dir,'BKGINIT.cbf')):
            end = ' -MXDS bestfile.par BKGINIT.cbf %s_%s.hkl ' % (self.index_number,image_number[0])
        """
        if self.header2:
            end += '%s_%s.hkl' % (self.index_number, image_number[1])
        command  += end
        command1 += end
        d = {}
        jobs = {}
        l = [(command, ''), (command1, '_anom')]
        st  = 0
        end1 = 2
        if runbefore:
            st  = runbefore[2]
            end1 = runbefore[3]

        # print l
        for i in range(st, end1):
            log = os.path.join(os.getcwd(), "best%s.log" % l[i][1])
            if self.verbose:
                self.logger.debug(l[i][0])
            # Save the path of the log
            d.update({'log'+l[i][1]:log})
            if self.test == False:
                if self.cluster_use:
                    jobs[str(i)] = Process(target=self.cluster_adapter.processCluster,
                                           args=(self, (l[i][0], log, self.cluster_queue)))
                else:
                    jobs[str(i)] = Process(target=BestAction,
                                           args=((l[i][0], log), self.logger))
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
                            start, ran = self.findBestStrat(d['log'+l[int(job)][1]].replace('log', 'plt'))
                            if start != False:
                                pass
                                # self.processBest(iteration, (start, ran, int(job), int(job)+1))
                            counter -= 1
                    time.sleep(0.1)

        # except:
        #     self.logger.exception('**Error in processBest**')

    def processMosflm(self):
        """
        Creates Mosflm executable for running strategy and run. Passes back dict with PID:logfile.
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::processMosflm")

        try:
            l = [("mosflm_strat", "", ""), ("mosflm_strat_anom", "_anom", "ANOMALOUS")]
            # Opens file from Labelit/Mosflm autoindexing and edit it to run a strategy.
            mosflm_rot = str(self.preferences.get("mosflm_rot", "0.0"))
            mosflm_seg = str(self.preferences.get("mosflm_seg", "1"))
            mosflm_st = str(self.preferences.get("mosflm_start", "0.0"))
            mosflm_end = str(self.preferences.get("mosflm_end", "360.0"))

            # Does the user request a start or end range?
            range1 = False
            if mosflm_st != "0.0":
                range1 = True
            if mosflm_end != "360.0":
                range1 = True
            if range1:
                if mosflm_rot == "0.0":
                    # mosflm_rot = str(360/float(Utils.symopsSG(self,Utils.getMosflmSG(self))))
                    mosflm_rot = str(360/float(Utils.symopsSG(self, Utils.getLabelitCell(self, "sym"))))
            # Save info from previous data collections.
            if self.multicrystalstrat:
                ref_data = self.preferences.get("reference_data")
                if self.spacegroup == False:
                    self.spacegroup = ref_data[0][-1]
                    Utils.fixMosflmSG(self)
                    # For posting in summary
                    self.prev_sg = True
            else:
                ref_data = False

            # Run twice for regular and anomalous strategies.
            for i in range(0, 2):
                shutil.copy(self.index_number, l[i][0])
                temp = []
                # Read the Mosflm input file from Labelit and use only the top part.
                for x, line in enumerate(open(l[i][0], "r").readlines()):
                    temp.append(line)
                    if line.count("ipmosflm"):
                        newline = line.replace(self.index_number, l[i][0])
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
                    new_line += "STRATEGY START %s END %s\nGO\n" % (mosflm_st, mosflm_end)
                    new_line += "ROTATE %s SEGMENTS %s %s\n" % (mosflm_rot, mosflm_seg, l[i][2])
                else:
                    if mosflm_rot == "0.0":
                        new_line += "STRATEGY AUTO %s\n"%l[i][2]
                    elif mosflm_seg != "1":
                        new_line += "STRATEGY AUTO ROTATE %s SEGMENTS %s %s\n" % (mosflm_rot, mosflm_seg, l[i][2])
                    else:
                        new_line += "STRATEGY AUTO ROTATE %s %s\n" % (mosflm_rot, l[i][2])
                new_line += "GO\nSTATS\nEXIT\neof\n"
                if self.test == False:
                    new = open(l[i][0], "w")
                    new.writelines(temp[:fi+1])
                    new.writelines(new_line)
                    new.close()
                    log = os.path.join(os.getcwd(), l[i][0]+".out")
                    inp = "tcsh %s" % l[i][0]
                    if self.cluster_adapter:
                        Process(target=self.cluster_adapter.processCluster,
                                args=(self,
                                      (inp, log, self.cluster_queue)
                                      )
                                ).start()
                    else:
                        Process(target=Utils.processLocal, args=(inp, self.logger)).start()

        except:
            self.logger.exception("**Error in processMosflm**")

    def check_best_detector(self, detector):
        """Check that the detector we need is in the BEST configuration file"""

        best_executable = subprocess.check_output(["which", "best"])
        detector_info = os.path.join(os.path.dirname(best_executable),
                                     "detector-inf.dat")

        # Read the detector info file to see if the detector is in it
        lines = open(detector_info, "r").readlines()
        found = False
        for line in lines:
            # print line.rstrip()
            if line.startswith(detector):
                found = True
                break
            elif line.startswith("end"):
                break

        if not found:
            self.tprint(arg="Detector %s missing from the BEST detector information file %s" % (detector, detector_info),
                        level=30,
                        color="red")
            self.print_best_detector_line(detector)

    def print_best_detector_line(self, detector):
        """Print the line that needs to be added to the best detector inf file"""

        pass

    def processStrategy(self, iteration=False):
        """
        Initiate all the strategy runs using multiprocessing.

        Keyword arguments
        iteration -- (default False)
        """

        if self.verbose:
            self.logger.debug("AutoindexingStrategy::processStrategy")

        self.tprint(arg="\nStarting strategy calculations", level=99, color="blue")

        # try:
        if iteration:
            st = iteration
            end = iteration+1
        else:
            st = 0
            end = 5
            if self.strategy == "mosflm":
                st = 4
            if self.multiproc == False:
                end = st+1

        # Get the Best version for this machine
        best_version = Utils.getBestVersion()

        # Make sure that the BEST install has the detector
        self.check_best_detector(DETECTOR_TO_BEST.get(self.header.get("detector"), None))

        for i in range(st, end):
            if i == 1:
                self.tprint(arg="  Starting BEST runs", level=99, color="white")
            if i == 4:
                self.tprint(arg="  Starting Mosflm runs", level=99, color="white")
                Utils.folders(self, self.labelit_dir)
                job = Process(target=self.processMosflm, name="mosflm%s" % i)
            else:
                Utils.foldersStrategy(self, os.path.join(os.path.basename(self.labelit_dir), str(i)))
                # Reduces resolution and reruns Mosflm to calc new files, then runs Best.
                job = Process(target=Utils.errorBest, name="best%s" % i, args=(self, i, best_version))
            job.start()
            self.jobs[str(i)] = job

        # except:
        #     self.logger.exception("**Error in processStrategy**")

    def processXOalign(self):
        """
        Run XOalign using rapd_agent_xoalign.py
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::processXOalign")

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
            self.logger.exception("**ERROR in processXOalign**")

    def postprocessDistl(self):
        """
        Send Distl log to parsing and make sure it didn't fail. Save output dict.
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::postprocessDistl")

        try:
            timer = 0
            while len(self.distl_output) != 0:
                for job in self.distl_output:
                    if job.is_alive() == False:
                        self.distl_output.remove(job)
                time.sleep(0.2)
                timer += 0.2
                if self.verbose:
                    number = round(timer % 1, 1)
                    if number in (0.0, 1.0):
                        pass
                        # print "Waiting for Distl to finish %s seconds" % timer
                if self.distl_timer:
                    if timer >= self.distl_timer:
                        job.terminate()
                        self.distl_output.remove(job)
                        self.distl_log.append("Distl timed out\n")
                        if self.verbose:
                            self.tprint(arg="Distl timed out", level=30, color="red")
                            self.logger.error("Distl timed out.")

            os.chdir(self.labelit_dir)
            f = 1
            if self.header2:
                f = 2
            for x in range(0, f):
                log = open("distl%s.log" % x, "r").readlines()
                self.distl_log.extend(log)
                distl = Parse.ParseOutputDistl(self, log)
                if distl == None:
                    self.distl_results = {"distl_results":"FAILED"}
                    self.tprint(arg="  DISTL analysis failed", level=30, color="red")
                else:
                    self.distl_results[str(x)] = {"distl_results": distl}

            Utils.distlComb(self)

            # pprint.pprint(self.distl_results)

            # Print DISTL results to commandline - verbose only
            self.tprint(arg="\nDISTL analysis results", level=10, color="blue")
            distl_results = self.distl_results["distl_results"]
            if len(distl_results["distl res"]) == 2:
                self.tprint(arg="  %21s  %6s %6s" % ("", "image 1", "image 2"), level=10, color="white")
                format_string = "  %21s: %6s  %6s"
            else:
                format_string = "  %21s: %s"

            distl_labels = {
                "total spots": "Total Spots",
                "spots in res": "Spots in Resolution",
                "good Bragg spots": "Good Bragg Spots",
                "overloads": "Overloaded Spots",
                "distl res": "DISTL Resolution",
                "labelit res": "Labelit Resolution",
                "max cell": "Max Cell",
                "ice rings": "Ice Rings",
                "min signal strength": "Min Signal Strength",
                "max signal strength": "Max Signal Strength",
                "mean int signal": "Mean Intensity Signal",
            }
            distl_labels = OrderedDict([
                ("total spots", "Total Spots"),
                ("spots in res", "Spots in Resolution"),
                ("good Bragg spots", "Good Bragg Spots"),
                ("overloads", "Overloaded Spots"),
                ("distl res", "DISTL Resolution"),
                ("labelit res", "Labelit Resolution"),
                ("max cell", "Max Cell"),
                ("ice rings", "Ice Rings"),
                ("min signal strength", "Min Signal Strength"),
                ("max signal strength", "Max Signal Strength"),
                ("mean int signal", "Mean Intensity Signal"),
                ])

            for key, val in distl_labels.iteritems():
                vals = tuple([val] + distl_results[key])
                # print format_string % vals
                self.tprint(arg=format_string % vals, level=10, color="white")

        except:
            self.logger.exception("**Error in postprocessDistl**")

    def postprocessBest(self, inp, runbefore=False):
        """
        Send Best log to parsing and save output dict. Error check the results and
        rerun if neccessary.

        Keyword arguments
        inp --
        runbefore -- (default False)
        """

        if self.verbose:
            self.logger.debug("AutoindexingStrategy::postprocessBest")

        try:
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

        except:
            self.logger.exception("**Error in postprocessBest.**")

        data = Parse.ParseOutputBest(self, (log, xml), anom)
        # print data.get("strategy res limit")

        if self.labelit_results["labelit_results"] != "FAILED":
            # Best error checking. Most errors caused by B-factor calculation problem.
            # If no errors...
            if type(data) == dict:
                data.update({"directory":os.path.dirname(inp)})
                if anom:
                    self.best_anom_results = {"best_results_anom":data}
                else:
                    self.best_results = {"best_results_norm":data}

                # Print to terminal
                # pprint.pprint(data)
                if "strategy anom flag" in data:
                    flag = "strategy "
                    self.tprint(arg="\nBEST strategy standard", level=99, color="blue")
                else:
                    flag = "strategy anom "
                    self.tprint(arg="\nBEST strategy ANOMALOUS", level=99, color="blue")
                # Header lines
                self.tprint(arg="  " + "-" * 85, level=99, color="white")
                self.tprint(arg="  " + " N |  Omega_start |  N.of.images | Rot.width |  Exposure | Distance | % Transmission", level=99, color="white")
                self.tprint(arg="  " + "-" * 85, level=99, color="white")
                for i in range(len(data[flag+"run number"])):
                    self.tprint(
                        arg="  %2d |    %6.2f    |   %6d     |   %5.2f   |   %5.2f   | %7s  |     %3.2f      |" %
                            (
                                int(data[flag+"run number"][i]),
                                float(data[flag+"phi start"][i]),
                                int(data[flag+"num of images"][i]),
                                float(data[flag+"delta phi"][i]),
                                float(data[flag+"image exp time"][i]),
                                str(data[flag+"distance"][i]),
                                float(data[flag+"new transmission"][i])
                            ),
                        level=99,
                        color="white")
                self.tprint(arg="  " + "-" * 85, level=99, color="white")

                return("OK")
            # BEST has failed
            else:
                if self.multiproc == False:
                    out = {"None":"No Best Strategy.",
                           "neg B":"Adjusting resolution",
                           "isotropic B":"Isotropic B detected"}
                    if out.has_key(data):
                        Utils.errorBestPost(self, iteration, out[data],anom)
                self.tprint(arg="BEST unable to calculate a strategy", level=30, color="red")
                # print data
                return("FAILED")

    def postprocessMosflm(self, inp):
        """
        Pass Mosflm log into parsing and save output dict.

        Keyword argument
        inp -- name of log file to interrogate
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::postprocessMosflm %s" % inp)

        try:
            if inp.count("anom"):
                l = ["ANOM", "self.mosflm_strat_anom", "Mosflm ANOM strategy results"]
            else:
                l = ["", "self.mosflm_strat", "Mosflm strategy results"]
            out = open(inp, "r").readlines()
            eval("%s_log" % l[1]).extend(out)
        except:
            self.logger.exception("**ERROR in postprocessMosflm**")

        data = Parse.ParseOutputMosflm_strat(self, out, inp.count("anom"))

        # Print to terminal
        # pprint.pprint(data)
        if "run_number" in data:
            flag = "strategy "
            self.tprint(arg="\nMosflm strategy standard", level=99, color="blue")
        else:
            flag = "strategy anom "
            self.tprint(arg="\nMosflm strategy ANOMALOUS", level=99, color="blue")
        # Header lines
        self.tprint(arg="  " + "-" * 69, level=99, color="white")
        self.tprint(arg="  " + " N |  Omega_start |  N.of.images | Rot.width |  Exposure | Distance ", level=99, color="white")
        self.tprint(arg="  " + "-" * 69, level=99, color="white")
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
                level=99,
                color="white")
        self.tprint(arg="  " + "-" * 69, level=99, color="white")

        if data == None:
            if self.verbose:
                self.logger.debug("No Mosflm %s strategy.", l[0])
            eval("%s_results"%l[1]).update({l[2]:"FAILED"})
        elif data == "sym":
            if self.verbose:
                self.logger.debug("dataset symmetry not compatible with autoindex symmetry")
            self.tprint(arg="Dataset symmetry not compatible with autoindex symmetry", level=30, color="red")
            eval("%s_results"%l[1]).update({l[2]:"SYM"})
        else:
            eval("%s_results" % l[1]).update({l[2]:data})

    def run_queue(self):
        """
        run_queue for strategy.
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::run_queue")

        try:
            def set_best_results(i,x):
                # Set Best output if it failed after 3 tries
                if i == 3:
                    if x == 0:
                        self.best_results = {"best_results_norm":"FAILED"}
                        self.best_failed = True
                    else:
                        self.best_anom_results = {"best_results_anom":"FAILED"}
                        self.best_anom_failed = True

            st = 0
            if self.strategy == "mosflm":
                st = 4
            # dict = {}
            # Run twice for regular(0) and anomalous(1) strategies
            l = ["", "_anom"]
            for x in range(0, 2):
                for i in range(st, 5):
                    timed_out = False
                    timer = 0
                    job = self.jobs[str(i)]
                    while 1:
                        if job.is_alive() == False:
                            if i == 4:
                                log = os.path.join(self.labelit_dir, "mosflm_strat%s.out" % l[x])
                            else:
                                log = os.path.join(self.labelit_dir, str(i))+"/best%s.log" % l[x]
                            break
                        time.sleep(0.1)
                        timer += 0.1
                        if self.verbose:
                            number = round(timer%1,1)
                            if number in (0.0, 1.0):
                                self.tprint(arg="    Waiting for strategy to finish %s seconds" % timer, level=10, color="white")
                        if self.strategy_timer:
                            if timer >= self.strategy_timer:
                                timed_out = True
                                break
                    if timed_out:
                        self.tprint(arg="Strategy calculation timed out", level=30, color="red")
                        set_best_results(i, x)
                    else:
                        if i == 4:
                            self.postprocessMosflm(log)
                        else:
                            job1 = self.postprocessBest(log)
                            if job1 == "OK":
                                break
                            # If Best failed...
                            else:
                                if self.multiproc == False:
                                    self.processStrategy(i+1)
                                set_best_results(i, x)

            if self.test == False:
                if self.multiproc:
                    if self.cluster_adapter:
                        # kill child process on DRMAA job causes error on cluster.
                        # turn off multiprocessing.event so any jobs still running on cluster are terminated.
                        self.running.clear()
                    else:
                        # kill all the remaining running jobs
                        for i in range(st, 5):
                            if self.jobs[str(i)].is_alive():
                                if self.verbose:
                                    self.logger.debug("terminating job: %s" % self.jobs[str(i)])
                                Utils.killChildren(self, self.jobs[str(i)].pid)

        except:
            self.logger.exception("**Error in run_queue**")

    def convert_images(self):
        """
        Convert H5 files to CBF's for strategies.
        """
        if self.verbose:
          self.logger.debug('AutoindexingStrategy::convert_images')

        try:
          def run_convert(img, imgn=False):
            header = Utils.convert_hdf5_cbf(inp=img, imgn=imgn)
            l = ['run_id', 'twotheta', 'place_in_run', 'date', 'transmission','collect_mode']
            if type(header) == dict:
              for x in range(len(l)):
                del header[l[x]]
            return (header)

          self.header.update(run_convert(self.header['fullname'], imgn=1))
          if self.header2:
            self.header2.update(run_convert(self.header2['fullname'], imgn=2))
          return True

        except:
            self.logger.exception('**ERROR in convert_images**')
            return False

    def labelitSort(self):
        """
        Sort out which iteration of Labelit has the highest symmetry and choose that solution. If
        Labelit does not find a solution, finish up the pipeline.
        """

        if self.verbose:
            self.logger.debug("AutoindexingStrategy::labelitSort")

        rms_list1 = []
        sg_list1 = []
        metric_list1 = []
        vol = []
        sg_dict  = {}
        sol_dict = {}
        sym = "0"

        # try:
        # Get the results and logs
        self.labelit_results = self.labelitQueue.get()
        self.labelit_log = self.labelitQueue.get()

        for run in self.labelit_results.keys():
            if type(self.labelit_results[run].get("labelit_results")) == dict:
                #Check for pseudotranslation in any Labelit run
                if self.labelit_results[run].get("labelit_results").get("pseudotrans") == True:
                    self.pseudotrans = True
                s, r, m, v = Utils.getLabelitStats(self, inp=run, simple=True)
                sg = Utils.convertSG(self, s)
                sg_dict[run] = sg
                sg_list1.append(float(sg))
                rms_list1.append(float(r))
                metric_list1.append(float(m))
                vol.append(v)
            else:
                #If Labelit failed, set dummy params
                sg_dict[run] = "0"
                sg_list1.append(0)
                rms_list1.append(100)
                metric_list1.append(100)
                vol.append("0")
        for x in range(len(sg_list1)):
            if sg_list1[x] == numpy.amax(sg_list1):
                # If its P1 look at the Mosflm RMS, else look at the Labelit metric.
                if str(sg_list1[x]) == "1.0":
                    sol_dict[rms_list1[x]]    = self.labelit_results.keys()[x]
                else:
                    sol_dict[metric_list1[x]] = self.labelit_results.keys()[x]
        l = sol_dict.keys()
        l.sort()
        # Best Labelit_results key
        highest = sol_dict[l[0]]
        # Since iter 5 cuts res, it is often the best. Only choose if its the only solution.
        if len(l) > 1:
            if highest == "5":
                highest = sol_dict[l[1]]

        # symmetry of best solution
        sym = sg_dict[highest]

        # If there is a solution...
        if sym != "0":
            self.logger.debug("The sorted labelit solution was #%s", highest)

            # Save best results in corect place.
            self.labelit_results = self.labelit_results[highest]
            # pprint.pprint(self.labelit_results)

            # Set self.volume for best solution
            self.volume = vol[int(highest)]

            # Set self.labelit_dir and go to it.
            self.labelit_dir = os.path.join(self.working_dir, highest)
            self.index_number = self.labelit_results.get("labelit_results").get("mosflm_index")
            os.chdir(self.labelit_dir)
            if self.spacegroup != False:
                check_lg = Utils.checkSG(self, sym)
                user_sg  = Utils.convertSG(self, self.spacegroup)
                if user_sg != sym:
                    fixSG = False
                    for line in check_lg:
                        if line == user_sg:
                            fixSG = True
                    if fixSG:
                        Utils.fixMosflmSG(self)
                        Utils.fixBestSG(self)
                    else:
                        self.ignore_user_SG = True

            # Print Labelit results to commandline
            self.tprint(arg="Highest symmetry Labelit result", level=99, color="blue")
            for line in self.labelit_results["labelit_results"]["output"][5:]:
                self.tprint(arg="  %s" % line.rstrip(), level=99, color="white")
            # pprint.pprint(self.labelit_results["labelit_results"]["output"])

        # No Labelit solution
        else:
            self.logger.debug("No solution was found when sorting Labelit results.")
            self.tprint(arg="Labelit failed to index", level=30, color="red")
            self.labelit_failed = True
            self.labelit_results = {"labelit_results":"FAILED"}
            self.labelit_dir = os.path.join(self.working_dir, "0")
            os.chdir(self.labelit_dir)
            self.processDistl()
            self.postprocessDistl()
            #   if os.path.exists("DISTL_pickle"):
              #   self.makeImages(2)
            self.best_failed = True
            self.best_anom_failed = True

        # except:
        #     self.logger.exception("**ERROR in labelitSort**")

    def findBestStrat(self, inp):
        """
        Find the BEST strategy according to the plots.
        """

        if self.verbose:
            self.logger.debug('AutoindexingStrategy::findBestStrat')

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
                    return('FAILED')
                else:
                    return(int(round(float(p_e)-float(p_s[0]))))
            except:
                self.logger.exception('**Error in getBestRotRange**')
                return('FAILED')

        try:
            phi_st = []
            phi_rn = []
            st  = False
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
                return((str(phi_st[phi_rn.index(min1)]), str(min1)))
            else:
                return((False, False))

        except:
            self.logger.exception('**Error in findBestStrat**')
            return((False, False))

    def print_info(self):
        """
        Print information regarding programs utilized by RAPD
        """
        if self.verbose:
            self.logger.debug('AutoindexingStrategy::print_info')

        # try:
        self.tprint(arg="\nRAPD index & strategy uses:", level=99, color="blue")

        info_string = """    Phenix
    Reference: J. Appl. Cryst. 37, 399-409 (2004)
    Website:   http://adder.lbl.gov/labelit/ \n
    Mosflm
    Reference: Leslie, A.G.W., (1992), Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No. 26
    Website:   http://www.mrc-lmb.cam.ac.uk/harry/mosflm/ \n
    RADDOSE
    Reference: Paithankar et. al. (2009) J. Synch. Rad. 16, 152-162.
    Website:   http://biop.ox.ac.uk/www/garman/lab_tools.html/ \n
    Best
    Reference: G.P. Bourenkov and A.N. Popov,  Acta Cryst. (2006). D62, 58-64
    Website:   http://www.embl-hamburg.de/BEST/"""
        self.tprint(arg=info_string, level=99, color="white")

        self.logger.debug(info_string)

    def print_plots(self):
        """Display plots on the commandline"""

        # Plot as long as JSON output is not selected
        if self.preferences.get("show_plots", True) and (not self.preferences.get("json", False)):

            # Determine the open terminal size
            term_size = os.popen('stty size', 'r').read().split()

            titled = False
            for plot_type in ("osc_range", "osc_range_anom"):

                if plot_type in self.plots:

                    if not titled:
                        self.tprint(arg="\nPlots from BEST", level=99, color="blue")
                        titled = True

                    tag = {"osc_range":"standard", "osc_range_anom":"ANOMALOUS"}[plot_type]

                    plot_data = self.plots[plot_type]

                    # Determine y max
                    y_array = numpy.array(plot_data["data"][0]["series"][0]["ys"])
                    y_max = y_array.max() + 10
                    y_min = 0 #max(0, (y_array.min() - 10))

                    gnuplot = subprocess.Popen(["gnuplot"], stdin=subprocess.PIPE) # %s,%s  (term_size[1], int(int(term_size[0])/3),
                    gnuplot.stdin.write("""set term dumb %d,%d
                                           set key outside
                                           set title 'Minimal Oscillation Ranges %s'
                                           set xlabel 'Starting Angle'
                                           set ylabel 'Rotation Range' rotate by 90 \n""" %  (min(180, int(term_size[1])), max(30, int(int(term_size[0])/3)), tag))

                    # Create the plot string
                    plot_string = "plot [0:180] [%d:%d] " % (y_min, y_max)
                    for i in range(min(5, len(plot_data["data"]))):
                        plot_string += "'-' using 1:2 title '%s' with lines," % plot_data["data"][i]["parameters"]["linelabel"].replace("compl -", "")
                    plot_string = plot_string.rstrip(",") + "\n"
                    gnuplot.stdin.write(plot_string)

                    # Run through the data and add to gnuplot
                    for i in range(min(5, len(plot_data["data"]))):
                        plot = plot_data["data"][i]
                        xs = plot["series"][0]["xs"]
                        ys = plot["series"][0]["ys"]
                        for i, j in zip(xs, ys):
                            gnuplot.stdin.write("%f %f\n" % (i,j))
                        gnuplot.stdin.write("e\n")

                    # Now plot!
                    gnuplot.stdin.flush()
                    time.sleep(3)
                    gnuplot.terminate()

    def postprocess(self):
        """
        Make all the HTML files, pass results back, and cleanup.
        """
        if self.verbose:
            self.logger.debug("AutoindexingStrategy::postprocess")

        output = {}

        # Set up the results for return
        self.results["process"] = {
            "process_id": self.command.get("process_id"),
            "status": 100}
        self.results["directories"] = self.setup
        self.results["information"] = self.header
        self.results["preferences"] = self.preferences

        # Generate the proper summaries that go into the output HTML files
        # if self.labelit_failed == False:
        #     if self.labelit_results:
        #         Summary.summaryLabelit(self)
        #         Summary.summaryAutoCell(self, True)
        # if self.distl_results:
        #     Summary.summaryDistl(self)
        # if self.raddose_results:
        #     Summary.summaryRaddose(self)
        if self.labelit_failed == False:
            if self.strategy == "mosflm":
                pass
                # Summary.summaryMosflm(self, False)
                # Summary.summaryMosflm(self, True)
            else:
                if self.best_failed:
                    if self.best_anom_failed:
                        pass
                        # Summary.summaryMosflm(self, False)
                        # Summary.summaryMosflm(self, True)
                    else:
                        # Summary.summaryMosflm(self, False)
                        # Summary.summaryBest(self, True)
                        self.htmlBestPlots()
                elif self.best_anom_failed:
                    # Summary.summaryMosflm(self, True)
                    # Summary.summaryBest(self, False)
                    self.htmlBestPlots()
                else:
                    # Summary.summaryBest(self, False)
                    # Summary.summaryBest(self, True)
                    self.htmlBestPlots()
                    self.print_plots()

        # Save path for files required for future STAC runs.
        try:
            if self.labelit_failed == False:
                os.chdir(self.labelit_dir)
                # files = ["DNA_mosflm.inp", "bestfile.par"]
                # files = ["mosflm.inp", "%s.mat"%self.index_number]
                files = ["%s.mat" % self.index_number, "bestfile.par"]
                for x,f in enumerate(files):
                    shutil.copy(f,self.working_dir)
                    if os.path.exists(os.path.join(self.working_dir, f)):
                        output["STAC file%s"%str(x+1)] = os.path.join(self.dest_dir, f)
                    else:
                        output["STAC file%s"%str(x+1)] = "None"
            else:
                output["STAC file1"] = "None"
                output["STAC file2"] = "None"
        except:
            self.logger.exception("**Could not update path of STAC files**")
            output["STAC file1"] = "FAILED"
            output["STAC file2"] = "FAILED"

        # Pass back paths for html files
        if self.gui:
            e = ".php"
        else:
            e = ".html"
        l = [("best_plots%s" % e, "Best plots html"),
             ("jon_summary_long%s" % e, "Long summary html"),
             ("jon_summary_short%s" % e, "Short summary html")]
        for i in range(len(l)):
            try:
                path = os.path.join(self.working_dir, l[i][0])
                path2 = os.path.join(self.dest_dir, l[i][0])
                if os.path.exists(path):
                    output[l[i][1]] = path2
                else:
                    output[l[i][1]] = "None"
            except:
                self.logger.exception("**Could not update path of %s file.**" % l[i][0])
                output[l[i][1]] = "FAILED"

        # Put all output files into a singe dict to pass back.
        output_files = {"Output files" : output}

        # Put all the result dicts from all the programs run into one resultant dict and pass back.
        try:
            results = {}
            if self.labelit_results:
                results.update(self.labelit_results)
            if self.distl_results:
                results.update(self.distl_results)
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
            # results.update(output_files)
            # self.results.append(results)
            # if self.gui:
            self.results["results"] = results
            self.logger.debug(self.results)
            # Print results to screen in JSON format
            if self.preferences.get("json", False):
                json_output = json.dumps(self.results).replace("\\n", "")
                print json_output
            if self.controller_address:
                rapd_send(self.controller_address, self.results)
        except:
            self.logger.exception("**Could not send results to pipe**")

        # Cleanup my mess.
        try:
            os.chdir(self.working_dir)
            if self.clean:
                if self.test == False:
                    if self.verbose:
                        self.logger.debug("Cleaning up files and folders")
                    os.system("rm -rf labelit_iteration* dataset_preferences.py")
                    for i in range(0, self.iterations):
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
        self.print_info()

        # Say job is complete.
        t = round(time.time() - self.st)
        self.logger.debug("-------------------------------------")
        self.logger.debug("RAPD autoindexing/strategy complete.")
        self.logger.debug("Total elapsed time: %s seconds", t)
        self.logger.debug("-------------------------------------")
        self.tprint(arg="\nRAPD autoindexing & strategy complete", level=99, color="green")
        self.tprint(arg="Total elapsed time: %s seconds" % t, level=10, color="white")

    def htmlBestPlots(self):
        """
        generate plots html/php file
        """

        self.tprint(arg="Generating plots from Best", level=10, color="white")

        if self.verbose:
            self.logger.debug("AutoindexingStrategy::htmlBestPlots")

        # pprint.pprint(self.best_results)

        # try:
        run = True
        plot = False
        plotanom = False
        dir1 = self.best_results.get("best_results_norm").get("directory", False)
        dir2 = self.best_anom_results.get("best_results_anom").get("directory", False)

        # Get the parsed results for reg and anom results and put them into a single dict.
        if dir1:
            # print ">>>", os.path.join(dir1, "best.plt")
            plot = Parse.ParseOutputBestPlots(self, open(os.path.join(dir1, "best.plt"), "r").readlines())
            if dir2:
                # print ">>>", os.path.join(dir2, "best_anom.plt")
                plotanom = Parse.ParseOutputBestPlots(self, open(os.path.join(dir2, "best_anom.plt"), "r").readlines())
                plot.update({"osc_range_anom": plotanom.get("osc_range")})
        elif dir2:
            # print ">>>", os.path.join(dir2, "best_anom.plt")
            plot = Parse.ParseOutputBestPlots(self, open(os.path.join(dir2, "best_anom.plt"), "r").readlines())
            plot.update({"osc_range_anom": plot.pop("osc_range")})
        else:
            run = False

        # Best failed?
        if self.best_failed:
            best_plots = False

        # Best success
        else:
            self.plots = plot

        # except:
        #     self.logger.exception("**ERROR in htmlBestPlots**")


class RunLabelit(Process):

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
      		     'sample_type': 'Protein'},
            'return_address': ('127.0.0.1', 50000)}
    	"""

        self.cluster_adapter = False
        self.st = time.time()

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
        self.controller_address = command["return_address"]

        # params
        self.test = params.get("test", False)
        # Will not use RAM if self.cluster_use=True since runs would be on separate nodes. Adds 1-3s to total run time.
        # self.cluster_use = params.get("cluster",True)

        # If self.cluster_use == True, you can specify a batch queue on your cluster. False to not specify.
        self.cluster_queue = params.get("cluster_queue", False)
        # Get detector vendortype for settings. Defaults to ADSC.
        self.vendortype = params.get("vendortype", "ADSC")
        # Turn on verbose output
        self.verbose = params.get("verbose", False)
        # Number of Labelit iteration to run.
        self.iterations = params.get("iterations", 6)
        # If limiting number of LABELIT run on cluster.
        # self.red = params.get("redis", False)
        self.short = False

    	# If using the cluster, get the correct module (already loaded)
        if params.get("cluster", False):
            self.cluster_adapter = params.get("cluster", False)

    	# Make decisions based on input params
        if self.iterations != 6:
            self.short = True
        # Sets settings so I can view the HTML output on my machine (not in the RAPD GUI), and does not send results to database.
        #******BEAMLINE SPECIFIC*****
        # if self.header.has_key("acc_time"):
        self.gui = True
        #     self.test = False
        # else:
        #     self.gui = True
        #******BEAMLINE SPECIFIC*****
        # Set times for processes. "False" to disable.
        if self.header2:
            self.labelit_timer = 180
        else:
            self.labelit_timer = 120
        # Turns on multiprocessing for everything
        # Turns on all iterations of Labelit running at once, sorts out highest symmetry solution, then continues...(much better!!)
        self.multiproc = True
        if self.preferences.has_key("multiprocessing"):
            if self.preferences.get("multiprocessing") == "False":
                self.multiproc = False
        self.sample_type = self.preferences.get("sample_type", "Protein")
        self.spacegroup = self.preferences.get("spacegroup", False)

        # This is where I place my overall folder settings.
        self.working_dir = self.setup.get("work")
        # This is where I have chosen to place my results
        self.auto_summary = False
        self.labelit_input = False
        self.labelit_log = {}
        self.labelit_results = {}
        self.labelit_summary = False
        self.labelit_failed = False
        # Labelit settings
        self.index_number = False
        self.ignore_user_cell = False
        self.ignore_user_SG = False
        self.min_good_spots = False
        self.twotheta = False
        # dicts for running the Queues
        self.labelit_jobs = {}
        self.pids = {}

        Process.__init__(self, name="RunLabelit")
        self.start()

    def run(self):
        """
        Convoluted path of modules to run.
        """

        if self.verbose:
            self.logger.debug("RunLabelit::run")

        self.preprocess()

        # Make the initial dataset_prefernces.py file
        self.preprocessLabelit()
        if self.short:
            self.labelit_timer = 300
            Utils.foldersLabelit(self, self.iterations)
            # if a specific iteration is sent in then it only runs that one
            if self.iterations == 0:
                self.labelit_jobs[self.processLabelit().keys()[0]] = 0
            else:
                self.labelit_jobs[Utils.errorLabelit(self, self.iterations).keys()[0]] = self.iterations
        else:
            # Create the separate folders for the labelit runs, modify the dataset_preferences.py file, and launch for each iteration.
            Utils.foldersLabelit(self)
            # Launch first job
            self.labelit_jobs[self.processLabelit().keys()[0]] = 0
            # If self.multiproc==True runs all labelits at the same time.
            if self.multiproc:
                for i in range(1, self.iterations):
                    self.labelit_jobs[Utils.errorLabelit(self,i).keys()[0]] = i
        self.run_queue()
        if self.short == False:
            # Put the logs together
            self.labelitLog()
        self.postprocess()

    def preprocess(self):
        """
        Setup the working dir in the RAM and save the dir where the results will go at the end.
        """
        if self.verbose:
            self.logger.debug("RunLabelit::preprocess")
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)
        if self.test:
            if self.short == False:
                self.logger.debug("TEST IS ON")
                self.tprint(arg="TEST IS ON", level=10, color="white")

    def preprocessLabelit(self):
        """
        Setup extra parameters for Labelit if turned on. Will always set beam center from image header.
        Creates dataset_preferences.py file for editing later in the Labelit error iterations if needed.
        """

        if self.verbose:
            self.logger.debug('RunLabelit::preprocessLabelit')

        # try:
        twotheta       = str(self.header.get("twotheta", "0"))
        #distance       = str(self.header.get('distance'))
        #x_beam         = str(self.preferences.get('x_beam', self.header.get('beam_center_x'))) #OLD
        #Once we figure out the beam center issue, I can switch to this.
	      #x_beam         = str(self.header.get('beam_center_calc_x', self.header.get('beam_center_x')))
        #y_beam         = str(self.header.get('beam_center_calc_y', self.header.get('beam_center_y')))
        x_beam         = str(self.header.get("x_beam"))
        y_beam         = str(self.header.get("y_beam"))
        # x_beam         = str(self.header.get('beam_center_x'))
        # y_beam         = str(self.header.get('beam_center_y'))

        # If an override beam center is provided, use it
        if self.preferences["x_beam"]:
            x_beam = self.preferences["x_beam"]
            y_beam = self.preferences["y_beam"]
            self.tprint("  Using override beam center %s, %s" % (x_beam, y_beam), 10, "white")

        binning = True
        if self.header.has_key('binning'):
            binning = self.header.get('binning')

        if self.test == False:
            preferences= open('dataset_preferences.py', 'w')
            preferences.write('#####Base Labelit settings#####\n')
            preferences.write('best_support=True\n')
            # Set Mosflm RMSD tolerance larger
            preferences.write('mosflm_rmsd_tolerance=4.0\n')

            # If binning is off. Force Labelit to use all pixels(MAKES THINGS WORSE). Increase number of spots to use for indexing.
            if binning == False:
                preferences.write('distl_permit_binning=False\n')
                preferences.write('distl_maximum_number_spots_for_indexing=600\n')

            # If user wants to change the res limit for autoindexing.
            if str(self.preferences.get('index_hi_res','0.0')) != '0.0':
                #preferences.write('distl.res.outer='+index_hi_res+'\n')
                preferences.write('distl_highres_limit=%s\n'%self.preferences.get('index_hi_res'))

            # Always specify the beam center.
            # If Malcolm flips the beam center in the image header...
            if self.preferences.get("beam_flip", False) == True:
                preferences.write("autoindex_override_beam=(%s,%s)\n" % (y_beam, x_beam))
            else:
                # print x_beam, y_beam
                preferences.write("autoindex_override_beam=(%s, %s)\n" % (x_beam, y_beam))

            # If two-theta is being used, specify the angle and distance correctly.
            if twotheta.startswith('0'):
                preferences.write('beam_search_scope=0.2\n')
            else:
                self.twotheta = True
                preferences.write('beam_search_scope=0.5\n')
                preferences.write('autoindex_override_twotheta=%s\n'%twotheta)
                # preferences.write('autoindex_override_distance='+distance+'\n')
            preferences.close()

        # except:
        #     self.logger.exception('**ERROR in RunLabelit.preprocessLabelit**')

    def processLabelit(self, iteration=0, inp=False):
        """
        Construct the labelit command and run. Passes back dict with PID:iteration.
        """
        if self.verbose:
            self.logger.debug("RunLabelit::processLabelit")

        try:
            labelit_input = []
            #Check if user specific unit cell
            d = {'a': False, 'c': False, 'b': False, 'beta': False, 'alpha': False, 'gamma': False}
            counter = 0
            for l in d.keys():
                temp = str(self.preferences.get(l,0.0))
                if temp != '0.0':
                    d[l] = temp
                    counter += 1
            if counter != 6:
                d = False
            # Put together the command for labelit.index
            command = 'labelit.index '
            # If first labelit run errors because not happy with user specified cell or SG then ignore user input in the rerun.
            if self.ignore_user_cell == False:
                if d:
                    command += 'known_cell=%s,%s,%s,%s,%s,%s ' % (d['a'], d['b'], d['c'], d['alpha'], d['beta'], d['gamma'])
            if self.ignore_user_SG == False:
                if self.spacegroup != False:
                    command += 'known_symmetry=%s ' % self.spacegroup
            # For peptide crystals. Doesn't work that much.
            if self.sample_type == 'Peptide':
                command += 'codecamp.maxcell=80 codecamp.minimum_spot_count=10 '
            if inp:
                command += '%s ' % inp
            command += '%s ' % self.header.get('fullname')
            # If pair of images
            if self.header2:
                command += "%s " % self.header2.get("fullname")
            # Save the command to the top of log file, before running job.
            if self.verbose:
                self.logger.debug(command)
            labelit_input.append(command)
            if iteration == 0:
                self.labelit_log[str(iteration)] = labelit_input
            else:
                self.labelit_log[str(iteration)].extend(labelit_input)
            labelit_jobs = {}
            # Don't launch job if self.test = True
            if self.test:
                labelit_jobs["junk%s" % iteration] = iteration
            else:
                # print command
                log = os.path.join(os.getcwd(), "labelit.log")
                #queue to retrieve the PID or JobIB once submitted.
                pid_queue = Queue()
                if self.cluster_adapter:
                    #Delete the previous log still in the folder, otherwise the cluster jobs will append to it.
                    if os.path.exists(log):
                        os.system("rm -rf %s" % log)
                    run = Process(target=self.cluster_adapter.process_cluster_beorun,
		                          args=({'command': command,
                                         'log': log,
                                         'queue': self.cluster_queue,
                                         'pid': pid_queue},) )
                else:
                    run = Process(target=Utils.processLocal, args=((command, log), self.logger, pid_queue))
                run.start()
                #Save the PID for killing the job later if needed.
                self.pids[str(iteration)] = pid_queue.get()
                labelit_jobs[run] = iteration
            #return a dict with the job and iteration
            return(labelit_jobs)

        except:
            self.logger.exception('**Error in RunLabelit.processLabelit**')

    def postprocessLabelit(self,iteration=0,run_before=False,blank=False):
        """
        Sends Labelit log for parsing and error checking for rerunning Labelit. Save output dicts.
        """
        if self.verbose:
            self.logger.debug('RunLabelit::postprocessLabelit')
        try:
            Utils.foldersLabelit(self, iteration)
    	    #labelit_failed = False
            if blank:
                error = 'Not enough spots for autoindexing.'
                if self.verbose:
                    self.logger.debug(error)
                self.labelit_log[str(iteration)].extend(error+'\n')
                return(None)
            else:
                log = open('labelit.log', 'r').readlines()
                self.labelit_log[str(iteration)].extend('\n\n')
                self.labelit_log[str(iteration)].extend(log)
                data = Parse.ParseOutputLabelit(self,log,iteration)
                if self.short:
                    #data = Parse.ParseOutputLabelitNoMosflm(self,log,iteration)
                    self.labelit_results = { "labelit_results" : data }
                else:
                    #data = Parse.ParseOutputLabelit(self,log,iteration)
                    self.labelit_results[str(iteration)] = { "labelit_results" : data }
        except:
            self.logger.exception('**ERROR in RunLabelit.postprocessLabelit**')

        # Do error checking and send to correct place according to iteration.
        out = {'bad input': {'error':'Labelit did not like your input unit cell dimensions or SG.','run':'Utils.errorLabelitCellSG(self,iteration)'},
               'bumpiness': {'error':'Labelit settings need to be adjusted.','run':'Utils.errorLabelitBump(self,iteration)'},
               'mosflm error': {'error':'Mosflm could not integrate your image.','run':'Utils.errorLabelitMosflm(self,iteration)'},
               'min good spots': {'error':'Labelit did not have enough spots to find a solution','run':'Utils.errorLabelitGoodSpots(self,iteration)'},
               'no index': {'error':'No solutions found in Labelit.','run':'Utils.errorLabelit(self,iteration)'},
               'fix labelit': {'error':'Distance is not getting read correctly from the image header.','kill':True},
               'no pair': {'error':'Images are not a pair.','kill':True},
               'failed': {'error':'Autoindexing Failed to find a solution','kill':True},
               'min spots': {'error':'Labelit did not have enough spots to find a solution.','run1':'Utils.errorLabelitMin(self,iteration,data[1])',
                             'run2':'Utils.errorLabelit(self,iteration)'},
               'fix_cell': {'error':'Labelit had multiple choices for user SG and failed.','run1':'Utils.errorLabelitFixCell(self,iteration,data[1],data[2])',
                            'run2':'Utils.errorLabelitCellSG(self,iteration)'},
               }
        # If Labelit results are OK, then...
        if type(data) == dict:
            d = False
        # Otherwise deal with fixing and rerunning Labelit
        elif type(data) == tuple:
            d = data[0]
        else:
            d = data
        if d:
            if out.has_key(d):
                if out[d].has_key('kill'):
                    if self.multiproc:
                        Utils.errorLabelitPost(self,iteration,out[d].get('error'),True)
                    else:
                        Utils.errorLabelitPost(self,self.iterations,out[d].get('error'))
                else:
                    Utils.errorLabelitPost(self,iteration,out[d].get('error'),run_before)
                    if self.multiproc:
                        if run_before == False:
                            return(eval(out[d].get('run',out[d].get('run1'))))
                    else:
                        if iteration <= self.iterations:
                            return(eval(out[d].get('run',out[d].get('run2'))))
            else:
                error = 'Labelit failed to find solution.'
                Utils.errorLabelitPost(self,iteration,error,run_before)
                if self.multiproc == False:
                    if iteration <= self.iterations:
                        return (Utils.errorLabelit(self,iteration))

    def postprocess(self):
        """
        Send back the results and logs.
        """
        if self.verbose:
            self.logger.debug("RunLabelit::postprocess")

        # try:

        # Free up spot on cluster.
        # if self.short and self.red:
        # self.red.lpush("bc_throttler", 1)

        # Pass back output
        self.output.put(self.labelit_results)
        if self.short == False:
            self.output.put(self.labelit_log)

        # except:
        #     self.logger.exception("**ERROR in RunLabelit.postprocess**")

    def run_queue(self):
        """
        Run Queue for Labelit.
        """
        if self.verbose:
            self.logger.debug('RunLabelit::run_queue')
        try:
            timed_out = False
            timer = 0
            # labelit = False
            jobs = self.labelit_jobs.keys()
            # Set wait time longer to lower the load on the node running the job.
            if self.short:
                wait = 1
            else:
                wait = 0.1
            if jobs != ['None']:
                counter = len(jobs)
                while counter != 0:
                    for job in jobs:
                        if self.test:
                            running = False
                        else:
                            running = job.is_alive()
                        if running == False:
                            jobs.remove(job)
                            iteration = self.labelit_jobs[job]
                            if self.verbose:
                                self.logger.debug('Finished Labelit%s'%iteration)
                                # self.tprint(arg="Finished Labelit%s" % iteration, level=10)
                            # Check if job had been rerun, fix the iteration.
                            if iteration >= 10:
                                iteration -=10
                                job = self.postprocessLabelit(iteration, True)
                            else:
                                job = self.postprocessLabelit(iteration, False)
                            # If job is rerun, then save the iteration and pid.
                            if job != None:
                                if self.multiproc:
                                    iteration +=10
                                else:
                                    iteration +=1
                                self.labelit_jobs[job.keys()[0]] = iteration
                                jobs.extend(job.keys())
                            else:
                                counter -= 1
                    time.sleep(wait)
                    timer += wait
                    """
                    if self.verbose:
                        number = round(timer%1,1)
                        if number in (0.0,1.0):
                            print 'Waiting for Labelit to finish '+str(timer)+' seconds'
                    """
                    if self.labelit_timer:
                        if timer >= self.labelit_timer:
                            if self.multiproc:
                                timed_out = True
                                break
                            else:
                                iteration += 1
                                if iteration <= self.iterations:
                                    Utils.errorLabelit(self,iteration)
                                else:
                                    timed_out = True
                                    break
                if timed_out:
                    self.logger.debug('Labelit timed out.')
                    for job in jobs:
                        i = self.labelit_jobs[job]
                        if i >= 10:
                            i -=10
                        self.labelit_results[str(i)] = {"labelit_results": 'FAILED'}
                        if self.cluster_use:
                            # Utils.killChildrenCluster(self,self.pids[str(i)])
                            self.cluster_adapter.killChildrenCluster(self,self.pids[str(i)])
                        else:
                            Utils.killChildren(self,self.pids[str(i)])

            if self.short == False:
                self.logger.debug('Labelit finished.')

        except:
            self.logger.exception('**Error in RunLabelit.run_queue**')

    def labelitLog(self):
        """Put the Labelit logs together"""

        if self.verbose:
            self.logger.debug("RunLabelit::LabelitLog")

        # try:
        for i in range(0,self.iterations):
            if self.labelit_log.has_key(str(i)):
                junk = ["-------------------------\nLABELIT ITERATION %s\n-------------------------\n" % i]
                if i == 0:
                    self.labelit_log["run1"] = ["\nRun 1\n"]
                self.labelit_log["run1"].extend(junk)
                self.labelit_log["run1"].extend(self.labelit_log[str(i)])
                self.labelit_log["run1"].extend("\n")
            else:
                self.labelit_log["run1"].extend("\nLabelit iteration %s FAILED\n"%i)

        # except:
        #     self.logger.exception("**ERROR in RunLabelit.LabelitLog**")

def BestAction(inp, logger=False, output=False):
    """
    Run Best.
    """
    if logger:
        logger.debug("BestAction")
        logger.debug(inp)

    # print inp
    # try:
    command, log = inp
    # Have to do this otherwise command is written to bottom of file??
    f = open(log, 'w')
    f.write('\n\n' + command + '\n')
    f.close()
    f = open(log, 'a')
    job = subprocess.Popen(command, shell=True, stdout=f, stderr=f)
    if output:
        output.put(job.pid)
    job.wait()
    f.close()
    # except:
    #     if logger:
    #         logger.exception('**Error in BestAction**')

if __name__ == '__main__':
  #construct test input for Autoindexing/strategy
  #This is an example input dict used for testing this script.
  #Input dict file. If autoindexing from two images, just include a third dict section for the second image header.
  ###To see all the input options look at extras/rapd_input.py (autoindexInput)###

  command = {
        "command":"AUTOINDEX+STRATEGY",
        "directories": { "work": "/tmp/rapd_test" },
        "header1":{
            #"wavelength": "0.9792", #RADDOSE
    	   	"wavelength": 1.000, #RADDOSE
    	   	"detector":'ray300',
    	   	#"binning": "2x2", #LABELIT
    	   	"binning": "none", #
    	   	"time": "1.00",  #BEST
    	   	"twotheta": "0.00", #LABELIT
    	   	"transmission": "20",  #BEST
    	   	'osc_range': 1.0,
    	   	'distance' : 200.0,
    	   	'count_cutoff': 65535,
    	   	'omega_start': 0.0,
    	   	#"beam_center_x": "216.71", #PILATUS
    	   	#"beam_center_y": "222.45", #PILATUS
    	   	#"beam_center_x": "150.72", #Q315
    	   	#"beam_center_y": "158.68", #Q315
    	   	#"beam_center_x": "172.80", #HF4M
    	   	#"beam_center_y": "157.18", #HF4M
    	   	"beam_center_x": "151.19", #22ID
    	        "beam_center_y": "144.82", #22ID
    	   	#"beam_center_x": "150.25", #22BM
    	   	#"beam_center_y": "151.35", #22BM
    	   	"flux":'1.6e11', #RADDOSE
    	   	"beam_size_x":"0.07", #RADDOSE
    	   	"beam_size_y":"0.03", #RADDOSE
    	   	"gauss_x":'0.03', #RADDOSE
    	   	"gauss_y":'0.01', #RADDOSE
    		"fullname": "/panfs/panfs0.localdomain/archive/ID_16_06_01_staff_test/Se-Tryp_SER16-pn10/SER-16_Pn10_1.0001",
    	   	#"fullname": "/panfs/panfs0.localdomain/archive/BM_16_03_03_staff_staff/Tryp/SERX12_Pn1_r1_1.0001",
    	   	#"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_23_chrzas/21281_p422x01/image/21281.0001",
    	   	#"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_04_chrzas_feb_4_2016/SER4-TRYP_Pn3/SER4-TRYP_Pn3.0001",
    	   	#"fullname": "/gpfs6/users/necat/Jon/RAPD_test/Temp/mar/SER4-TRYP_Pn3.0001",

    	   	#minikappa
    	   	#Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
    	   	#"mk3_phi":"0.0", #
    	   	#"mk3_kappa":"0.0", #
    	   	"phi": "0.000",
    	   	"STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
    	   	"STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
    	   	"axis_align": 'long',	 #long,all,a,b,c,ab,ac,bc #XOAlign
		},
        "header2":{#"wavelength": "0.9792", #RADDOSE
	    "wavelength": 1.000, #RADDOSE
	    "detector":'ray300',
	    #"binning": "2x2", #LABELIT
	    "binning": "none", #
	    "time": "1.00",  #BEST
	    "twotheta": "0.00", #LABELIT
	    "transmission": "20",  #BEST
	    'osc_range': 1.0,
	    'distance' : 200.0,
	    'count_cutoff': 65535,
	    'omega_start': 0.0,
	    #"beam_center_x": "216.71", #PILATUS
	    #"beam_center_y": "222.45", #PILATUS
	    #"beam_center_x": "150.72", #Q315
	    #"beam_center_y": "158.68", #Q315
	    #"beam_center_x": "172.80", #HF4M
	    #"beam_center_y": "157.18", #HF4M
	    "beam_center_x": "151.19", #22ID
	    "beam_center_y": "144.82", #22ID
	    #"beam_center_x": "150.25", #22BM
	    #"beam_center_y": "151.35", #22BM
	    "flux":'1.6e11', #RADDOSE
	    "beam_size_x":"0.07", #RADDOSE
	    "beam_size_y":"0.03", #RADDOSE
	    "gauss_x":'0.03', #RADDOSE
	    "gauss_y":'0.01', #RADDOSE
	    "fullname": "/panfs/panfs0.localdomain/archive/ID_16_06_01_staff_test/Se-Tryp_SER16-pn10/SER-16_Pn10_1.0090",
	    #"fullname": "/panfs/panfs0.localdomain/archive/BM_16_03_03_staff_staff/Tryp/SERX12_Pn1_r1_1.0090",
	    #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_23_chrzas/21281_p422x01/image/21281.0020",
	    #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_04_chrzas_feb_4_2016/SER4-TRYP_Pn3/SER4-TRYP_Pn3.0050",
	    #"fullname": "/gpfs6/users/necat/Jon/RAPD_test/Temp/mar/SER4-TRYP_Pn3.0050",

	    #minikappa
	    #Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
	    #"mk3_phi":"0.0", #
	    #"mk3_kappa":"0.0", #
	    "phi": "0.000",
	    "STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
	    "STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
	    "axis_align": 'long',    #long,all,a,b,c,ab,ac,bc #XOAlign
	    },
	  "preferences":{"strategy_type": 'best', #Preferred program for strategy
	  		#"strategy_type": 'mosflm', #
	  	  	"crystal_size_x": "100", #RADDOSE
		 	 "crystal_size_y": "100", #RADDOSE
		  	"crystal_size_z": "100", #RADDOSE
			  "shape": "2.0", #BEST
			  "sample_type": "Protein", #LABELIT, BEST
			  "best_complexity": "none", #BEST
			  "susceptibility": "1.0", #BEST
			  "index_hi_res": 0.0, #LABELIT
			  "spacegroup": "None", #LABELIT, BEST, beam_center
			  #"spacegroup": "R3", #
			  "solvent_content": 0.55, #RADDOSE
			  "beam_flip": "False", #NECAT, when x and y are sent reversed.
			  "multiprocessing":"True", #Specifies to use 4 cores to make Autoindex much faster.
			  "x_beam": "0",#Used if position not in header info
			  "y_beam": "0",#Used if position not in header info
			  "aimed_res": 0.0, #BEST to override high res limit
			  "a":0.0, ##LABELIT
			  "b":0.0, ##LABELIT
			  "c":0.0, ##LABELIT
			  "alpha":0.0, #LABELIT
			  "beta":0.0, #LABELIT
			  "gamma":0.0, #LABELIT

			  #Change these if user wants to continue dataset with other crystal(s).
			  "reference_data_id": None, #MOSFLM
			  #"reference_data_id": 1,#MOSFLM
			  #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30','P41212']],#MOSFLM
			  'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',0.0,20.0,'junk','P3'],['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',40.0,50.0,'junk2','P3']],#MOSFLM
			  #MOSFLM settings for multisegment strategy (like give me best 30 degrees to collect). Ignored if "mosflm_rot" !=0.0
			  "mosflm_rot": 0.0, #MOSFLM
			  "mosflm_seg":1, #MOSFLM
			  "mosflm_start":0.0,#MOSFLM
			  "mosflm_end":360.0,#MOSFLM
			  },			     # Settings for calculations
	  "return_address":("127.0.0.1", 50001),      # Location of control process
    }

  #OLD INPUT
  inp_OLD = ["AUTOINDEX",
  {#"work": "/gpfs6/users/necat/Jon/RAPD_test/Output",
   "work": "/home/schuerjp/temp/Junk",
   },

  #Info from first image
  {#"wavelength": "0.9792", #RADDOSE
   "wavelength": 1.000, #RADDOSE
   "detector":'ray300',
   #"binning": "2x2", #LABELIT
   "binning": "none", #
   "time": "1.00",  #BEST
   "twotheta": "0.00", #LABELIT
   "transmission": "20",  #BEST
   'osc_range': 1.0,
   'distance' : 200.0,
   'count_cutoff': 65535,
   'omega_start': 0.0,
   #"beam_center_x": "216.71", #PILATUS
   #"beam_center_y": "222.45", #PILATUS
   #"beam_center_x": "150.72", #Q315
   #"beam_center_y": "158.68", #Q315
   #"beam_center_x": "172.80", #HF4M
   #"beam_center_y": "157.18", #HF4M
   #"beam_center_x": "149.87", #22ID
   #"beam_center_y": "145.16", #22ID
   "beam_center_x": "140.06", #22BM
   "beam_center_y": "142.22", #22BM
   "flux":'1.6e11', #RADDOSE
   "beam_size_x":"0.07", #RADDOSE
   "beam_size_y":"0.03", #RADDOSE
   "gauss_x":'0.03', #RADDOSE
   "gauss_y":'0.01', #RADDOSE
   "fullname": "/panfs/panfs0.localdomain/archive/BM_16_03_03_staff_staff/Tryp/SERX12_Pn1_r1_1.0001",
   #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_23_chrzas/21281_p422x01/image/21281.0001",
   #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_04_chrzas_feb_4_2016/SER4-TRYP_Pn3/SER4-TRYP_Pn3.0001",
   #"fullname": "/gpfs6/users/necat/Jon/RAPD_test/Temp/mar/SER4-TRYP_Pn3.0001",

   #minikappa
   #Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
   #"mk3_phi":"0.0", #
   #"mk3_kappa":"0.0", #
   "phi": "0.000",
   "STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
   "STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
   "axis_align": 'long',    #long,all,a,b,c,ab,ac,bc #XOAlign
  },

   #Info from second image. Remove this dict if NOT present in run.
  {#"wavelength": "0.9792", #RADDOSE
   "wavelength": 1.000, #RADDOSE
   "detector":'ray300',
   #"binning": "2x2", #LABELIT
   "binning": "none", #
   "time": "1.00",  #BEST
   "twotheta": "0.00", #LABELIT
   "transmission": "20",  #BEST
   'osc_range': 1.0,
   'distance' : 200.0,
   'count_cutoff': 65535,
   'omega_start': 0.0,
   #"beam_center_x": "216.71", #PILATUS
   #"beam_center_y": "222.45", #PILATUS
   #"beam_center_x": "150.72", #Q315
   #"beam_center_y": "158.68", #Q315
   #"beam_center_x": "172.80", #HF4M
   #"beam_center_y": "157.18", #HF4M
   #"beam_center_x": "149.87", #22ID
   #"beam_center_y": "145.16", #22ID
   "beam_center_x": "140.06", #22BM
   "beam_center_y": "142.22", #22BM
   "flux":'1.6e11', #RADDOSE
   "beam_size_x":"0.07", #RADDOSE
   "beam_size_y":"0.03", #RADDOSE
   "gauss_x":'0.03', #RADDOSE
   "gauss_y":'0.01', #RADDOSE
   "fullname": "/panfs/panfs0.localdomain/archive/BM_16_03_03_staff_staff/Tryp/SERX12_Pn1_r1_1.0090",
   #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_23_chrzas/21281_p422x01/image/21281.0020",
   #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_04_chrzas_feb_4_2016/SER4-TRYP_Pn3/SER4-TRYP_Pn3.0050",
   #"fullname": "/gpfs6/users/necat/Jon/RAPD_test/Temp/mar/SER4-TRYP_Pn3.0050",

   #minikappa
   #Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
   #"mk3_phi":"0.0", #
   #"mk3_kappa":"0.0", #
   "phi": "0.000",
   "STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
   "STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
   "axis_align": 'long',    #long,all,a,b,c,ab,ac,bc #XOAlign
  },

  #Beamline params
  {"strategy_type": 'best', #Preferred program for strategy
   #"strategy_type": 'mosflm', #
   "crystal_size_x": "100", #RADDOSE
   "crystal_size_y": "100", #RADDOSE
   "crystal_size_z": "100", #RADDOSE
   "shape": "2.0", #BEST
   "sample_type": "Protein", #LABELIT, BEST
   "best_complexity": "none", #BEST
   "susceptibility": "1.0", #BEST
   "index_hi_res": 0.0, #LABELIT
   "spacegroup": "None", #LABELIT, BEST, beam_center
   #"spacegroup": "R3", #
   "solvent_content": 0.55, #RADDOSE
   "beam_flip": "False", #NECAT, when x and y are sent reversed.
   "multiprocessing":"True", #Specifies to use 4 cores to make Autoindex much faster.
   "x_beam": "0",#Used if position not in header info
   "y_beam": "0",#Used if position not in header info
   "aimed_res": 0.0, #BEST to override high res limit
   "a":0.0, ##LABELIT
   "b":0.0, ##LABELIT
   "c":0.0, ##LABELIT
   "alpha":0.0, #LABELIT
   "beta":0.0, #LABELIT
   "gamma":0.0, #LABELIT

   #Change these if user wants to continue dataset with other crystal(s).
   "reference_data_id": None, #MOSFLM
   #"reference_data_id": 1,#MOSFLM
   #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30','P41212']],#MOSFLM
   'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',0.0,20.0,'junk','P3'],['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',40.0,50.0,'junk2','P3']],#MOSFLM
   #MOSFLM settings for multisegment strategy (like give me best 30 degrees to collect). Ignored if "mosflm_rot" !=0.0
   "mosflm_rot": 0.0, #MOSFLM
   "mosflm_seg":1, #MOSFLM
   "mosflm_start":0.0,#MOSFLM
   "mosflm_end":360.0,#MOSFLM
    },

  ('127.0.0.1', 50001)]#self.sendBack2 for sending results back to rapd_cluster.

  import sites.sercat as site
  import utils.log


  log = utils.log.get_logger(logfile_dir=command['directories']['work'],)
  #log = utils.log.get_logger(logfile_dir=logfile_dir,
  #                              logfile_id=logfile_id,
  #                              level=10)

  RapdAgent(site, command, log)

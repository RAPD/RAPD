"""assess_integrated_data RAPD plugin"""

"""
This file is part of RAPD

Copyright (C) 2018, Cornell University
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

__created__ = "2018-08-02"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's types
DATA_TYPE = "MX"
PLUGIN_TYPE = "ASSESS_INTEGRATED_DATA"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique ID for this handler (uuid.uuid1().hex[:4])
ID = "ea69"
VERSION = "1.0.0"

# Standard imports
# import argparse
# import from collections import OrderedDict
# import datetime
import glob
import json
import logging
# import math
import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
import shutil
import stat
import subprocess
import sys
import time
# import unittest
# import urllib2
import uuid
from distutils.spawn import find_executable

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
import plugins.analysis.commandline
import plugins.analysis.plugin
import plugins.pdbquery.commandline
import plugins.pdbquery.plugin
from plugins.subcontractors.aimless import parse_aimless
# import utils
import utils.credits as rcredits
import info
from utils import exceptions

# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

class RapdPlugin(multiprocessing.Process):
    """
    RAPD plugin class

    Command format:
    {
       "command":"assess_integrated_data",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    # Holders for passed-in info
    command = None
    preferences = None

    # Holders for results
    results = {}

    def __init__(self, site, command, tprint=False, logger=False):
        """Initialize the plugin"""

         # Keep track of start time
        self.start_time = time.time()

        pprint(command)

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
                pass
            self.tprint = func

        # Some logging
        self.logger.info(command)

        # Store passed-in variables
        self.site = site
        self.command = command  
        self.preferences = self.command.get("preferences", {})

        # Set up the results with command and process data
        self.results["command"] = command

        # Create a process section of results with the id and a starting status of 1
        self.results["process"] = {
            "process_id": self.command.get("process_id"),
            "status": 1}

        multiprocessing.Process.__init__(self, name="assess_integrated_data")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()
        self.print_credits()

    def preprocess(self):
        """Set up for plugin action"""

        self.tprint(arg=0, level="progress")
        self.tprint("preprocess")

        # Check for dependency problems
        self.check_dependencies()

        # Move to working directory
        os.chdir(self.command["directories"]["work"])

    def process(self):
        """Run plugin action"""

        self.tprint("process")
        
        # Run aimless
        aimless_results = self.aimless()

        # Put results into self.results looking roughly like the core integrate plugin
        self.results["summary"]= aimless_results["summary"]
        self.results["plots"] = aimless_results["plots"]
        self.results["log"] = aimless_results["log"]

        # Update status
        self.results["process"]["status"] = 10

        # Send back results
        self.handle_return()

        # Run analysis
        self.run_analysis_plugin()

        # Run pdbquery
        self.run_pdbquery_plugin()


    def postprocess(self):
        """Events after plugin action"""

        self.tprint("postprocess")

        self.tprint(arg=99, level="progress")
        # Clean up mess
        self.clean_up()

    def check_dependencies(self):
        """Make sure dependencies are all available"""

        for executable in ("aimless",):
            if not find_executable(executable):
                self.tprint("Executable for %s is not present, exiting" % executable,
                            level=30,
                            color="red")
                self.results["process"]["status"] = -1
                self.results["error"] = "Executable for %s is not present" % executable
                self.write_json(self.results)
                raise exceptions.MissingExecutableException(executable)

    def clean_up(self):
        """Clean up after plugin action"""

        self.tprint("clean_up")

    def handle_return(self):
        """Output data to consumer - still under construction"""

        self.tprint("handle_return")

        run_mode = self.command["preferences"]["run_mode"]

        # Handle JSON At least write to file
        self.write_json()

        # Print results to the terminal
        if run_mode == "interactive":
            self.print_results(self.results)
        # Traditional mode as at the beamline
        elif run_mode == "server":
            pass
        # Run and return results to launcher
        elif run_mode == "subprocess":
            return self.results
        # A subprocess with terminal printing
        elif run_mode == "subprocess-interactive":
            self.print_results()
            return self.results

    def write_json(self):
        """Print out JSON-formatted result"""

        json_string = json.dumps(self.results)

        # Output to terminal?
        if self.preferences.get("json", False):
            print json_string

        # Always write a file
        os.chdir(self.command["directories"]["work"])
        with open("result.json", "w") as outfile:
            outfile.writelines(json_string)

    def print_results(self, results):
        """Print out results to the terminal"""

        # Print summary
        summary = results["summary"]

        self.tprint("\nAnalysis Summary", 99, "blue")
        # self.tprint("  Spacegroup: %s" % summary["scaling_spacegroup"], 99, "white")
        # self.tprint("  Unit cell: %5.1f %5.1f %5.1f %5.2f %5.2f %5.2f" %
        #             tuple(summary["scaling_unit_cell"]), 99, "white")
        # self.tprint("  Mosaicity: %5.3f" % summary["mosaicity"], 99, "white")
        # self.tprint("  ISa: %5.2f" % summary["ISa"], 99, "white")
        self.tprint("                        overall   inner shell   outer shell", 99, "white")
        self.tprint("  High res limit         %5.2f       %5.2f         %5.2f" %
                    tuple(summary["bins_high"]), 99, "white")
        self.tprint("  Low res limit         %6.2f      %6.2f        %6.2f" %
                    tuple(summary["bins_low"]), 99, "white")
        self.tprint("  Completeness           %5.1f       %5.1f         %5.1f" %
                    tuple(summary["completeness"]), 99, "white")
        self.tprint("  Multiplicity            %4.1f        %4.1f          %4.1f" %
                    tuple(summary["multiplicity"]), 99, "white")
        self.tprint("  I/sigma(I)              %4.1f        %4.1f          %4.1f" %
                    tuple(summary["isigi"]), 99, "white")
        self.tprint("  CC(1/2)                %5.3f       %5.3f         %5.3f" %
                    tuple(summary["cc-half"]), 99, "white")
        self.tprint("  Rmerge                 %5.3f       %5.3f         %5.3f" %
                    tuple(summary["rmerge_norm"]), 99, "white")
        self.tprint("  Anom Rmerge            %5.3f       %5.3f         %5.3f" %
                    tuple(summary["rmerge_anom"]), 99, "white")
        self.tprint("  Rmeas                  %5.3f       %5.3f         %5.3f" %
                    tuple(summary["rmeas_norm"]), 99, "white")
        self.tprint("  Anom Rmeas             %5.3f       %5.3f         %5.3f" %
                    tuple(summary["rmeas_anom"]), 99, "white")
        self.tprint("  Rpim                   %5.3f       %5.3f         %5.3f" %
                    tuple(summary["rpim_norm"]), 99, "white")
        self.tprint("  Anom Rpim              %5.3f       %5.3f         %5.3f" %
                    tuple(summary["rpim_anom"]), 99, "white")
        self.tprint("  Anom Completeness      %5.1f       %5.1f         %5.1f" %
                    tuple(summary["anom_completeness"]), 99, "white")
        self.tprint("  Anom Multiplicity       %4.1f        %4.1f          %4.1f" %
                    tuple(summary["anom_multiplicity"]), 99, "white")
        self.tprint("  Anom Correlation      %6.3f      %6.3f        %6.3f" %
                    tuple(summary["anom_correlation"]), 99, "white")
        self.tprint("  Anom Slope             %5.3f" % summary["anom_slope"][0], 99, "white")
        self.tprint("  Observations         %7d     %7d       %7d" %
                    tuple(summary["total_obs"]), 99, "white")
        self.tprint("  Unique Observations  %7d     %7d       %7d\n" %
                    tuple(summary["unique_obs"]), 99, "white")

    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        self.tprint("print_credits")

        self.tprint(rcredits.HEADER, level=99, color="blue")

        programs = ["CCTBX", "AIMLESS"]
        info_string = rcredits.get_credits_text(programs, "    ")
        self.tprint(info_string, level=99, color="white")

    def aimless(self):
        """Run aimless on the input data"""

        self.logger.debug("aimless")
        self.tprint(arg="  Running Aimless", level=10, color="white")

        data_file = self.command["input_data"]["data_file"]
        logfile = "aimless_" + os.path.basename(data_file)[:-3] + "log"
        comfile = logfile.replace("log", "com")

        print "opening", comfile
        with open(comfile, "w") as aimless_file:
            aimless_file.write("#!/bin/csh\n")
            aimless_file.write('aimless hklin  %s << eof > %s\n' % (data_file, logfile))
            aimless_file.write("anomalous on\n")
            aimless_file.write("scales constant\n")
            aimless_file.write("sdcorrection norefine full 1 0 0 partial 1 0 0\n")
            aimless_file.write("cycles 0\n")
            aimless_file.write("OUTPUT NONE\n")
            aimless_file.write("eof")
        os.chmod(comfile, stat.S_IRWXU)
        cmd = './%s' % comfile

        # Run
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        
        # Parse aimless
        graphs, summary = parse_aimless(logfile)

        # Read in the log lines
        log = open(logfile, "r").readlines()

        aimless_results = {
            "log": log,
            "plots": graphs,
            "summary": summary
        }

        return aimless_results

    def run_analysis_plugin(self):
        """Set up and run the analysis plugin"""

        self.logger.debug("run_analysis_plugin")

        # Run analysis
        if self.preferences.get("analysis", False):

            self.logger.debug("Setting up analysis plugin")
            self.tprint("\nLaunching analysis plugin", level=30, color="blue")

            # Make sure we are in the work directory
            start_dir = os.getcwd()
            os.chdir(self.command["directories"]["work"])

            # Queue to exchange information
            #plugin_queue = Queue()

            # Handle site-based var
            self.db_settings = False
            if self.site:
                self.db_settings = self.site.CONTROL_DATABASE_SETTINGS

            # Construct the pdbquery plugin command
            class AnalysisArgs(object):
                """Object containing settings for plugin command construction"""
                clean = self.preferences.get("clean_up", False)
                data_file = self.command["input_data"]["data_file"]
                dir_up = self.preferences.get("dir_up", False)
                json = self.preferences.get("json", True)
                nproc = self.preferences.get("nproc", 1)
                progress = self.preferences.get("progress", False)
                run_mode = self.preferences.get("run_mode", False)
                sample_type = "default"
                show_plots = self.preferences.get("show_plots", False)
                db_settings = self.db_settings
                test = False

            analysis_command = plugins.analysis.commandline.construct_command(AnalysisArgs)

            # The pdbquery plugin
            plugin = plugins.analysis.plugin

            # Print out plugin info
            self.tprint(arg="\nPlugin information", level=10, color="blue")
            self.tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
            self.tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
            self.tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
            self.tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

            # Run the plugin
            self.analysis_process = plugin.RapdPlugin(command=analysis_command,
                                                      processed_results = self.results,
                                                      tprint=self.tprint,
                                                      logger=self.logger)
            self.analysis_process.start()
            
            # Back to where we were, in case it matters
            os.chdir(start_dir)

        # Do not run analysis
        else:
            self.results["analysis"] = False

    def run_pdbquery_plugin(self):
        """Set up and run the pdbquery plugin"""

        self.logger.debug("run_pdbquery_plugin")

        # Run analysis
        if self.preferences.get("pdbquery", False):

            # Now Launch PDBQuery
            self.tprint("\nLaunching PDBQUERY plugin", level=30, color="blue")
            self.tprint("  This can take a while...", level=30, color="white")
            
            # Make sure we are in the work directory
            start_dir = os.getcwd()
            os.chdir(self.command["directories"]["work"])

            # Handle site-based var
            self.db_settings = False
            if self.site:
                self.db_settings = self.site.CONTROL_DATABASE_SETTINGS

            # Construct the pdbquery plugin command
            class PdbqueryArgs(object):
                """Object for command construction"""
                clean = self.preferences.get("clean_up", False)
                data_file = self.command["input_data"]["data_file"]
                dir_up = self.preferences.get("dir_up", False)
                json = self.preferences.get("json", True)
                nproc = self.preferences.get("nproc", 1)
                progress = self.preferences.get("progress", False)
                run_mode = self.preferences.get("run_mode", False)
                db_settings = self.db_settings
                exchange_dir = self.preferences.get("exchange_dir", False)
                pdbs = False
                contaminants = True
                search = True
                test = False
    
            pdbquery_command = plugins.pdbquery.commandline.construct_command(PdbqueryArgs)
    
            # The pdbquery plugin
            plugin = plugins.pdbquery.plugin
    
            # Print out plugin info
            self.tprint(arg="\nPlugin information", level=10, color="blue")
            self.tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
            self.tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
            self.tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
            self.tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")
    
            # Run the plugin
            self.pdbq_process = plugin.RapdPlugin(command=pdbquery_command,
                                                  processed_results = self.results,
                                                  computer_cluster=self.preferences.get("computer_cluster", False),
                                                  tprint=self.tprint,
                                                  logger=self.logger)

            self.pdbq_process.start()
            
            """
            # Allow multiple returns for each part of analysis.
            while True:
                analysis_result = plugin_queue.get()
                self.results["results"]["analysis"] = analysis_result
                self.send_results(self.results)
                if analysis_result['process']["status"] in (-1, 100):
                    break
            """
            #analysis_result = plugin_queue.get()
            #self.results["results"]["analysis"] = analysis_result

            # Back to where we were, in case it matters
            os.chdir(start_dir)

        # Do not run analysis
        else:
            self.results["pdbquery"] = False

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Test assess_integrated_data plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Reduce output")

    args = my_parser.parse_args()

    # Insert logic to check or modify args here

    return args

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    if args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    unittest.main(verbosity=verbosity)

    if __name__ == "__main__":

        main()


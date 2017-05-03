"""analysis RAPD plugin"""

"""
This file is part of RAPD

Copyright (C) 2011-2017, Cornell University
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

__created__ = "2011-02-02"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "ANALYSIS"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "f06818cf1b0f11e79232ac87a3333966"
VERSION = "1.0.0"

# Standard imports
# import argparse
# import from collections import OrderedDict
# import datetime
from distutils.spawn import find_executable
# import glob
import json
import logging
from multiprocessing import Process, Queue
import os
# from pprint import pprint
# import pymongo
# import re
# import redis
import shutil
import subprocess
# import sys
import time
# import unittest
import numpy

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import plugins.subcontractors.parse as parse
import utils.credits as rcredits
import utils.modules as modules
import utils.xutils as xutils
# import info
import plugins.pdbquery.commandline
import plugins.pdbquery.plugin


# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

class RapdPlugin(Process):
    """
    RAPD plugin class

    Command format:
    {
       "command":"analysis",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    input_sg = None
    cell = None
    cell_output = Queue()
    sample_type = "protein"
    solvent_content = 0.55
    stats_timer = 180
    test = True
    volume = None

    xtriage_output_raw = None
    molrep_output_raw = None
    phaser_results = None

    results = {
        "command": None,
        "parsed": {},
        "raw": {},
        "status": 1,
    }

    def __init__(self, command, tprint=False, logger=False):
        """Initialize the plugin"""

        # Keep track of start time
        self.start_time = time.time()

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
        self.logger.info(command)
        # pprint(command)

        # Store passed-in variables
        self.command = command
        self.results["command"] = command

        # Start up processing
        Process.__init__(self, name="analysis")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """Set up for plugin action"""

        # self.tprint("preprocess")
        self.logger.debug("preprocess")

        # Handle sample type from commandline
        if not self.command["preferences"]["sample_type"] == "default":
            self.sample_type = self.command["preferences"]["sample_type"]

        # Make the work_dir if it does not exist.
        if os.path.exists(self.command["directories"]["work"]) == False:
            os.makedirs(self.command["directories"]["work"])

        # Change directory to the one specified in the incoming dict
        os.chdir(self.command["directories"]["work"])

        # Get information from the data file
        self.input_sg, self.cell, self.volume = \
            xutils.get_mtz_info(
                datafile=self.command["input_data"]["datafile"])

        self.tprint("\nReading in datafile", level=30, color="blue")
        self.tprint("  Spacegroup: %s" % self.input_sg, level=20, color="white")
        self.tprint("  Cell: %s" % str(self.cell), level=20, color="white")
        self.tprint("  Volume: %f" % self.volume, level=20, color="white")

        # Handle ribosome sample types
        if (self.command["preferences"]["sample_type"] != "default" and \
            self.volume > 25000000.0) or \
            self.command["preferences"]["sample_type"] == "ribosome": #For 30S
            self.sample_type = "ribosome"
            self.solvent_content = 0.64
            self.stats_timer = 300

        self.tprint("  Sample type: %s" % self.sample_type, level=20, color="white")
        self.tprint("  Solvent content: %s" % self.solvent_content, level=20, color="white")

        # Get some data back into the command
        self.command["preferences"]["sample_type"] = self.sample_type
        self.command["preferences"]["solvent_content"] = self.solvent_content

        if self.test:
            self.logger.debug("TEST IS SET \"ON\"")

    def process(self):
        """Run plugin action"""

        self.tprint("\nAnalyzing the data file", level=30, color="blue")

        self.run_xtriage()
        self.run_molrep()
        self.run_phaser_ncs()

        # Output to terminal
        self.print_xtriage_results()
        self.print_plots()

        # Run the pdbquery
        if self.command["preferences"]["pdbquery"]:
            self.process_pdb_query()

    def postprocess(self):
        """Clean up after plugin action"""

        self.tprint("postprocess", level=10, color="white")

        # Cleanup my mess.
        self.clean_up()

        # Finished
        self.results["status"] = 100

        # Handle JSON output
        self.handle_json()

        # Notify inerested party
        self.handle_return()

    def run_xtriage(self):
        """Run Xtriage and the parse the output"""

        self.tprint("  Running xtriage", level=30, color="white")

        command = "phenix.xtriage %s scaling.input.xray_data.obs_labels=\"I(+),\
SIGI(+),I(-),SIGI(-)\"  scaling.input.parameters.reporting.loggraphs=True" % \
self.command["input_data"]["datafile"]

        xtriage_proc = subprocess.Popen([command,],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)
        # stdout, _ = xtriage_proc.communicate()
        # xtriage_output_raw = stdout
        xtriage_proc.wait()

        # Store raw output
        self.results["raw"]["xtriage"] = open("logfile.log", "r").readlines()

        # Move logfile.log
        shutil.move("logfile.log", "xtriage.log")

        self.results["parsed"]["xtriage"] = \
            parse.parse_xtriage_output(self.results["raw"]["xtriage"])

        return True

    def run_molrep(self):
        """Run Molrep to calculate self rotation function"""

        self.tprint("  Calculating self rotation function",
                    level=30,
                    color="white")

        command = "molrep -f %s -i <<stop\n_DOC  Y\n_RESMAX 4\n_RESMIN 9\nstop"\
                  % self.command["input_data"]["datafile"]

        molrep_proc = subprocess.Popen([command,],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       shell=True)
        stdout, _ = molrep_proc.communicate()
        molrep_output_raw = stdout

        # Store raw output
        self.results["raw"]["molrep"] = molrep_output_raw

        # Save the output in log form
        with open("molrep_selfrf.log", "w") as out_file:
            out_file.write(stdout)

        # Parse the Molrep log
        parsed_molrep_results = parse.parse_molrep_output(molrep_output_raw)

        # Convert the Molrep postscript file to JPEG, if convert is available
        if find_executable("convert"):
            convert_proc = subprocess.Popen(["convert",
                                             "molrep_rf.ps",
                                             "molrep_rf.jpg"],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            shell=False)
            _, stderr = convert_proc.communicate()
            if stderr:
                self.tprint("  Unable to convert postscript to jpeg. Imagemagick needs to be installed",
                            level=30,
                            color="red")
                parsed_molrep_results["self_rotation_image"] = False
            else:
                parsed_molrep_results["self_rotation_image"] = os.path.abspath("molrep_rf.jpg")
        else:
            self.tprint("  Unable to convert postscript to jpeg. Imagemagick needs to be installed",
                        level=30,
                        color="red")
            parsed_molrep_results["self_rotation_image"] = False

        self.results["parsed"]["molrep"] = parsed_molrep_results

        return True

    def run_phaser_ncs(self):
        """Run Phaser tNCS and anisotropy correction"""

        self.tprint("  Analyzing NCS and anisotropy",
                    level=30,
                    color="white")

        command  = "phenix.phaser << eof\nMODE NCS\nHKLIn %s\nLABIn F=F SIGF=SI\
GF\neof\n" % self.command["input_data"]["datafile"]

        phaser_proc = subprocess.Popen([command,],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       shell=True)
        stdout, _ = phaser_proc.communicate()
        phaser_output_raw = stdout

        # Store raw output
        self.results["raw"]["phaser"] = phaser_output_raw

        # Save the output in log form
        with open("phaser_ncs.log", "w") as out_file:
            out_file.write(stdout)

        self.results["parsed"]["phaser"] = parse.parse_phaser_ncs_output(phaser_output_raw)

        return True

    def process_pdb_query(self):
        """Prepare and run PDBQuery"""
        self.logger.debug("process_pdb_query")

        self.tprint("\nLaunching PDBQUERY plugin", level=30, color="blue")
        self.tprint("  This can take a while...", level=30, color="white")

        # Construct the pdbquery plugin command
        class pdbquery_args(object):
            clean = True
            contaminants = True
            datafile = self.command["input_data"]["datafile"]
            json = False
            no_color = False
            nproc = 1
            pdbs = False
            run_mode = "subprocess-interactive"
            search = True
            test = False
            verbose = True

        pdbquery_command = plugins.pdbquery.commandline.construct_command(pdbquery_args)

        # print pdbquery_command

        # The pdbquery plugin
        plugin = plugins.pdbquery.plugin
        # plugin = modules.load_module(seek_module="plugin",
        #                              directories=["plugins.pdbquery"],
        #                              logger=self.logger)

        # Print out plugin info
        self.tprint(arg="\nPlugin information", level=10, color="blue")
        self.tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
        self.tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
        self.tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
        self.tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

        # Run the plugin
        pdbquery_result = plugin.RapdPlugin(pdbquery_command,
                                            self.tprint,
                                            self.logger)

        self.results["pdbquery"] = pdbquery_result

    def clean_up(self):
        """Clean up the working directory"""

        self.tprint("  Cleaning up", level=30, color="white")

        if self.command["preferences"].get("clean", False):

            self.logger.debug("Cleaning up Phaser files and folders")

            # Change to work dir
            os.chdir(self.working_dir)

            # # Gather targets and remove
            # files_to_clean = glob.glob("Phaser_*")
            # for target in files_to_clean:
            #     shutil.rmtree(target)

    def handle_return(self):
        """Output data to consumer"""

        run_mode = self.command["preferences"]["run_mode"]

        if run_mode == "interactive":
            pass
            # self.print_results()
            # self.print_credits()
        elif run_mode == "json":
            pass
        elif run_mode == "server":
            pass
        elif run_mode == "subprocess":
            return self.results
        elif run_mode == "subprocess-interactive":
            # self.print_results()
            # self.print_credits()
            return self.results

    def print_results(self):
        """Print the results to the commandline"""

        self.print_xtriage_results()
        self.print_plots()

    def handle_json(self):
        """Output JSON-formatted results to terminal"""

        json_results = json.dumps(self.results)

        # Write the results to a JSON-encoded file
        with open("result.json", "w") as out_file:
            out_file.write(json_results)

        # If running in JSON mode, print to terminal
        if self.command["preferences"]["run_mode"] == "json":
            print json_results

    def print_xtriage_results(self):
        """Print out the xtriage results"""

        xtriage_results = self.results["parsed"]["xtriage"]

        self.tprint("\nXtriage results", level=99, color="blue")

        self.tprint("  Input spacegroup: %s (%d)" % (
            xtriage_results["spacegroup"]["text"],
            xtriage_results["spacegroup"]["number"]),
                    level=99,
                    color="white")

        self.tprint("\n  Input unit cell: a= %.2f      b= %.2f     c= %.2f" % (
            xtriage_results["unit_cell"]["a"],
            xtriage_results["unit_cell"]["b"],
            xtriage_results["unit_cell"]["c"]),
                    level=99,
                    color="white")
        self.tprint("                   alpha= %.2f  beta= %.2f  gamma= %.2f" % (
            xtriage_results["unit_cell"]["alpha"],
            xtriage_results["unit_cell"]["beta"],
            xtriage_results["unit_cell"]["gamma"]),
                    level=99,
                    color="white")

        self.tprint("\n  Patterson analysis (off-origin peaks)", level=99, color="white")
        self.tprint("                height % of   dist from    fractional coords",
                    level=99,
                    color="white")
        self.tprint("  #   p-value   origin peak     origin      x      y      z",
                    level=99,
                    color="white")
        for peak_id, peak_data in xtriage_results["Patterson peaks"].iteritems():
            self.tprint("  {}   {:6.4f}     {:5.2f}%         {:5.2f}    {:5.3f}  {:5.3f}  {:5.3f}"\
                .format(peak_id,
                        peak_data["p-val"],
                        peak_data["peak"]*100.0,
                        peak_data["dist"],
                        peak_data["frac x"],
                        peak_data["frac y"],
                        peak_data["frac z"]),
                        level=99,
                        color="white")

        self.tprint("\n  Xtriage verdict\n", level=99, color="white")
        for line in xtriage_results["verdict_text"]:
            self.tprint("    %s" % line, level=99, color="white")

    def print_plots(self):
        """Print plots to the terminal"""

        if "interactive" in self.command["preferences"].get("run_mode"):

            self.tprint("\nPlots", level=99, color="blue")

            # Determine the open terminal size
            term_size = os.popen('stty size', 'r').read().split()

            xtriage_plots = self.results["parsed"]["xtriage"]["plots"]
            # pprint(xtriage_plots)

            # The intensity plot
            for plot_label in ("Intensity plots",
                               "Measurability of Anomalous signal",
                               "NZ test",
                               "L test, acentric data",):

                # The plot data
                plot_parameters = xtriage_plots[plot_label]["parameters"]
                plot_data = xtriage_plots[plot_label]["data"]

                # Settings for each plot
                if plot_label == "Intensity plots":
                    plot_title = "Intensity vs. Resolution"
                    x_axis_label = "Resolution (A)"
                    y_axis_label = "Intensity"
                    line_label = y_axis_label
                    reverse = True
                    plot_data = (plot_data[0],)
                elif plot_label == "Measurability of Anomalous signal":
                    plot_title = "Anomalous Measurability"
                    x_axis_label = "Resolution (A)"
                    y_axis_label = "Measurability"
                    line_label = "Measured"
                    # Line for what is meaningful signal
                    y2s = [0.05,] * len(plot_data[0]["series"][0]["ys"])
                    line_label_2 = "Meaningful"
                    reverse = True
                    plot_data = (plot_data[0],)
                elif plot_label in ("NZ test", "L test, acentric data"):
                    # pprint(plot_parameters)
                    # pprint(plot_data)
                    plot_title = plot_parameters["toplabel"]
                    x_axis_label = plot_parameters["x_label"]
                    y_axis_label = ""

                # Determine plot extent
                y_array = numpy.array(plot_data[0]["series"][0]["ys"])
                y_max = y_array.max() * 1.1
                y_min = 0
                x_array = numpy.array(plot_data[0]["series"][0]["xs"])
                x_max = x_array.max()
                x_min = x_array.min()

                # Special y_max & second y set
                if plot_label == "Measurability of Anomalous signal":
                    y_max = max(0.055, y_max)

                gnuplot = subprocess.Popen(["gnuplot"],
                                           stdin=subprocess.PIPE,
                                           stderr=subprocess.PIPE)

                gnuplot.stdin.write("""set term dumb %d,%d
                                       set title '%s'
                                       set xlabel '%s'
                                       set ylabel '%s' rotate by 90 \n""" %
                                    (int(term_size[1])-20,
                                     30,
                                     plot_title,
                                     x_axis_label,
                                     y_axis_label))

                # Create the plot string
                if reverse:
                    plot_string = "plot [%f:%f] [%f:%f] " \
                                      % (x_max, x_min, y_min, y_max)
                else:
                    plot_string = "plot [%f:%f] [%f:%f] " \
                                      % (x_min, x_max, y_min, y_max)
                # Mark the minimum measurability
                if plot_label == "Measurability of Anomalous signal":
                    plot_string += "'-' using 1:2 with lines title '%s', " % line_label_2
                    plot_string += "'-' using 1:2 with lines title '%s'\n" % line_label

                elif plot_label in ("NZ test", "L test, acentric data"):
                    for index, data in enumerate(plot_data):
                        line_label = data["parameters"]["linelabel"]
                        plot_string += "'-' using 1:2 with lines title '%s' " % line_label
                        if index == len(plot_data) - 1:
                            plot_string += "\n"
                        else:
                            plot_string += ", "

                else:
                    plot_string += "'-' using 1:2 title '%s' with lines\n" % line_label

                gnuplot.stdin.write(plot_string)


                # Mark the minimum measurability
                if plot_label == "Measurability of Anomalous signal":
                    # Run through the data and add to gnuplot
                    for plot in plot_data:
                        xs = plot["series"][0]["xs"]
                        ys = plot["series"][0]["ys"]
                        # Minimal impact line
                        for x_val, y_val in zip(xs, y2s):
                            gnuplot.stdin.write("%f %f\n" % (x_val, y_val))
                        gnuplot.stdin.write("e\n")
                        # Experimental line
                        for x_val, y_val in zip(xs, ys):
                            # print x_val, y_val, y2_val
                            gnuplot.stdin.write("%f %f\n" % (x_val, y_val))
                        gnuplot.stdin.write("e\n")
                else:
                    # Run through the data and add to gnuplot
                    for plot in plot_data:
                        xs = plot["series"][0]["xs"]
                        ys = plot["series"][0]["ys"]
                        for x_val, y_val in zip(xs, ys):
                            gnuplot.stdin.write("%f %f\n" % (x_val, y_val))
                        gnuplot.stdin.write("e\n")

                # Now plot!
                gnuplot.stdin.flush()
                time.sleep(2)
                gnuplot.terminate()

    def print_credits(self):
        """Print information on programs used to the terminal"""

        self.tprint(rcredits.HEADER,
                    level=99,
                    color="blue")

        programs = ["CCTBX", "MOLREP", "PHENIX", "PHASER"]
        info_string = rcredits.get_credits_text(programs, "    ")

        self.tprint(info_string, level=99, color="white")

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Test analysis plugin"
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

        commandline_args = get_commandline()

        main(args=commandline_args)


"""
RAPD agent for fast integration with XDS
"""

__license__ = """
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
__created__ = "2011-06-29"
__maintainer__ = "David Neau"
__email__ = "dneau@anl.gov"
__status__ = "Production"

# This is an active rapd agent
RAPD_AGENT = True

# This handler's request type
AGENT_TYPE = "INTEGRATE"
AGENT_SUBTYPE = "CORE"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "bd11f4401eaa11e697c3ac87a3333966"
VERSION = "2.0.0"

# Standard imports
from distutils.spawn import find_executable
import json
import logging
import logging.handlers
import math
from multiprocessing import Process
import os
import os.path
from pprint import pprint
import shutil
import stat
import subprocess
import sys
import threading
import time

import numpy

# RAPD imports
from subcontractors.xdsme.xds2mos import Xds2Mosflm
from utils.communicate import rapd_send
from subcontractors.stats import AutoStats
import utils.xutils as Utils

# Import smartie.py from the installed CCP4 package
# smartie.py is a python script for parsing log files from CCP4
sys.path.append(os.path.join(os.environ["CCP4"], "share", "smartie"))
import smartie

class RapdAgent(Process):
    """
    classdocs

    command format
    {
        "command":"INDEX+STRATEGY",
        "directories":
            {
                "data_root_dir":""                  # Root directory for the data session
                "work":""                           # Where to perform the work
            },
        "image_data":{},                            # Image information
        ["header2":{},]                             # 2nd image information
        "preferences":{}                            # Settings for calculations
        "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    results = {}

    def __init__(self, site, command, tprint=False, logger=False):
        """
        Initialize the agent

        Keyword arguments
        site -- full site settings
        command -- dict of all information for this agent to run
        """

        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        # Get the logger Instance
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Store passed-in variables
        self.site = site
        self.command = command
        # pprint(self.command)
        self.settings = self.command.get("preferences")
        # pprint(self.settings)
        # sys.exit()


        # self.input = input[0:4]
        self.controller_address = self.command.get("return_address", False)
        # self.logger = logger
        self.spacegroup = None

        self.dirs = self.command["directories"]
        self.image_data = self.command.get("data").get("image_data")
        self.run_data = self.command.get("data").get("run_data")
        self.process_id = self.command["process_id"]
        # if "image_data" in self.command:
        #     self.image_data = self.command["image_data"]
        #     self.process_id = self.command["image_data"]["agent_process_id"]
        #     if "run_data" in self.command:
        #         self.image_data.update(self.command["run_data"])
        # elif 'original' in self.command:
        #     self.image_data = self.command['original']
        # else:
        #     self.image_data = self.command

        self.logger.debug("self.image_data = %s", self.image_data)

        # if 'x_beam' not in self.image_data.keys():
        #     self.image_data['x_beam'] = self.image_data['x_beam'] or self.image_data['beam_center_x']
        #     self.image_data['y_beam'] = self.image_data['y_beam'] or self.image_data['beam_center_y']
        # if 'start' not in self.image_data.keys():
        if self.settings.get("start_frame", False):
            self.image_data["start"] = self.settings.get("start_frame")
        else:
            self.image_data["start"] = self.run_data.get("start")
        # print "self.image_data[\"start\"]", self.image_data["start"]

        if self.settings.get("end_frame", False):
            self.image_data["total"] = self.settings.get("end_frame") - self.image_data["start"] + 1
        else:
            self.image_data["total"] = self.run_data.get("total")
        # print "self.image_data[\"total\"]", self.image_data["total"]

        self.image_data['image_template'] = self.run_data['image_template']

        # Check for 2theta tilt:
        if 'twotheta' in self.run_data:
            self.image_data['twotheta'] = self.run_data['twotheta']
            # self.image_data['start'] = self.settings['request']['frame_start']
            # self.image_data['total'] = str( int(self.settings['request']['frame_start'])
            #                         + int(self.settings['request']['frame_finish']) - 1)
        if self.settings.get('spacegroup', False):
            self.spacegroup = self.settings['spacegroup']

        if 'multiprocessing' in self.settings:
            self.cluster_use = self.settings['multiprocessing']
            if self.cluster_use == 'True':
                self.cluster_use = True
            elif self.cluster_use == 'False':
                self.cluster_use = False
        else:
            self.cluster_use = False

        if 'ram_integrate' in self.settings:
            self.ram_use = self.settings['ram_integrate']
            if self.ram_use == 'True':
                self.ram_use = True
            elif self.ram_use == 'False':
                self.ram_use = False
            if self.ram_use == True:
                self.ram_nodes = self.settings['ram_nodes']
            # ram_nodes is a list containing three lists.
            # ram_nodes[0] is a list containing the name of the nodes where
            # data was distributed to.
            # ram_nodes[1] is a list of the first frame number for the wedge
            # of images copied to the corresponding node.
            # ram_nodes[2] is a list of the last frame number for the wedge
            # of images copied to the corresponding node.
            else:
                self.ram_nodes = None
        else:
            self.ram_use = False
            self.ram_nodes = None

        if 'standalone' in self.settings:
            self.standalone = self.settings['standalone']
            if self.standalone == 'True':
                self.standalone = True
            elif self.standalone == 'False':
                self.standalone = False
        else:
            self.standalone = False

        if 'work_dir_override' in self.settings:
            if (self.settings['work_dir_override'] == True or
                self.settings['work_dir_override'] == 'True'):
                self.dirs['work'] = self.settings['work_directory']

        if 'beam_center_override' in self.settings:
            if (self.settings['beam_center_override'] == True or
                self.settings['beam_center_override'] == 'True'):
                self.image_data['x_beam'] = self.settings['x_beam']
                self.image_data['y_beam'] = self.settings['y_beam']

        # Some detectord need flipped for XDS
        if self.settings.get('flip_beam', False):
            x = self.image_data['y_beam']
            self.image_data['y_beam'] = self.image_data['x_beam']
            self.image_data['x_beam'] = x

        self.xds_default = []

        # Parameters likely to be changed based on beamline setup.

        # Directory containing XDS.INP default files for detectors.
        #if os.path.isdir('/home/necat/DETECTOR_DEFAULTS'):
        #    self.detector_directory = '/home/necat/DETECTOR_DEFAULTS/'
            #Also check set_detector_data for other detector dependent values!
        # XDS parameters for number of JOBS and PROCESSORS.
        # Values are beamline specific, depending on computing resources.
        # self.jobs is number of nodes XDS can use for colspot and/or integration.
        # self.procs is number of procesors XDS can use per job.
        if self.cluster_use == True:
            if self.ram_use == True:
                self.jobs = len(self.ram_nodes[0])
                self.procs = 8
            else:
                # Set self.jobs and self.procs based on available cluster resources
                self.jobs = 20
                self.procs = 8
        else:
            # Setting self.jobs > 1 provides some speed up on
            # multiprocessor machines.
            # Should be set based on computer used for processing
            self.jobs = 1
            self.procs = 4

        Process.__init__(self, name="FastIntegration")
        self.start()

    def run(self):
        self.logger.debug('Fastintegration::run')
        self.preprocess()
        self.process()
        #self.postprocess()

    def preprocess(self):
        """
        Things to do before main proces runs.
        1. Change to the correct working directory.
        2. Read in detector specific parameters.
        """
        self.logger.debug('FastIntegration::preprocess')
        if os.path.isdir(self.dirs['work']) == False:
            os.makedirs(self.dirs['work'])
        os.chdir(self.dirs['work'])

        self.xds_default = self.createXDSinp(self.settings['xdsinp'])

        #if 'detector' in self.image_data:
        #    if self.image_data['detector'] in ['PILATUS', 'HF4M', 'rayonix_mx300hs']:
        #        self.xds_default = self.set_detector_data(self.image_data['detector'])
        #    #elif self.image_data['detector'] == 'HF4M':
            #    self.xds_default = self.set_detector_data(self.image_data['detector'])
            #elif self.image_data['detector'] == 'rayonix_mx300hs':
            #	self.xds_default = self.set_detector_data(self.image_data['detector'])
        #    else:
        #        if 'binning' in self.image_data.keys():
        #            if self.image_data['binning'] == '2x2':
        #                self.image_data['detector'] = 'ADSC_binned'
        #                self.xds_default = self.set_detector_data('ADSC_binned')
        #            elif self.image_data['binning'] == 'unbinned' or self.image_data['binning'] == 'none':
        #                self.image_data['detector'] = 'ADSC'
        #                self.xds_default = self.set_detector_data('ADSC')
        #        elif 'bin' in self.image_data.keys():
        #            if self.image_data['bin'] == '2x2':
        #                self.image_data['binning'] = '2x2'
        #                self.image_data['detector'] = 'ADSC_binned'
        #                self.xds_default = self.set_detector_data('ADSC_binned')
        #            elif self.image_data['bin'] == 'unbinned' or self.image_data['bin'] == 'none':
        #                self.image_data['binning'] = 'unbinned'
        #                self.image_data['detector'] = 'ADSC'
        #                self.xds_default = self.set_detector_data('ADSC')

    def process (self):
        """
        Things to do in main process:
        1. Run integration and scaling.
        2. Report integration results.
        3. Run analysis of data set.
        """
        self.logger.debug('FastIntegration::process')
        if not self.command["command"] in ("INTEGRATE", "XDS"):
            self.logger.debug('Program did not request an integration')
            self.logger.debug('Now Exiting!')
            return()

        input = self.xds_default
        if self.command["command"] == 'XDS':
            integration_results = self.xds_total(input)
        else:
            if os.path.isfile(self.last_image) == True:
                if self.ram_use == True:
                    integration_results = self.ram_total(input)
                else:
                    integration_results = self.xds_total(input)
            else:
                if self.ram_use == True:
                    integration_results = self.ram_integrate(input)
                elif (self.image_data['detector'] == 'ADSC' or
    #                  self.image_data['detector'] == 'PILATUS' or
                      self.cluster_use == False):
                    integration_results = self.xds_split(input)
                else:
                    integration_results = self.xds_processing(input)
            os.chdir(self.dirs['work'])
        if integration_results == 'False':
            # Do a quick clean up?
            pass
        else:
            final_results = self.finish_data(integration_results)

        # Set up the results for return
        self.results['process'] = {
        	'agent_process_id':self.process_id,
        	'status':100 }
        self.results['results'] = final_results
        self.logger.debug(self.results)
        #self.sendBack2(results)

        self.write_json(self.results)

        # Skip this for now
        self.print_info()
        return()

        analysis = self.run_analysis(final_results['files']['mtzfile'], self.dirs['work'])
        analysis = 'Success'
        if analysis == 'Failed':
            self.logger.debug(analysis)
            # Add method for dealing with a failure by run_analysis.
            pass
        elif analysis == 'Success':
            self.logger.debug(analysis)
            self.results["status"] = "SUCCESS"
            self.logger.debug(self.results)
            # self.sendBack2(results)
            if self.controller_address:
                rapd_send(self.controller_address, self.results)

        return()

    def print_results(self, results):
        """Print out results to the terminal"""

        if isinstance(results, dict):

            # Print summary
            summary = results["summary"]
            # pprint(summary)
            self.tprint("  Spacegroup: %s" % summary["scaling_spacegroup"], 99, "white")
            self.tprint("  Unit cell: %5.1f %5.1f %5.1f %5.2f %5.2f %5.2f" % tuple(summary["scaling_unit_cell"]), 99, "white")
            self.tprint("  Mosaicity: %5.3f" % summary["mosaicity"], 99, "white")
            self.tprint("                        overall   inner shell   outer shell", 99, "white")
            self.tprint("  High res limit         %5.2f       %5.2f         %5.2f" % tuple(summary["bins_high"]), 99, "white")
            self.tprint("  Low res limit          %5.2f       %5.2f         %5.2f" % tuple(summary["bins_low"]), 99, "white")
            self.tprint("  Completeness           %5.1f       %5.1f         %5.1f" % tuple(summary["completeness"]), 99, "white")
            self.tprint("  Multiplicity            %4.1f        %4.1f          %4.1f" % tuple(summary["multiplicity"]), 99, "white")
            self.tprint("  I/sigma(I)              %4.1f        %4.1f          %4.1f" % tuple(summary["isigi"]), 99, "white")
            self.tprint("  CC(1/2)                %5.3f       %5.3f         %5.3f" % tuple(summary["cc-half"]), 99, "white")
            self.tprint("  Rmerge                 %5.3f       %5.3f         %5.3f" % tuple(summary["rmerge_norm"]), 99, "white")
            self.tprint("  Anom Rmerge            %5.3f       %5.3f         %5.3f" % tuple(summary["rmerge_anom"]), 99, "white")
            self.tprint("  Rmeas                  %5.3f       %5.3f         %5.3f" % tuple(summary["rmeas_norm"]), 99, "white")
            self.tprint("  Anom Rmeas             %5.3f       %5.3f         %5.3f" % tuple(summary["rmeas_anom"]), 99, "white")
            self.tprint("  Rpim                   %5.3f       %5.3f         %5.3f" % tuple(summary["rpim_norm"]), 99, "white")
            self.tprint("  Anom Rpim              %5.3f       %5.3f         %5.3f" % tuple(summary["rpim_anom"]), 99, "white")
            self.tprint("  Anom Completeness      %5.1f       %5.1f         %5.1f" % tuple(summary["anom_completeness"]), 99, "white")
            self.tprint("  Anom Multiplicity       %4.1f        %4.1f          %4.1f" % tuple(summary["anom_multiplicity"]), 99, "white")
            self.tprint("  Anom Correlation      %5.3f      %5.3f        %5.3f" % tuple(summary["anom_correlation"]), 99, "white")
            self.tprint("  Anom Slope             %5.3f" % summary["anom_slope"][0], 99, "white")
            self.tprint("  Observations         %7d     %7d       %7d" % tuple(summary["total_obs"]), 99, "white")
            self.tprint("  Unique Observations  %7d     %7d       %7d\n" % tuple(summary["unique_obs"]), 99, "white")

    def print_plots(self, results):
        """Display plots on the commandline"""

        # Plot as long as JSON output is not selected
        if self.settings.get("show_plots", True) and (not self.settings.get("json_output", False)):

            # Possible titles - more for documentation
            plot_titles = [
                'I/sigma, Mean Mn(I)/sd(Mn(I))',
                'Average I, RMS deviation, and Sd',
                'Completeness',
                'RMS correlation ration',
                'Imean/RMS scatter',
                'Rmerge, Rfull, Rmeas, Rpim vs. Resolution',
                'Radiation Damage',
                'Rmerge vs Frame',
                'Redundancy',
                'Anomalous & Imean CCs vs Resolution'
                ]

            plots = results["plots"]

            # Determine the open terminal size
            term_size = os.popen('stty size', 'r').read().split()

            titled = False

            plot_type = "Rmerge vs Frame"
            if plot_type in plots:

                if not titled:
                    self.tprint(arg="\nPlots from integration", level=99, color="blue")
                    titled = True

                #             tag = {"osc_range":"standard", "osc_range_anom":"ANOMALOUS"}[plot_type]

                plot_data = plots[plot_type]["data"]
                plot_params = plots[plot_type]["parameters"]
                # pprint(plot_data)

                # Get each subplot
                raw = False
                smoothed = False
                for subplot in plot_data:
                    # pprint(subplot)
                    if subplot["parameters"]["linelabel"] == "SmRmerge":
                        smoothed = subplot
                    elif subplot["parameters"]["linelabel"] == "Rmerge":
                        raw = subplot

                # Determine plot extent
                y_array = numpy.array(raw["series"][0]["ys"])
                y_max = y_array.max() * 1.1
                y_min = 0 # max(0, (y_array.min() - 10))
                x_array = numpy.array(raw["series"][0]["xs"])
                x_max = x_array.max()
                x_min = x_array.min()

                # print y_min, y_max, x_min, x_max

                gnuplot = subprocess.Popen(["gnuplot"], stdin=subprocess.PIPE) # %s,%s  (term_size[1], int(int(term_size[0])/3),
                gnuplot.stdin.write("""set term dumb %s,%s
                                       set title 'Rmerge vs. Batch'
                                       set xlabel 'Image #'
                                       set ylabel 'Rmerge' rotate by 90 \n""" %  (min(180, term_size[1]), max(30, int(int(term_size[0])/3))))

                # Create the plot string
                plot_string = "plot [%d:%d] [%f:%f] " % (x_min, x_max, y_min, y_max)
                plot_string += "'-' using 1:2 title 'Rmerge' with lines\n"
                # plot_string += "'-' using 1:2 title 'Smooth' with points\n"
                gnuplot.stdin.write(plot_string)

                # Run through the data and add to gnuplot
                for plot in (raw, ): #smoothed):
                    # plot = plot_data["data"][i]
                    xs = plot["series"][0]["xs"]
                    ys = plot["series"][0]["ys"]
                    # print xs
                    # print ys
                    for i, j in zip(xs, ys):
                        gnuplot.stdin.write("%f %f\n" % (i,j))
                    gnuplot.stdin.write("e\n")

                # Now plot!
                gnuplot.stdin.flush()
                time.sleep(3)
                gnuplot.terminate()


    def print_info(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('AutoindexingStrategy::print_info')

        # try:
        self.tprint(arg="\nRAPD integration uses:", level=99, color="blue")
        """
'\n\nRAPD used the following programs for integrating and scaling the dataset:\n',
               '  XDS - \n',
               '       "XDS", W. Kabsch (2010) Acta Cryst. D66, 125-132.\n',
               '       "Integration, scaling, space-group assignment and post-refinement",',
               ' W. Kabsch (2010) Acta Cryst. D66, 133-144.\n',
               '  pointless and aimless - \n',
               '      "Scaling and assessment of data quality", P.R.',
               ' Evans (2006) Acta Cryst. D62, 72-82.\n',
               '      "An introduction to data reduction: space-group',
               ' determination and intensity statistics,',
               ' P.R. Evans (2011) Acta Cryst. D67, 282-292\n',
               '      "How good are my data and what is the resolution?"',
               ' P.R. Evans and G.N. Murshudov (2013) Acta Cryst. D66,',
               ' 1204-1214.\n',
               '  truncate, freerflag, and mtz2various  - \n',
               '       "The CCP4 Suite: Programs for Protein ',
               'Crystallography". Acta Cryst. D50, 760-763 \n',
               '  xdsstat - \n      http://strucbio.biologie.',
               'uni-konstanz.de/xdswiki/index.php/Xdsstat\n',
               '\n</pre></div></div></body>'
               ]
        """
        info_string = """    XDS
    "XDS", W. Kabsch (2010) Acta Cryst. D66, 125-132.
    "Integration, scaling, space-group assignment and post-refinement",
    W. Kabsch (2010) Acta Cryst. D66, 133-144.

    Pointless & Aimless
    "Scaling and assessment of data quality", P.R. Evans (2006) Acta Cryst.
    D62, 72-82.
    "An introduction to data reduction: space-group determination and
    intensity statistics", P.R. Evans (2011) Acta Cryst. D67, 282-292.
    "How good are my data and what is the resolution?", P.R. Evans and
    G.N. Murshudov (2013) Acta Cryst. D66, 1204-1214.
    """

        self.tprint(arg=info_string, level=99, color="white")

        self.logger.debug(info_string)

    def write_json(self, results):
        """Write a file with the JSON version of the results"""

        with open ("result.json", 'w') as outfile:
            outfile.writelines(json.dumps(results))


    def ram_total (self, xdsinput):
        """
        This function controls processing by XDS when the complete data
        is present and distributed to ramdisks on the cluster
        """
        self.logger.debug('Fastintegration::ram_total')
        first = int(self.image_data['start'])
        last = int(self.image_data['start']) + int(self.image_data['total']) -1
        data_range = '%s %s' %(first, last)
        dir = 'wedge_%s_%s' %(first, last)
        xdsdir = os.path.join(self.dirs['work'], dir)
        if os.path.isdir(xdsdir) == False:
            os.mkdir(xdsdir)
        os.chdir(xdsdir)

        # Figure out how many images are on the first node.
        # If greater than self.procs, simply set up spot ranges with a number
        # of images equal to self.procs from the first and last ram nodes.
        # If less than self.procs, reduce self.procs and set up spot ranges
        # with all of the images on the first and last ram nodes.
        Num_images = self.ram_nodes[2][0] - self.ram_nodes[1][0] + 1
        if Num_images  < self.procs:
            self.procs = Num_images
        spot_range = self.ram_nodes[1][0] + self.procs - 1

        xdsinp = xdsinput[:]
        xdsinp.append('JOB=XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n')
        # Add the spot ranges.
        xdsinp.append('SPOT_RANGE=%s %s\n' %(self.ram_nodes[1][0], spot_range))
        # Make sure the last ram node has an adequate number of images available.
        spot_range = self.ram_nodes[1][-1] + self.procs - 1
        if self.ram_nodes[2][-1] < spot_range:
            spot_range = self.ram_nodes[2][-1]
        xdsinp.append('SPOT_RANGE=%s %s\n' %(self.ram_nodes[1][-1], spot_range))
        xdsinp.append('DATA_RANGE=%s\n' % data_range)
        self.write_file('XDS.INP', xdsinp)
        self.write_forkscripts(self.ram_nodes, self.image_data['osc_range'])

        self.xds_ram(self.ram_nodes[0][0])

        newinp = self.check_for_xds_errors(xdsdir,xdsinp)
        if newinp == False:
            self.logger.debug('  Unknown xds error occurred. Please check for cause!')
            self.tprint(arg="Unknown xds error occurred. Please check for cause!",
                        level=10,
                        color="red")
            raise Exception("Unknown XDS error")
            return False
        else:
            # Find a suitable cutoff for resolution
            # Returns False if no new cutoff, otherwise returns the value of
            # the high resolution cutoff as a float value.
            new_rescut = self.find_correct_res(xdsdir, 1.0)
            if new_rescut != False:
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.nocutoff' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.nocutoff' %xdsdir)
                newinp[-2] = 'JOB=CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n'
                newinp[-3] = 'INCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % new_rescut
                self.write_file('XDS.INP', newinp)
                self.xds_ram(self.ram_nodes[0][0])
            # Prepare the display of results.
            final_results = self.run_results(xdsdir)

            # Polish up xds processing by moving GXPARM.XDS to XPARM.XDS
            # and rerunning xds.
            #
            # Don't polish if low resolution, as this tend to blow up.
            if new_rescut <= 4.5:
                os.rename('%s/GXPARM.XDS' %xdsdir, '%s/XPARM.XDS' %xdsdir)
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.old' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.old' %xdsdir)
                newinp[-2] = 'JOB=INTEGRATE CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n'
                newinp[-3] = '\n'
                self.write_file('XDS.INP', newinp)
                self.xds_ram(self.ram_nodes[0][0])
                #Check to see if a new resolution cutoff should be applied
                #new_rescut = self.find_correct_res(xdsdir, 1.0)
                #if new_rescut != False:
                #    os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.nocutoff' %xdsdir)
                #    os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.nocutoff' %xdsdir)
                #    newinp[-2] = 'JOB=CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n'
                #    newinp[-5] = 'INCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % new_rescut
                #    self.write_file('XDS.INP', newinp)
                #    self.xds_ram(self.ram_nodes[0][0])
                #    new_rescut = self.find_correct_res(xdsdir, 1.0)
                #    if new_rescut != False:
                #        os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.oldcutoff' %xdsdir)
                #        os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.oldcutoff' %xdsdir)
                #        newinp[-5] = 'INCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % new_rescut
                #        self.write_file('XDS.INP', newinp)
                #        self.xds_ram(self.ram_nodes[0][0])
                final_results = self.run_results(xdsdir)

            final_results['status'] = 'SUCCESS'
            return(final_results)


    def xds_total (self, xdsinput):
        """
        This function controls processing by XDS when the complete data
        set is already present on the computer system.
        """
        self.logger.debug('Fastintegration::xds_total')
        self.tprint(arg="\nXDS processing", level=99, color="blue")

        first = int(self.image_data['start'])
        last = int(self.image_data['start']) + int(self.image_data['total']) -1
        data_range = '%s %s' %(first, last)
        self.logger.debug('start = %s, total = %s' %(self.image_data['start'], self.image_data['total']))
        self.logger.debug('first - %s, last = %s' %(first,last))
        self.logger.debug('data_range = %s' % data_range)
        dir = 'wedge_%s_%s' %(first,last)
        xdsdir = os.path.join(self.dirs['work'],dir)
        if os.path.isdir(xdsdir) == False:
            os.mkdir(xdsdir)

        xdsinp = xdsinput[:]
        #xdsinp= self.find_spot_range(first, last, self.image_data['osc_range'], xdsinput[:])
        xdsinp.append('MAXIMUM_NUMBER_OF_PROCESSORS=%s\n' % self.procs)
        xdsinp.append('MAXIMUM_NUMBER_OF_JOBS=%s\n' % self.jobs)
        #xdsinp.append('MAXIMUM_NUMBER_OF_JOBS=1\n')
        xdsinp.append('JOB=XYCORR INIT COLSPOT !IDXREF DEFPIX INTEGRATE CORRECT\n\n')
        xdsinp.append('DATA_RANGE=%s\n' % data_range)
        xdsfile = os.path.join(xdsdir,'XDS.INP')
        self.write_file(xdsfile, xdsinp)

        # Run XDS
        self.tprint(arg="  Searching for peaks",
                    level=99,
                    color="white",
                    newline=False)
        self.xds_run(xdsdir)

        #xdsinp[-3] =('MAXIMUM_NUMBER_OF_JOBS=%s\n' % self.jobs)
        xdsinp[-2] =("JOB=IDXREF DEFPIX INTEGRATE CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n")
        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Indexing and integrating",
                    level=99,
                    color="white",
                    newline=False)
        self.xds_run(xdsdir)

        # If known xds_errors occur, catch them and take corrective action
        newinp = self.check_for_xds_errors(xdsdir, xdsinp)
        if newinp == False:
            self.logger.exception('Unknown xds error occurred. Please check for cause!')
            self.tprint(arg="\nXDS error unknown to RAPD has occurred. Please check for cause!",
                        level=30,
                        color="red")
            # TODO  put out failing JSON
            raise Exception("XDS error unknown to RAPD has occurred.")

        elif self.spacegroup != None:
            # Check consistency of spacegroup, and modify if necessary.
            xdsinp = self.find_xds_symm(xdsdir, xdsinp)

        # Prepare the display of results.
        prelim_results = self.run_results(xdsdir)
        self.tprint("\nPreliminary results summary", 99, "blue")
        self.print_results(prelim_results)

        # Find a suitable cutoff for resolution
        # Returns False if no new cutoff, otherwise returns the value of
        # the high resolution cutoff as a float value.
        new_rescut = self.find_correct_res(xdsdir, 1.0)
        newinp[-2] = 'JOB= INTEGRATE CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n'
        if new_rescut != False:
            os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.nocutoff' %xdsdir)
            os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.nocutoff' %xdsdir)
            #newinp[-2] = 'JOB= INTEGRATE CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n'
            newinp[-2] = '%sINCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % (newinp[-2], new_rescut)
            self.write_file(xdsfile, newinp)
            self.tprint(arg="  Reintegrating with new resolution cutoff",
                        level=99,
                        color="white",
                        newline=False)
            self.xds_run(xdsdir)

        # Prepare the display of results.
        prelim_results_2 = self.run_results(xdsdir)
        self.tprint("\nIntermediate results summary", 99, "blue")
        self.print_results(prelim_results_2)

        # Polish up xds processing by moving GXPARM.XDS to XPARM.XDS
        # and rerunning xds.
        #
        # If low resolution, don't try to polish the data, as this tends to blow up.
        if new_rescut <= 4.5:
            os.rename('%s/GXPARM.XDS' %xdsdir, '%s/XPARM.XDS' %xdsdir)
            os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.old' %xdsdir)
            os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.old' %xdsdir)
            #newinp[-2] = 'JOB=INTEGRATE CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n'
            self.write_file(xdsfile, newinp)
            self.tprint(arg="  Polishing",
                        level=99,
                        color="white",
                        newline=False)
            self.xds_run(xdsdir)
            final_results = self.run_results(xdsdir)
        else:
            # Check to see if a new resolution cutoff should be applied
            new_rescut = self.find_correct_res(xdsdir, 1.0)
            if new_rescut != False:
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.oldcutoff' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.oldcutoff' %xdsdir)
                #newinp[-2] = 'JOB=INTEGRATE CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n'
                newinp[-2] = '%sINCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % (newinp[-2], new_rescut)
                self.write_file(xdsfile, newinp)
                self.tprint(arg="  New resolution cutoff", level=99, color="white", newline=False)
                self.xds_run(xdsdir)
        #        old_rescut = new_rescut
        #        new_rescut = self.find_correct_res(xdsdir, 1.0)
        #        if new_rescut != False:
        #            os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.oldcutoff' %xdsdir)
        #            os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.oldcutoff' %xdsdir)
        #            newinp[-5] = 'INCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % new_rescut
        #            self.write_file(xdsfile, newinp)
        #            self.xds_run(xdsdir)
            final_results = self.run_results(xdsdir)

        # Put data into the commanline
        self.tprint("\nFinal results summary", 99, "blue")
        self.print_results(final_results)
        self.print_plots(final_results)

        final_results['status'] = 'ANALYSIS'
        return(final_results)

    def xds_split (self, xdsinput):
        """
        Controls xds processing for unibinned ADSC data
        Launches XDS when half the data set has been collected and again once
        the complete data set has been collected.
        """
        self.logger.debug("FastIntegration::xds_split")

        first_frame = int(self.image_data['start'])
        half_set = (int(self.image_data['total']) / 2) + first_frame - 1
        last_frame = int(self.image_data['start']) + int(self.image_data['total']) - 1
        frame_count = first_frame + 1

        file_template = os.path.join(self.image_data['directory'],self.image_template)
        # Figure out how many digits needed to pad image number.
        # First split off the <image number>.<extension> portion of the file_template.
        numimg = self.image_template.split('_')[-1]
        # Then split off the image number portion.
        num = numimg.split('.')[0]
        # Then find the length of the number portion
        pad = len(num)
        replace_string = ''
        for i in range (0, pad, 1):
            replace_string += '?'

        look_for_file = file_template.replace(replace_string,
                                              '%0*d' %(pad, frame_count))

        # Maximum wait time for next image is exposure time + 30 seconds.
        wait_time = int(math.ceil(float(self.image_data['time']))) + 30

        timer = Process(target=time.sleep, args=(wait_time,))
        timer.start()

        while frame_count < last_frame:
            if os.path.isfile(look_for_file) == True:
                if timer.is_alive():
                    timer.terminate()
                timer = Process(target=time.sleep, args=(wait_time,))
                timer.start()
                if frame_count == half_set:
                    proc_dir = 'wedge_%s_%s' % (first_frame, frame_count)
                    xds_job = Process(target= self.xds_wedge,
                                      args= (proc_dir, frame_count, xdsinput))
                    xds_job.start()
                frame_count += 1
                look_for_file = file_template.replace(replace_string,
                                              '%0*d' %(pad, frame_count))
            elif timer.is_alive() == False:
                self.logger.debug('     Image %s not found after waiting %s seconds.'
                                  % (look_for_file, wait_time))
                self.logger.debug('     RAPD assumes the data collection has been aborted.')
                self.logger.debug('         Launching a final xds job with last image detected.')
                self.image_data['last'] = frame_count - 1
                results = self.xds_total(xdsinput)
                return(results)

        # If you reach here, frame_count equals the last frame, so look for the
        # last frame and then launch xds_total.
        while timer.is_alive():
            if os.path.isfile(self.last_image):
                if xds_job.is_alive():
                    xds_job.terminate()
                results = self.xds_total(xdsinput)
                timer.terminate()
                break

        # If timer expires (ending the above loop) and last frame has not been
        # detected, launch xds_total with last detected image.
        if os.path.isfile(self.last_image) == False:
            if xds_job.is_alive():
                xds_job.terminate()
            self.image_data['last'] = frame_count - 1
            results = self.xds_total(xdsinput)

        return(results)

    def xds_processing (self, xdsinput):
        """
        Controls processing of data on disks (i.e. not stored in RAM)
        by xds.  Attempts to process every 10 images up to 100 and then
        every 20 images after that. This function should be used for NE-CAT
        data collected on ADSC in binned mode
        """

        """
        Need to set up a control where every ten frames an XDS processing is launched.
        Need to keep track of what's been launched.  To avoid launching too many XDS
        jobs, if an XDS job is running when next ten frames are collected, don't launch
        new wedge but rather wait for next multiple of 10. XDS jobs should be checked for
        common errors and rerun if needed.  A resolution cutoff should be generated at the
        CORRECT stage (pass this cutoff on to next wedge?).  Once the data set is complete,
        last XDS should be "polished" by moving GXPARM.XDS to XPARM.XDS

        As XDS jobs finish, launch whatever generates the GUI display

        """
        self.logger.debug('FastIntegration::xds_processing')
        first_frame = int(self.image_data['start'])
        last_frame =  + int(self.image_data['total']) - int(self.image_data['start']) + 1

        frame_count = first_frame
        # Maximum wait time for next image is exposure time + 15 seconds.
        #wait_time = int(math.ceil(float(self.image_data['time']))) + 15
        # Maximum wait time for next image is exposure time + 60 seconds.
        if self.image_data['detector'] == 'PILATUS' or self.image_data['detector'] == 'HF4M':
            wait_time = int(math.ceil(float(self.image_data['time']))) + 15
        else:
            wait_time = int(math.ceil(float(self.image_data['time']))) + 60
        try:
            wedge_size=int(10 // float(self.image_data['osc_range']))
        except:
            self.logger.debug('xds_processing:: dynamic wedge size allocation failed!')
            self.logger.debug('                 Setting wedge size to 10.')
            wedge_size = 10

        file_template = os.path.join(self.image_data['directory'],self.image_template)
        # Figure out how many digits needed to pad image number.
        # First split off the <image number>.<extension> portion of the file_template.
        numimg = self.image_template.split('_')[-1]
        # Then split off the image number portion.
        num = numimg.split('.')[0]
        # Then find the length of the number portion
        pad = len(num)
        replace_string = ''
        for i in range (0, pad, 1):
            replace_string += '?'

        look_for_file = file_template.replace(replace_string,
                                              '%0*d' %(pad, frame_count))

        timer = Process(target = time.sleep, args = (wait_time,))
        timer.start()
        # Create the process xds_job (runs a timer with no delay).
        # This is so xds_job exists when it is checked for later on.
        # Eventually xds_job is replaced by the actual integration jobs.
        xds_job = Process(target=time.sleep, args = (0,))
        xds_job.start()

        while frame_count < last_frame:
            # Look for next look_for_file to see if it exists.
            # If it does, check to see if it is a tenth image.
            # If it is a tenth image, launch an xds job.
            # If it isn't a tenth image, index the look_for_file
            # If it doesn't exist, keep checking until time_process expires.
            if os.path.isfile(look_for_file) == True:
                # Reset the timer process
                if timer.is_alive():
                    timer.terminate()
                timer = Process(target = time.sleep, args = (wait_time,))
                timer.start()
                # If frame_count is a tenth image, launch and xds job
                remainder = ((frame_count + 1) - first_frame) % wedge_size
                #self.logger.debug('	remainder = %s' % remainder)
                if xds_job.is_alive == True:
                    self.logger.debug('		xds_job.is_alive = True')
                if ( ((frame_count + 1) -first_frame) % wedge_size == 0 and
                     xds_job.is_alive() == False):
                    proc_dir = 'wedge_%s_%s' %(first_frame, frame_count)
                    xds_job = Process(target = self.xds_wedge,
                            args = (proc_dir, frame_count, xdsinput))
                    xds_job.start()
                # Increment the frame count to look for next image
                frame_count += 1
                look_for_file = file_template.replace(replace_string,
                                              '%0*d' %(pad, frame_count))
            # If next frame does not exist, check to see if timer has expired.
            # If timer has expired, assume an abort has occurred.
            elif timer.is_alive() == False:
                    self.logger.debug('     Image %s not found after waiting %s seconds.'
                                      % (look_for_file, wait_time))
                    # There have been a few cases, particularly with Pilatus's
                    # Furka file transfer has failed to copy an image to disk.
                    # So check for the next two files before assuming there has
                    # been an abort.
                    self.logger.debug('     RAPD assumes the data collection has been aborted.')
                    self.logger.debug('     RAPD checking for next two subsequent images to be sure.')
                    frame_count += 1
                    look_for_file = file_template.replace(replace_string,'%0*d' %(pad, frame_count))
                    if os.path.isfile(look_for_file) == True:
                        timer = Process(target = time.sleep, args = (wait_time,))
                        timer.start()
                        # Increment the frame count to look for next image
                        frame_count += 1
                        look_for_file = file_template.replace(replace_string,
                                                      '%0*d' %(pad, frame_count))
                    else:
                        self.logger.debug('    RAPD did not fine the next image, checking for one more.')
                        frame_count += 1
                        look_for_file = file_template.replace(replace_string, '%0*d' %(pad, frame_count))
                        if os.path.isfile(look_for_file) == True:
                            timer = Process(target = time.sleep, args = (wait_time,))
                            timer.start()
                            frame_count += 1
                            look_for_file = file_template.replace(replace_string, '%0*d' %(pad, frame_count))
                        else:
                            self.logger.debug('         RAPD did not find the next image either.')
                            self.logger.debug('         Launching a final xds job with last image detected.')
                            self.image_data['total'] = frame_count - 2 - first_frame
                            results = self.xds_total(xdsinput)
                            return(results)

        # If you reach here, frame_count equals the last frame, so look for the
        # last frame and then launch xds_total.
        while timer.is_alive():
            if os.path.isfile(self.last_image):
                if xds_job.is_alive():
                    xds_job.terminate()
                results = self.xds_total(xdsinput)
                timer.terminate()
                break

        # If timer expires (ending the above loop) and last frame has not been
        # detected, launch xds_total with last detected image.
        if os.path.isfile(self.last_image) == False:
            if xds_job.is_alive():
                xds_job.terminate()
            self.image_data['total'] = frame_count - first_frame
            results = self.xds_total(xdsinput)

        return(results)

    def xds_wedge (self, dir, last, xdsinput):
        """
        This function controls processing by XDS for an intermediate wedge
        """
        self.logger.debug('Fastintegration::xds_wedge')
        self.tprint(arg="\nXDS processing", level=99, color="blue")

        first = int(self.image_data['start'])
        data_range = '%s %s' %(first, last)
        xdsdir = os.path.join(self.dirs['work'],dir)
        if os.path.isdir(xdsdir) == False:
            os.mkdir(xdsdir)

        xdsinp = xdsinput[:]
        #xdsinp = self.find_spot_range(first, last, self.image_data['osc_range'],xdsinput[:])
        xdsinp.append('MAXIMUM_NUMBER_OF_PROCESSORS=%s\n' % self.procs)
        xdsinp.append('MAXIMUM_NUMBER_OF_JOBS=%s\n' % self.jobs)
        #xdsinp.append('MAXIMUM_NUMBER_OF_JOBS=1\n')
        xdsinp.append('JOB=XYCORR INIT COLSPOT !IDXREF DEFPIX INTEGRATE CORRECT\n\n')
        xdsinp.append('DATA_RANGE=%s\n' % data_range)
        xdsfile = os.path.join(xdsdir,'XDS.INP')
        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Searching for peaks wedge", level=99, color="white", newline=False)
        self.xds_run(xdsdir)

        #xdsinp[-3]=('MAXIMUM_NUMBER_OF_JOBS=%s\n'  % self.jobs)
        xdsinp[-2]=('JOB=IDXREF DEFPIX INTEGRATE CORRECT !XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n\n')
        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Indexing and integrating", level=99, color="white", newline=False)
        self.xds_run(xdsdir)

        # If known xds_errors occur, catch them and take corrective action
        newinp = 'check_again'
        while newinp == 'check_again':
            newinp = self.check_for_xds_errors(xdsdir, xdsinp)
        if newinp == False:
            self.logger.debug('  Unknown xds error occurred for %s.' %dir)
            self.logger.debug('  Please check for cause!')
            return()
        else:
            # Find a suitable cutoff for resolution
            # Returns False if no new cutoff, otherwise returns the value of
            # the high resolution cutoff as a float value.
            new_rescut = self.find_correct_res(xdsdir, 1.0)
            if new_rescut != False:
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.nocutoff' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.nocutoff' %xdsdir)
                newinp[-2] = 'JOB=INTEGRATE CORRECT\n'
                newinp[-2] = '%sINCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % (newinp[-2], new_rescut)
                self.write_file(xdsfile, newinp)
                self.tprint(arg="  Reintegrating", level=99, color="white", newline=False)
                self.xds_run(xdsdir)
            results = self.run_results(xdsdir)
        return(results)

    def createXDSinp (self, xds_dict):
    	"""
    	This function takes the dict holding XDS keywords and values
    	and converts them into a list of strings that serves as the
    	basis for writing out an XDS.INP file.
    	"""

    	self.logger.debug("FastIntegration::createXDSinp")

        # print self.image_data["start"]
        # print self.image_data["total"]

        last_frame = self.image_data['start'] + self.image_data["total"] - 1
        self.logger.debug('last_frame = %s' % last_frame)
        # print last_frame
        # self.logger.debug('detector_type = %s' % detector_type)
        background_range = '%s %s' %(int(self.image_data['start']), int(self.image_data['start']) + 4)

    	x_beam = float(self.image_data['x_beam']) / float(self.image_data['pixel_size'])
        y_beam = float(self.image_data['y_beam']) / float(self.image_data['pixel_size'])
        #if x_beam < 0 or x_beam > int(xds_dict['NX']):
        #    raise RuntimeError, 'x beam coordinate outside detector'
        #if y_beam < 0 or y_beam > int(xds_dict['NY']):
        #    raise RuntimeError, 'y beam coordinate outside detector'

    	if 'image_template' in self.image_data:
    	    self.image_template = self.image_data['image_template']
    	else:
    	    raise RuntimeError, '"image_template" not defined in input data.'

    	file_template = os.path.join(self.image_data['directory'], self.image_template)
    	# Count the number of '?' that need to be padded in a image filename.
    	pad = file_template.count('?')
    	# Replace the first instance of '?' with the padded out image number
    	# of the last frame
    	self.last_image = file_template.replace('?','%d'.zfill(pad) %last_frame,1)
    	# Remove the remaining '?'
    	self.last_image = self.last_image.replace('?','')
    	# Repeat the last two steps for the first image's filename.
    	self.first_image = file_template.replace('?', str(self.image_data['start']).zfill(pad),1)
    	self.first_image = self.first_image.replace('?','')

    	# Begin constructing the list that will represent the XDS.INP file.
    	xds_input = ['!===== DATA SET DEPENDENT PARAMETERS =====\n',
                      'ORGX=%.2f ORGY=%.2f ! Beam Center (pixels)\n' % (x_beam, y_beam),
                      'DETECTOR_DISTANCE=%.2f ! (mm)\n' % (float(self.image_data['distance'])),
                      'OSCILLATION_RANGE=%.2f ! (degrees)\n' % (float(self.image_data['osc_range'])),
                      'X-RAY_WAVELENGTH=%.5f ! (Angstroems)\n' % (float(self.image_data['wavelength'])),
                      'NAME_TEMPLATE_OF_DATA_FRAMES=%s\n\n' % file_template,
    		          'BACKGROUND_RANGE=%s\n\n' % background_range,
                      '!===== DETECTOR_PARAMETERS =====\n']
    	for key, value in xds_dict.iteritems():
            # Regions that are excluded are defined with
            # various keyword containing the word UNTRUSTED.
            # Since multiple regions may be specified using
            # the same keyword on XDS but a dict cannot
            # have multiple values assigned to a key,
            # the following if statements work though any
            # of these regions and add them to xdsinput.
            if 'UNTRUSTED' in key:
                if 'RECTANGLE' in key:
                    line = 'UNTRUSTED_RECTANGLE=%s\n' %value
                elif 'ELLIPSE' in key:
                    line = 'UNTRUSTED_ELLIPSE=%s\n' %value
                elif 'QUADRILATERL' in key:
                    line = 'UNTRUSTED_QUADRILATERAL=%s\n' %value
            else:
                line = "%s=%s\n" % (key, value)
            xds_input.append(line)

    	# If the detector is tilted in 2theta, adjust the value of
    	# DIRECTION_OF_DETECTOR_Y-AXIS.
    	# **** IMPORTANT ****
    	# This adjustment assumes that the 2theta tilt affects only
    	# the DIRECTION_OF_DETECTOR_Y-AXIS, and not the
    	# DIRECTION_OF_DETECTOR_X-AXIS.
    	#
    	# If 2theta is not inclined, self.image_data should not have the key
    	# 'twotheta', or have that key set to a value of None.
    	#
    	# If 2theta is inclined, it should be give in self.image_data
    	# with the key 'twotheta' and a value in degrees.
    	#
    	if 'twotheta' in self.image_data and self.image_data['twotheta'] != None:
    	    twotheta = math.radians(float(self.image_data['twotheta']))
    	    tilty = math.cos(twotheta)
    	    tiltz = math.sin(twotheta)
    	    xds_input.append('!***** Detector is tilted in 2theta *****\n')
    	    xds_input.append('! 2THETA = %s degrees\n' % self.image_data['twotheta'])
    	    xds_input.append('!*** Resetting DIRECTION_OF_DETECTOR_Y-AXIS ***\n')
    	    xds_input.append('DIRECTION_OF_DETECTOR_Y-AXIS= 0.0 %.4f %.4f\n' %(tilty, tiltz))
    	    xds_input.append('! 0.0 cos(2theta) sin(2theta)\n\n')

        # pprint(xds_input)
        # sys.exit()

    	return(xds_input)

    def set_detector_data (self, detector_type):
        """
        This function returns a list of strings that constitute the default
        parameters needed to create an XDS.INP file.

        new detector types can be added by following the format of preexisting
        detector types.

        Current detector types are:
        ADSC - unbinned ADSC Q315 as at NE-CAT
        ADSC_binned - binned ADSC Q315 as at NE-CAT
        PILATUS - Pilatus 6M
        HF4M - ADSC HF4M
        MX300hs - SER-CAT's Rayonix MX300hs
        """
        self.logger.debug('FastIntegration::set_detector_type')
        last_frame = int(self.image_data['start']) + int(self.image_data['total']) -1
        self.logger.debug('last_frame = %s' % last_frame)
        self.logger.debug('detector_type = %s' % detector_type)
        background_range = '%s %s' %(int(self.image_data['start']), int(self.image_data['start']) + 4)

        # Detector specific paramters.
        # ADSC unbinned.
        if detector_type == 'ADSC':
            x_beam = float(self.image_data['y_beam']) / 0.0513
            y_beam = float(self.image_data['x_beam']) / 0.0513
            if x_beam < 0 or x_beam > 6144:
                raise RuntimeError, 'x beam coordinate outside detector'
            if y_beam < 0 or y_beam > 6144:
                raise RuntimeError, 'y beam coordinate outside detector'
            if 'image_template' in self.image_data:
                self.image_template = self.image_data['image_template']
            else:
                #self.image_template = '%s_%s_???.img' %(self.image_data['image_prefix'],FM
                if 'prefix' in self.image_data:
                    self.image_template = '%s_%s_???.img' %(self.image_data['prefix'],
                                               self.image_data['run_number'])
                else:
                    self.image_template = '%s_%s_???.img' %(self.image_data['image_prefix'], self.image_data['run_number'])
            file_template = os.path.join(self.image_data['directory'], self.image_template)
            self.last_image = file_template.replace('???','%03d' %last_frame)
            self.first_image = file_template.replace('???','%03d' %int(self.image_data['start']))

            if self.ram_use == True:
                file_template = os.path.join('/dev/shm/',
                                             self.image_data['prefix'],
                                             self.image_template)
            if self.image_data.has_key('pixel_size'):
            	pass
            else:
            	self.image_data['pixel_size'] = '0.0513'
            # Set untrusted region for this detector on NE-CAT 24ID-E
            untrusted_region = 'UNTRUSTED_RECTANGLE= 0 1040 3080 4090\n\n'

        #ADSC binned.
        elif detector_type == 'ADSC_binned':
            detector_type = 'ADSC'
            x_beam = float(self.image_data['y_beam']) / 0.10259
            y_beam = float(self.image_data['x_beam']) / 0.10259
            if x_beam < 0 or x_beam > 3072:
                raise RuntimeError, 'x beam coordinate outside detector'
            if y_beam < 0 or y_beam > 3072:
                raise RuntimeError, 'y beam coordinate outside detector'
            if 'image_template' in self.image_data:
                self.image_template = self.image_data['image_template']
            else:
                if 'prefix' in self.image_data:
                    self.image_template = '%s_%s_???.img' %(self.image_data['prefix'],
                                               self.image_data['run_number'])
                else:
                    self.image_template = '%s_%s_???.img' %(self.image_data['image_prefix'], self.image_data['run_number'])
            file_template = os.path.join(self.image_data['directory'],self.image_template)
            self.last_image = file_template.replace('???','%03d' %last_frame)
            self.first_image = file_template.replace('???','%03d' %int(self.image_data['start']))
            if self.ram_use == True:
                file_template = os.path.join('/dev/shm/',
                                             self.image_data['prefix'],
                                             self.image_template)
            if self.image_data.has_key('pixel_size'):
            	pass
            else:
            	self.image_data['pixel_size'] = '0.10259'
            # Set untrusted region for this detector at NE-CAT 24ID-E.
            untrusted_region = 'UNTRUSTED_RECTANGLE= 0 520 1540 2045\n\n'
        if detector_type == 'ADSC':
         	min_pixel_value = '1'

        # ADSC HF-4M
        elif detector_type == 'HF4M':
            x_beam = float(self.image_data['y_beam']) / 0.150
            y_beam = float(self.image_data['x_beam']) / 0.150
            if x_beam < 0 or x_beam > 2100:
                raise RuntimeError, 'x beam coordinate outside of detector'
            if y_beam < 0 or y_beam > 2290:
                raise RuntimeError, 'y beam coordinate outside of detector'
            detector_file = 'XDS-HF4M.INP'
            if 'image_template' in self.image_data:
                self.image_template = self.image_data['image_template']
            else:
                self.image_template = '%s_%s_????.cbf' %(self.image_data['image_prefix'], self.image_data['run_number'])
            file_template = os.path.join(self.image_data['directory'],self.image_template)
            self.last_image = file_template.replace('????','%04d' %last_frame)
            self.first_image = file_template.replace('????','%04d' %int(self.image_data['start']))
            if self.ram_use == True:
                file_template = os.path.join('/dev/shm/', self.image_data['image_prefix'], self.image_template)

        # Pilatus 6M.
        elif detector_type == 'PILATUS':
            x_beam = float(self.image_data['y_beam']) / 0.172
            y_beam = float(self.image_data['x_beam']) / 0.172
            if x_beam < 0 or x_beam > 2463:
                raise RuntimeError, 'x beam coordinate outside detector'
            if y_beam < 0 or y_beam > 2527:
                raise RuntimeError, 'y beam coordinate outside detector'
            if 'image_template' in self.image_data:
                self.image_template = self.image_data['image_template']
            else:
                self.image_template = '%s_%s_????.cbf' %(self.image_data['image_prefix'],
                                                     self.image_data['run_number'])
            file_template = os.path.join(self.image_data['directory'],self.image_template)
            self.last_image = file_template.replace('????','%04d' %last_frame)
            self.first_image = file_template.replace('????','%04d' %int(self.image_data['start']))
            if self.ram_use == True:
                file_template = os.path.join('/dev/shm/',
                                             self.image_data['image_prefix'],
                                             self.image_template)
            if self.image_data.has_key('pixel_size'):
            	pass
            else:
            	self.image_data['pixel_size'] = '0.172'
            # Set untrusted region for this detector on NE-CAT 24ID-C
            # The Pilatus has a lot of regions untrusted between modules.
            untrusted_region=''
            rectangles = ['487 495 0 2527']
            rectangles.extend('981 989 0 2527')
            rectangles.extend('1475 1483 0 2527')
            rectangles.extend('1969 1977 0 2527')
            rectangles.extend('0 2463 195 213')
            rectangles.extend('0 2463 407 425')
            rectangles.extend('0 2463 619 637')
            rectangles.extend('0 2463 831 849')
            rectangles.extend('0 2463 1043 1061')
            rectangles.extend('0 2463 1255 1273')
            rectangles.extend('0 2463 1467 1485')
            rectangles.extend('0 2463 1679 1697')
            rectangles.extend('0 2463 1891 1909')
            rectangles.extend('0 2463 2103 2121')
            rectangles.extend('0 2463 2315 2333')
            for rectangle in rectangles:
            	untrusted_region += 'UNTRUSTED_RECTANGLE= %s\n' %rectangle
            untrusted_region +='\n'
            # We also use non-default values for SEPMIN and CLUSTER_RADIUS for the Pilatus, so add those.
            untrusted_region +='SEPMIN=4 ! Default is 6 for other detectors.\n'
            untrusted_region +='CLUSTER_RADIUS=2 ! Defaults is 3 for other detectors.\n'
            untrusted_region +='SENSOR_THICKNESS=0.32\n\n'
            min_pixel_value = '0'

        # Rayonix 300hs.
        elif detector_type == 'rayonix_mx300hs':
            detector_type = 'MAR345'
            x_beam = float(self.image_data['x_beam']) / float(self.image_data['pixel_size'])
            y_beam = float(self.image_data['y_beam']) / float(self.image_data['pixel_size'])
            if x_beam < 0 or x_beam > int(self.image_data['size1']):
            	raise RuntimeError, 'x beam coordinate outside detector'
            if y_beam < 0 or y_beam > int(self.image_data['size1']):
            	raise RuntimeError, 'y beam coordinate outside detector'
            detector_file = 'XDS-MX300HS.INP'
            if 'image_template' in self.image_data:
            	self.image_template = self.image_data['image_template']
            else:
            	self.image_template = '%s.????' %self.image_data['image_prefix']
            file_template = os.path.join(self.image_data['directory'],self.image_template)
            self.last_image = file_template.replace('????', '%04d' %last_frame)
            self.first_iamge = file_template.replace('????', '%04d' %int(self.image_data['start']))
            # Set untrusted region for this detector on SER-CAT beamline
            untrusted_region = ''
            min_pixel_value = '0'

        self.logger.debug('	Last Image = %s' % self.last_image)
        # Begin xds input with parameters determined by data set.
        xds_input = ['!============ DATA SET DEPENDENT PARAMETERS====================\n',
                     'ORGX=%.2f ORGY=%.2f !Beam center (pixels)\n' %(x_beam, y_beam),
                     'DETECTOR_DISTANCE=%.2f !(mm)\n' %float(self.image_data['distance']),
                     'OSCILLATION_RANGE=%.2f !(degrees)\n' %float(self.image_data['osc_range']),
                     'X-RAY_WAVELENGTH=%.5f !(Angstroems)\n' %float(self.image_data['wavelength']),
                     '\n',
                     'NAME_TEMPLATE_OF_DATA_FRAMES=%s\n' %file_template,
                     '\n',
                     'BACKGROUND_RANGE=%s\n\n' % background_range,
                     '!=============== DETECTOR PARAMETERS ========================\n',
                     'DETECTOR=%s MINIMUM_VALID_PIXEL_VALUE=%s OVERLOAD=%s\n' %(
                     	     detector_type, min_pixel_value,self.image_data['count_cutoff']),
                     'NX=%s NY=%s QX=%s QY=%s\n' %(
                     	     self.image_data['size1'],self.image_data['size2'],self.image_data['pixel_size'],self.image_data['pixel_size']),
                     'TRUSTED_REGION=0.0 1.0 !Relative radii limiting trusted detector region\n\n',
                     'ROTATION_AXIS=1.0 0.0 0.0\n',
                     'INCIDENT_BEAM_DIRECTION=0.0 0.0 1.0\n',
                     'FRACTION_OF_POLARIZATION=0.90 !default =0.5 for unpolarized beam\n',
                     'POLARIZATION_PLANE_NORMAL= 0.0 1.0 0.0\n',
                     "FRIEDEL'S_LAW=FALSE !Defaults is TRUE\n\n",
                     'INCLUDE_RESOLUTION_RANGE=200.0 0.0 !Angstroems\n',
                     'REFINE(IDXREF)=BEAM AXIS ORIENTATION CELL POSITION\n',
                     'REFINE(INTEGRATE)=BEAM CELL ORIENTATION POSITION\n',
                     'REFINE(CORRECT)=BEAM AXIS CELL ORIENTATION POSITION\n',
                     'STRICT_ABSORPTION_CORRECTION=TRUE\n\n',
                     'DIRECTION_OF_DETECTOR_X-AXIS=1.0 0.0 0.0\n']
        # If detector is tilted in two-theta, adjust DIRECTION_OF_Y-AXIS
        if self.image_data['twotheta'] == 0.0 or self.image_data['twotheta'] == None:
            xds_input.append('DIRECTION_OF_DETECTOR_Y-AXIS=0.0 1.0 0.0\n\n')
        else:
            twotheta = math.radians(float(self.image_data['twotheta']))
            tilty = math.cos(twotheta)
            tiltz = math.sin(twotheta)
            xds_input.append('!******  Detector is inclined ****\n')
            xds_input.append('! TWO_THETA = %s\n' % self.image_data['twotheta'])
            xds_input.append('!***   Reset DIRECTION_OF_DETECTOR_Y-AXIS ***')
            xds_input.append('DIRECTION_OF_DETECTOR_Y-AXIS=0.0 %.4f %.4f\n' %(tilty, tiltz))
            xds_input.append('!0.0 cos(2theta) sin(2theta)\n\n')
        xds_input.append(untrusted_region)

        return(xds_input)


    def write_file (self, filename, file_input):
        """
        Writes out file_input as filename.
        file_input should be a list containing the desired contents
        of the file to be written.
        """
        self.logger.debug('FastIntegration::write_file')
        self.logger.debug('    Filename = %s' % filename )
        # pprint(file_input)
        with open (filename, 'w') as file:
            file.writelines(file_input)
        return()

    def find_spot_range (self, first, last, osc, input):
        """
        Finds up to two spot ranges for peak picking.
        Ideally the two ranges each cover 5 degrees of data and
        are 90 degrees apart.  If the data set is 10 degrees or
        less, return a single spot range equal to the entire data
        set. If the data set is less than 90 degrees, return two
        spot ranges representing the first 5 degrees and the middle
        5 degrees of data.
        """
        self.logger.debug('FastIntegration::find_spot_range')
        self.logger.debug('     first_frame = %s' % first)
        self.logger.debug('     last_frame = %s' % last)
        self.logger.debug('     frame_width = %s' % osc)

        # Determine full oscillation range of the data set.
        fullrange = (float(last) - float(first) + 1) * float(osc)
        # If the full oscillation range is 10 degrees or less
        # return a single spot_range equal to the full data set
        if fullrange <= 10:
            input.append('SPOT_RANGE=%s %s\n\n' %(first, last))
        else:
            endspot1 = int(first) + int(5 / float(osc)) - 1
            input.append('SPOT_RANGE=%s %s\n\n' %(first, endspot1))
            if fullrange < 95:
                spot2_start = int( (int(last) - int(first) + 1) / 2)
            else:
                spot2_start = int(90 / float(osc))
            spot2_end = spot2_start + int(5 / float(osc)) - 1
            input.append('SPOT_RANGE=%s %s\n\n' %(spot2_start, spot2_end))
        return(input)

    def xds_run (self, directory):
        """
        Launches the running of xds.
        """
        self.logger.debug('FastIntegration::xds_run')
        self.logger.debug('     directory = %s', directory)
        self.logger.debug('     detector = %s', self.image_data['detector'])

        # if self.image_data['detector']=='rayonix_mx300hs':
        #     xds_command = '/usr/local/XDS-INTEL64_Linux_x86_64/xds_par'
        # else:
        xds_command = 'xds_par'

        os.chdir(directory)
        # TODO skip processing for now
        if self.cluster_use == True:
            job = Process(target=BLspec.processCluster,args=(self,(xds_command,'XDS.LOG','8','phase2.q')))
        else:
            job = Process(target=Utils.processLocal,
                          args=((xds_command, "XDS.LOG"),
                          self.logger))
        job.start()
        while job.is_alive():
            time.sleep(1)
            self.tprint(arg=".", level=99, color="white", newline=False)
        self.tprint(arg=" done", level=99, color="white")
        os.chdir(self.dirs['work'])

        return()

    def xds_ram (self, first_node):
        """
        Launches xds_par via ssh on the first_node.
        This ensures that xds runs properly when trying to use
        data distributed to the cluster's ramdisks
        """
        self.logger.debug('FastIntegration::xds_ram')
        command = ('ssh -x %s "cd $PWD && xds_par > XDS.LOG"' % first_node)
        self.logger.debug('		%s' % command)
        p = subprocess.Popen(command, shell=True)
        sts = os.waitpid(p.pid, 0)[1]

        return()

    def find_correct_res(self, directory, isigi):
        """
        Looks at CORRECT.LP to find a resolution cutoff, where I/sigma is
        approximately 1.5
        """
        self.logger.debug('     directory = %s' % directory)
        self.logger.debug('     isigi = %s' % isigi)
        self.tprint(arg="  Determining resolution cutoff ",
                    level=99,
                    color="white",
                    newline=False)

        new_hi_res = False
        correctlp = os.path.join(directory,'CORRECT.LP')
        try:
            correct_log = open(correctlp, 'r').readlines()
        except IOError as e:
            self.logger.debug('Could not open CORRECT.LP')
            self.logger.debug(e)
            return(new_hi_res)

        flag = 0
        IsigI = 0
        hires = 0

        # Read from the bottom of CORRECT.LP up, looking for the first
        # occurence of "total", which signals that you've found the
        # last statistic table given giving I/sigma values in the file.
        for i in range (len(correct_log)-1, 0, -1):
            if correct_log[i].strip().startswith('total'):
                flag = 1
            elif flag == 1:
                if len(correct_log[i]) == 1:
                    new_hi_res = hires
                    break
                line = correct_log[i].split()
                if line[0][0].isdigit():
                    #if line[8] == '-99.00':
                    #    self.logger.debug('    IsigI = -99.00')
                    #    return(False)
                    prev_hires = hires
                    prev_IsigI = IsigI
                    hires = float(line[0])
                    try:
                        IsigI = float(line[8])
                    except ValueError:
                        pass
                    #self.logger.debug('		hires = %s, IsigI = %s' %(hires, IsigI))
                    if IsigI >= isigi:
                        # If the first IsigI value greater than 2, break and
                        # return False as new_hires.
                        if prev_IsigI == 0:
                            break
                        else:
                            new_hi_res = '%0.2f' % numpy.interp([isigi],
                                                                [prev_IsigI, IsigI],
                                                                [prev_hires, hires])
                            # print [isigi]
                            # print [prev_IsigI, IsigI]
                            # print [prev_hires, hires]
                            # print interp([isigi], [prev_IsigI, IsigI], [prev_hires, hires])
                            break
                else: # If first character in line is not a digit, you;ve
                    # read through the entire table, so break.
                    new_hi_res = hires
                    break
        self.logger.debug('     prev_hires = %s     prev_IsigI = %s' % (prev_hires, prev_IsigI))
        self.logger.debug('     hires = %s          IsigI = %s' %(hires, IsigI))
        self.logger.debug('	New cutoff = %s' %new_hi_res)
        hi_res = float(new_hi_res)

        self.tprint(arg="new cutoff = %4.2f" % hi_res,
                    level=99,
                    color="white")

        return hi_res

    def check_for_xds_errors(self, dir, input):
        """
        Examines results of an XDS run and searches for known problems.
        """
        self.logger.debug('FastIntegration::check_for_xds_errors')
        self.tprint(arg="  Checking XDS output for errors",
                    level=99,
                    color="white")

        os.chdir(dir)
        # Enter a loop that looks for an error, then tries to correct it
        # and the reruns xds.
        # Loop should continue until all errors are corrected, or only
        # an unknown error is detected.
        xdslog = open('XDS.LOG','r').readlines()
        for line in xdslog:
            if '! ERROR !' in line:
                # An error was found in XDS.LOG, now figure out what it was.
                if 'CANNOT CONTINUE WITH A TWO DIMENSION' in line:
                    self.logger.debug('    Found an indexing error')
                    self.tprint(arg="\n  Found an indexing error",
                                level=10,
                                color="red")

                    # Try to fix by extending the data range
                    tmp = input[-1].split('=')
                    first,last = tmp.split()
                    if int(last) == (int(self.image_data('start')) + int(self.image_data('total')) -1):
                        self.logger.debug('         FAILURE: Already using the full data range available.')
                        return(False)
                    else:
                        input[-1] = 'SPOT_RANGE=%s %s' %(first, (int(last) + 1))
                        self.write_file('XDS.INP', input)
                        os.system('mv XDS.LOG initialXDS.LOG')
                        self.tprint(arg="\n  Extending spot range",
                                    level=10,
                                    color="white",
                                    newline=False)
                        self.xds_run(dir)
                        return(input)
                elif 'SOLUTION IS INACCURATE' in line or 'INSUFFICIENT PERCENTAGE' in line:
                    self.logger.debug('    Found inaccurate indexing solution error')
                    self.logger.debug('    Will try to continue anyway')
                    self.tprint(arg="  Found inaccurate indexing solution error - trying to continue anyway",
                                level=30,
                                color="red")

                    # Inaccurate indexing solution, can try to continue with DEFPIX,
                    # INTEGRATE, and CORRECT anyway
                    self.logger.debug(' The length of input is %s' % len(input))
                    if 'JOB=DEFPIX' in input[-2]:
                        self.logger.debug('Error = %s' %line)
                        self.logger.debug('XDS failed to run with inaccurate indexing solution error.')
                        self.tprint(arg="\n  XDS failed to run with inaccurate indexing solution error.",
                                    level=30,
                                    color="red")
                        return(False)
                    else:
                        input[-2] = ('JOB=DEFPIX INTEGRATE CORRECT !XYCORR INIT COLSPOT'
                                 + ' IDXREF DEFPIX INTEGRATE CORRECT\n')
                        self.write_file('XDS.INP', input)
                        os.system('mv XDS.LOG initialXDS.LOG')
                        self.tprint(arg="\n  Integrating with suboptimal indexing solution",
                                    level=99,
                                    color="white",
                                    newline=False)
                        self.xds_run(dir)
                        return(input)
                elif 'SPOT SIZE PARAMETERS HAS FAILED' in line:
                    self.logger.debug('	Found failure in determining spot size parameters.')
                    self.logger.debug('	Will use default values for REFLECTING_RANGE and BEAM_DIVERGENCE.')
                    self.tprint(arg="\n  Found failure in determining spot size parameters.",
                                level=99,
                                color="red")

                    input.append('\nREFLECTING_RANGE=1.0 REFLECTING_RANGE_E.S.D.=0.10\n')
                    input.append('BEAM_DIVERGENCE=0.9 BEAM_DIVERGENCE_E.S.D.=0.09\n')
                    self.write_file('XDS.INP', input)
                    os.system('mv XDS.LOG initialXDS.LOG')
                    self.tprint(arg="  Integrating after failure in determining spot size parameters",
                                level=99,
                                color="white",
                                newline=False)
                    self.xds_run(dir)
                    return(input)
                else:
                    # Unanticipated Error, fail the error check by returning False.
                    self.logger.debug('Error = %s' %line)
                    return(False)
        return(input)

    def write_forkscripts (self, node_list, osc):
        """
        Creates two small script files that are run in place of
        XDS's forkcolspot and forkintegrate scripts to allow
        utilization of data distributed on the cluster's ramdisks.

        In order for the forkscripts to work, the forkcolspot and
        forkintegrate scripts in the xds directory should be modified
        appropriately.
        """
        self.logger.debug('FastIntegration::write_forkscripts')

        niba0 = 5 // float(osc) # minimum number of images per batch
        ntask = len(node_list[0]) # Total number of jobs
        nodes = node_list[0] # list of nodes where data is distributed
        fframes = node_list[1] # list of first image on each node
        lframes = node_list[2] # list of last image on each node

        forkc = ['#!/bin/bash\n']
        forkc.append('echo "1" | ssh -x %s "cd $PWD && mcolspot_par" &\n'
                     % nodes[0])
        forkc.append('echo "2" | ssh -x %s "cd $PWD && mcolspot_par" &\n'
                     % nodes[-1])
        forkc.append('wait\n')
        forkc.append('rm -f mcolspot.tmp')

        forki = ['#!/bin/bash\n']
        for x in range (0, ntask, 1):
            itask = x + 1
            nitask = lframes[x] - fframes[x] + 1
            if nitask < niba0:
                nbatask = 1
            else:
                nbatask = nitask // niba0
            forki.append('echo "%s %s %s %s" | ssh -x %s "cd $PWD && mintegrate_par" &\n'
                         % (fframes[x], nitask, itask, nbatask, nodes[x]))
        forki.append('wait\n')
        forki.append('rm -f mintegrate.tmp')

        self.write_file('forkc', forkc)
        self.write_file('forki', forki)
        os.chmod('forkc', stat.S_IRWXU)
        os.chmod('forki', stat.S_IRWXU)
        return()

    def run_results (self, directory):
        """
        Takes the results from xds integration/scaling and prepares
        tables and plots for the user interface.
        """
        self.logger.debug('FastIntegration::run_results')
        os.chdir(directory)

        orig_rescut = False

        # Run xdsstat on XDS_ASCII.HKL.
        xdsstat_log = self.xdsstat()

        # Run pointless to convert XDS_ASCII.HKL to mtz format.
        mtzfile = self.pointless()

        # Run dummy run of aimless to generate various stats and plots.
        # i.e. We don't use aimless for actual scaling, it's already done by XDS.
        if mtzfile != 'Failed':
            aimless_log = self.aimless(mtzfile)
        else:
            self.logger.debug('    Pointless did not run properly!')
            self.logger.debug('    Please check logs and files in %s' %self.dirs['work'])
            return('Failed')

        # Parse the aimless logfile to look for resolution cutoff.
        aimlog = open(aimless_log, "r").readlines()
        for line in aimlog:
            if 'High resolution limit' in line:
                current_resolution = line.split()[-1]
            elif 'from half-dataset correlation' in line:
                resline = line
            elif 'from Mn(I/sd) >  1.50' in line:
                resline2 = line
                break
        res_cut = resline.split('=')[1].split('A')[0].strip()
        res_cut2 = resline2.split('=')[1].split('A')[0].strip()
        if float(res_cut2) < float(res_cut):
            res_cut = res_cut2

        # Run aimless with a higher resolution cutoff if the suggested resolution
        # is greater than the initial resolution + 0.05.
        if (float(res_cut) > float(current_resolution) + 0.05):
            # Save information on original resolution suggestions
            orig_rescut = resline
            # rerun aimless
            aimless_log = self.aimless(mtzfile, res_cut)

        #graphs, tables, summary = self.parse_aimless(aimless_log)
        graphs, summary =self.parse_aimless2(aimless_log)

        wedge = directory.split('_')[-2:]
        summary['wedge'] = '-'.join(wedge)

        # Parse INTEGRATE.LP and add information about mosaicity to summary.
        summary['mosaicity'] = float(self.parse_integrateLP())

        # Parse CORRECT.LP and add information from that to summary.
        summary['ISa'] = self.parse_correctLP()

        # Parse CORRECT.LP and pull out per wedge statistics
        #self.parse_correct()

        #scalamtz = mtzfile.replace('pointless','scala')
        #scalalog = scalamtz.replace('mtz','log')
        scalamtz = mtzfile.replace('pointless', 'aimless')
        scalalog = scalamtz.replace('mtz', 'log')
        # generate web files for results display in the UI
        #plotsHTML = self.make_plots(graphs, tables)
        # shortHTML = self.make_short_results(directory, summary, orig_rescut)
        # longHTML = self.make_long_results(scalalog)

        # shutil.copyfile(plotsHTML, os.path.join(self.dirs['work'], plotsHTML))
        # shutil.copyfile(shortHTML, os.path.join(self.dirs['work'], shortHTML))
        # shutil.copyfile(longHTML, os.path.join(self.dirs['work'], longHTML))

        results = {'status'   : 'WORKING',
                   'plots'    : graphs,
                #    'short'    : shortHTML,
                #    'long'     : longHTML,
                   'summary'  : summary,
                   'mtzfile'  : scalamtz,
                   'dir'      : directory
                   }
        self.logger.debug("Returning results!")
        self.logger.debug(results)

         # Set up the results for return
        self.results['process'] = {
        	'agent_process_id':self.process_id,
        	'status':50
            }
        self.results['results'] = results
        self.logger.debug(self.results)

        # self.sendBack2(tmp)
        if self.controller_address:
            rapd_send(self.controller_address, self.results)

        return results

    def make_long_results(self, logfile):
        """
        Grab the contents of various logfiles generated by data processing,
        and put them in a php file.
        """
        self.logger.debug('FastIntegration:make_long_results')

        file = ['<?php\n//prevents caching\n',
                'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n',
                'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n',
                'header("Cache-Control: post-check=0, pre-check=0",false);\n\n',
                'session_cache_limiter();\n',
                'session_start();\n\n',
                "require('/var/www/html/rapd/login/config.php');\n",
                "require('/var/www/html/rapd/login/functions.php');\n\n",
                'if(allow_user() != "yes")\n{\n',
                '    if(allow_local_data($_SESSION[data]) != "yes")\n    {\n',
                "        include ('/login/no_access.html');\n",
                '        exit();\n\n    }\n} else {\n    $local = 0;\n}\n?>\n',
                '<head>\n    <!-- Inline Stylesheet -->\n',
                '    <style type="text/css" media="screen"><!--\n',
                '    body {\n        background-image: none;\n        font-size: 17px;\n',
                '        }\n    table.display td {padding: 1px 7px;}\n',
                '    tr.GradeD {font-weight: bold;}\n',
                '    table.integrate td, th {border-style: solid;\n',
                '        border-width: 2px;\n',
                '        border-spacing: 0;\n',
                '        border-color: gray;\n',
                '        padding: 5px;\n',
                '        text-align: center;\n',
                '        height: 2r10px;\n',
                '        font-size: 15px; }\n',
                '    table.integrate tr.alt {background-color: #EAF2D3; }\n',
                '--></style>\n',
                '<!--<script type="text/javascript" language="javascript"',
                ' src="../js/dataTables-1.5/media/js/jquery.js"></script>-->\n',
                '    <script type="text/javascript" charset="utf-8">\n',
                '    $(document).ready(function(){\n',
                "    $('.accordion').accordion({\n",
                '    collapsible: true,\n',
                '    autoHeight: false,\n',
                '    active: 0          });\n',
                "    $('#cell').dataTable({\n",
                '    "bPaginate": false,\n',
                '    "bFilter": false,\n',
                '    "bInfo": false,\n',
                '    "bSort": false,\n',
                '    "bAutoWidth": false    });\n',
                "    $('#pdb1').dataTable({\n",
                '    "bPaginate": false,\n',
                '    "bFilter": false,\n',
                '    "bInfo": false,\n',
                '    "bSort": false,\n',
                '    "bAutoWidth": false    });;\n',
                '        } );\n    </script>\n</head>\n<body>\n',
                '<div class="accordion">\n',
                '<h3><a href="#">Click to view Pointless log file.</a></h3>\n',
                '<div>\n<pre>\n==========    pointless    ==========\n'
                ]
        pointless_log = logfile.replace('aimless','pointless')
        in_lines = open(pointless_log, 'r').readlines()
        for in_line in in_lines:
            if '&' in in_line:
                in_line = in_line.replace('&',"&amp")
            if '<I' in in_line:
                in_line = in_line.replace('<','&lt')
                in_line = in_line.replace('>','&gt')
            file.append(in_line)
        file.extend(['</pre>\n</div>\n',
                     '<h3><a href="#">Click to view Aimless log file.</a></h3>\n',
                     '<div>\n<pre>\n==========    aimless    ==========\n'
                     ])
        in_lines = open(logfile, 'r').readlines()
        for in_line in in_lines:
            if 'applet' in in_line or in_line.startswith('codebase'):
                pass
            else:
                if '&' in in_line:
                    in_line = in_line.replace('&','&amp')
                if '<I' in in_line:
                    in_line = in_line.replace('<','&lt')
                    in_line = in_line.replace('>','&gt')
                file.append(in_line)
        file.extend(['</pre>\n</div>\n',
                     '<h3><a href="#">Click to view INTEGRATE.LP.</a></h3>\n',
                     '<div>\n<pre>\n==========    INTEGRATE.LP    ==========\n'
                     ])
        in_lines = open('INTEGRATE.LP', 'r').readlines()
        for in_line in in_lines:
            if '<I' in in_line:
                in_line = in_line.replace('<','&lt')
                in_line = in_line.replace('>','&gt')
            file.append(in_line)
        file.extend(['</pre>\n</div>\n',
                     '<h3><a href="#">Click to view CORRECT.LP.</a></h3>\n',
                     '<div>\n<pre>\n==========   CORRECT.LP    ==========\n'
                     ])
        in_lines = open('CORRECT.LP', 'r').readlines()
        for in_line in in_lines:
            #if '&' in in_line:
            #    in_line.replace('&','&amp')
            if '<I' in in_line:
                in_line = in_line.replace('<','&lt')
                in_line = in_line.replace('>','&gt')
            file.append(in_line)
        file.append('</pre>\n</div>\n</div>\n</body>')

        self.write_file('long_results.php',file)
        return('long_results.php')

    def make_short_results(self, directory, results, orig_rescut=False):
        """
        Parses the aimless logfile and extracts the summary table
        at the end of the file.  Then writes an html file to be
        displayed as the Summary of the data processing.
        """
        self.logger.debug('FastIntegration::make_short_results')
        if 'ID' in self.image_data.keys():
            pass
        else:
            self.image_data['ID'] = self.image_data['image_prefix']
        parsed = ['<?php\n',
                  '//prevents caching\n',
                  'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n',
                  'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n',
                  'header("Cache-Control: post-check=0, pre-check=0",false);\n\n',
                  'session_cache_limiter();\n',
                  'session_start();\n\n',
                  "require('/var/www/html/rapd/login/config.php');\n",
                  "require('/var/www/html/rapd/login/functions.php');\n\n",
                  'if(allow_user() != "yes")\n{\n',
                  '    if(allow_local_data($_SESSION[data]) != "yes")\n    {\n',
                  "        include ('/login/no_access.html');\n",
                  '        exit();\n    }\n} else {\n    $local = 0;\n}\n?>\n',
                  '<head>\n<!-- Inline Stylesheet -->\n<style type="text/css"><!--\n',
                  '    body {font-size: 17px; }\n',
                  '    table.integrate td, th {border-style: solid;\n',
                  '            border-width: 2px;\n',
                  '            border-spacing: 0;\n',
                  '            border-color: gray;\n',
                  '            padding: 5px;\n',
                  '            text-align: center;\n',
                  '            height: 2r10px;\n',
                  '            font-size: 15px; }\n',
                  '    table.integrate tr.alt {background-color: #EAF2D3; }\n',
                  '--></style>\n</head>\n<body>\n<div id="container">\n',
                  '<div align="center">\n',
                  '<h3 class="green">Processing Results for %s</h3>\n'
                  % self.image_data['ID'],
                  '<h3 class="green">Images %s' % results['wedge'],
                  '<h2>Spacegroup: %s</h2>\n' % results['scaling_spacegroup'],
                  '<h2>Unit Cell: %s</h2>\n' % (' '.join(results['scaling_unit_cell'])),
                  '<h2>SIGMAR (Mosaicity): %s&deg</h2>\n' % results['mosaicity'],
                  '<h2>Asymptotic limit of I/sigma (ISa) = %s</h2>\n' % results['ISa'],
                  '<table class="integrate">\n',
                  '<tr><th></th><td>Overall</td><td>Inner Shell</td><td>Outer Shell</td></tr>\n'
                  ]
        pairs1 = [('High resolution limit','bins_high'),
                      ('Low resolution limit','bins_low'),
                      ('Completeness','completeness'),
                      ('Multiplicity','multiplicity'),
                      ('I/sigma','isigi'),
                      ('CC(1/2)', 'cc-half'),
                      ('Rmerge','rmerge_norm'),
                      ('Rmerge (anomalous)', 'rmerge_anom'),
                      ('Rmeas','rmeas_norm'),
                      ('Rmeas (anomalous)','rmeas_anom'),
                      ('Rpim','rpim_norm'),
                      ('Rpim (anomalous)','rpim_anom'),
                      #('Partial bias','bias'),
                      ('Anomalous completeness','anom_completeness'),
                      ('Anomalous multiplicity','anom_multiplicity'),
                      ('Anomalous correlation','anom_correlation'),
                      ('Anomalous slope','anom_slope'),
                      ('Total observations','total_obs'),
                      ('Total unique','unique_obs')]
        count = 0
        for l,k in pairs1:
            if (count % 2 == 0):
                line = '<tr><th>%s</th>' % l
            else:
                line = '<tr class="alt"><th>%s</th>' % l
            for v in results[k]:
                line += '<td>%s</td>' % v.strip()
            if l == 'Anomalous slope':
                line += '<td>--</td><td>--</td>'
            line += '</tr>\n'
            parsed.append(line)
            count += 1
        parsed.append('</table>\n</div><br>\n')

        #slope = float(results['anom_slope'][0])
        #flag = False
        #parsed.extend(['<div align="left>\n',
        #               '<h3 class ="green">Analysis for anomalous signal.</h3>\n',
        #               '<pre>An anomalous slope > 1 may indicate the presence of anomalous signal.\n',
        #               'This data set has an anomalous slope of %s.\n' % results['anom_slope'][0],
        #               ])
        #if slope > 1.1:
        #    parsed.append('Analysis of this data set by anomalous slope indicates the presence of a significant anomalous signal.\n')
        #    flag = True
        #elif slope > 1.0:
        #    parsed.append('Analysis of this data set by anomalous slope indicates either weak or no anomalous signal.\n')
        #    flag = True
        #else:
        #    parsed.append('Analysis of this data set by anomalous slope indicates no detectable anomalous signal.\n')
        #if flag == True:
        #    if results['CC_cut'] != False:
        #        parsed.append('\nThe anomalous correlation coefficient suggests the anomalous signal')
        #        parsed.append(' extends to %s Angstroms.\n(cutoff determined where CC_anom is above 0.3)\n'
        #                      % results['CC_cut'][0])
        #    if results['RCR_cut'] != False:
        #        parsed.append('\nThe r.m.s. correlation ratio suggests the anomalous signal')
        #        parsed.append(' extends to %s Angstroms.\n(cutoff determined where RCR_anom is above 1.5)\n\n'
        #                      % results['RCR_cut'][0])
        #    if results['CC_cut'] == False and results['RCR_cut'] == False:
        #        parsed.append('\nA cutoff for the anomalous signal could not be determined')
        #        parsed.append(' based on either the\n anomalous correlation coefficient or')
        #        parsed.append(' by the r.m.s. correlation ratio.\n\n</pre></div><br>\n')

        parsed.append('<p><div align="center"><b>%s</b></p>' % results['text2'])
        parsed.append('<div align="left"><pre>\n\n')
        #parsed.append('At currently defined resolution...\n')
        #for line in results['text']:
        #    parsed.append('    %s' % line)
        #if orig_rescut != False:
        #    parsed.append ('At full detector resolution...\n')
        #    for text in orig_rescut:
        #        parsed.append('    %s' % text)
        #    parsed.append('\n\n')
        parsed.extend(['\n\nRAPD used the following programs for integrating and scaling the dataset:\n',
                       '  XDS - \n',
                       '       "XDS", W. Kabsch (2010) Acta Cryst. D66, 125-132.\n',
                       '       "Integration, scaling, space-group assignment and post-refinement",',
                       ' W. Kabsch (2010) Acta Cryst. D66, 133-144.\n',
                       '  pointless and aimless - \n',
                       '      "Scaling and assessment of data quality", P.R.',
                       ' Evans (2006) Acta Cryst. D62, 72-82.\n',
                       '      "An introduction to data reduction: space-group',
                       ' determination and intensity statistics,',
                       ' P.R. Evans (2011) Acta Cryst. D67, 282-292\n',
                       '      "How good are my data and what is the resolution?"',
                       ' P.R. Evans and G.N. Murshudov (2013) Acta Cryst. D66,',
                       ' 1204-1214.\n',
                       '  truncate, freerflag, and mtz2various  - \n',
                       '       "The CCP4 Suite: Programs for Protein ',
                       'Crystallography". Acta Cryst. D50, 760-763 \n',
                       '  xdsstat - \n      http://strucbio.biologie.',
                       'uni-konstanz.de/xdswiki/index.php/Xdsstat\n',
                       '\n</pre></div></div></body>'
                       ])
        self.write_file('results.php', parsed)
        return('results.php')




    def make_plots(self, graphs, tables):
        """
        Generates the plots html file.

        Keyword arguments
        graphs --
        tables --
        """
        self.logger.debug('FastIntegration::make_plots')
        # plotThese contains a list of graph titles that you want plotted
        # addition plots may be requested by adding the title (stripped of
        # leading and trailing whitespace) to plotThese.
        # The plot titles also serve as keys for the tab titles.
        plotThese = {
                     #'Mn(k) & 0k (theta=0) v. batch'    : 'Scale vs frame',
                     #'Relative Bfactor v. batch'        : 'Bfactor vs frame',
                     'Rmerge v Batch for all runs'      : 'R vs frame',
                     #'Imean & RMS Scatter'              : 'I vs frame',
                     'Imean/RMS scatter'                : 'I/sd vs frame',
                     'I/sigma, Mean Mn(I)/sd(Mn(I))'    : 'I/sigma',
                     'Rmerge v Resolution'              : 'R vs Res',
                     'Rmerge, Rfull, Rmeas, Rpim v Resolution' : 'R vs Res',
                     'Average I,sd and Sigma'           : 'I vs Res',
                     'Average I, RMSdeviation and Sd'   : 'I vs Res',
                     'Completeness v Resolution'        : 'Completeness',
                     'Multiplicity v Resolution'        : 'Redundancy',
                     'Rmeas, Rsym & PCV v Resolution'   : 'Rmeas',
                     'Rpim (precision R) v Resolution'  : 'Rpim',
                     #'Rd vs frame_difference'           : 'Rd',
                     'Anom & Imean CCs v resolution -'  : 'Anom Corr',
                     'Anom & Imean CCs v resolution'    : 'CCanom and CC1/2',
                     'RMS correlation ratio'            : 'RCR',
                     'Rcp v. batch'                     : 'Rcp v batch'
                     }

        plotfile = ['<html>\n',
                    '<head>\n',
                    '  <style type="text/css">\n',
                    '    body     { background-image: none; }\n',
                    '    .x-label { position:relative; text-align:center; top: 10px; }\n',
                    '    .title   { font-size:30px; text-align:center; }\n',
                    '  </style>\n',
                    '  <script type="text/javascript">\n',
                    '$(function() {\n',
                    '              // Tabs\n',
                    "              $('.tabs').tabs();\n",
                    '              });\n',
                    '  </script>\n',
                    '</head>\n',
                    '<body>\n',
                    '    <table>\n',
                    '        <tr>\n',
                    '            <td width="100%">\n',
                    '            <div class="tabs">\n',
                    '                <!-- This is where the tabl labels are defined\n',
                    '                     221 = tab2 (on page) tab2 (full output tab) tab1 -->\n',
                    '                <ul>\n'
                    ]
        # Define tab labels for each graph.
        for i, graph in enumerate(graphs):
            if graph[0] in plotThese:
                title = plotThese[graph[0]]
                plotfile.append('                <li><a href="#tabs-22%s">%s</a></li>\n'
                                % (i, title))
        plotfile.append('                </ul>\n')

        # Define title and x-axis labels for each graph.
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                plotfile.extend(['                <div id="tabs-22%s">\n' % i,
                    '                    <div class="title"><b>%s</b></div>\n'
                    % graph[0],
                    '                    <div id="chart%s_div" style=' % i,
                    '"width:800px; height:600px"></div>\n',
                    '                    <div class="x-label">%s</div>\n'
                    % graph[1],
                    '                </div>\n'
                    ])
        plotfile.extend(['            </div> <!-- End of Tabs -->\n',
                         '            </td>\n',
                         '        </tr>\n',
                         '    </table>\n\n',
                         '<script id="source" language="javascript" type="text/javascript">\n',
                         '$(function () {\n'
                         ])

        # varNames is a counter, such that the variables used for plotting
        # will simply be y+varName (i.e. y0, y1, y2, etc)
        # actual labels are stored transiently in varLabel, and added
        # as comments next to the variable when it is initialized
        varNum = 0
        for i,graph in enumerate(graphs):
            title, xlabel, ylabels, xcol, ycols, tableNum = graph
            if title in plotThese:
                varLabel = []
                data = []
                plotline = '       var '
                # graph[2] is the label for the y-values.
                #ylabels = graph[2]
                for ylabel in ylabels:
                    varLabel.append(ylabel)
                    var = 'y%s' %varNum
                    varNum += 1
                    data.append(var)
                    if ylabel == ylabels[-1]:
                        plotline += ('%s= [];\n' % var)
                    else:
                        plotline += ('%s= [], ' % var)
                plotfile.append(plotline)
                #xcol = int(graph[3])
                #ycols = graph[4]
                #tableNum = graph[5]
                self.logger.debug('table # %s' %tableNum)
                for line in tables[tableNum]:
                    #self.logger.debug('tableNum = %s   line=%s    line[0]=%s' %(tableNum,line, line[0]))
                    if line[0] == '$$':
                        #self.logger.debug("line == '$$' is TRUE")
                        break
                    for y, ycol in enumerate(ycols):
                        #self.logger.debug("ycols == %s" %ycols)
                        if line[ycol] !='-':
                            plotfile.append('        %s.push([%s,%s]);\n'
                                            %(data[y], line[xcol], line[ycol]))
                plotfile.extend(['               var plot%s' % i,
                                 ' = $.plot($("#chart%s_div"), [\n' % i
                                 ])
                for x in range(0, len(data), 1):
                    plotfile.append('               {data:%s, label:"%s" },\n'
                                    % (data[x], varLabel[x]))
                plotfile.extend(['               ],\n',
                                 '               { lines: {show: true},\n',
                                 '                 points: {show: false},\n',
                                 "                 selection: {mode: 'xy' },\n",
                                 '                 grid: {hoverable: true, clickable: true },\n'
                                 ]               )
                if xlabel == 'Dmin (A)':
                    plotfile.append('               xaxis: {ticks: [\n')
                    for line in tables[tableNum]:
                        if line[0] == '$$':
                            break
                        plotfile.append('                              [%s,"%s"],\n'
                                        %(line[xcol], line[xcol+1]))
                    plotfile.append('               ]},\n')
                plotfile.append('               });\n\n')
        plotfile.extend(['function showTooltip(x, y, contents) {\n',
                         "   $('<div id=tooltip>' + contents + '</div>').css( {\n",
                         "            position: 'absolute',\n",
                         "            display: 'none',\n",
                         "            top: y + 5,\n",
                         '            left: x + 5, \n',
                         "            border: '1px solid #fdd',\n",
                         "            padding: '2px',\n",
                         "            'background-color': '#fee',\n",
                         "            opacity: 0.80\n"
                         '        }).appendTo("body").fadeIn(200);\n',
                         '       }\n\n',
                         '    var previousPoint = null;\n'
                         ])
        for i, graph in enumerate(graphs):
            title = graph[0]
            xlabel = graph[1]
            if title in plotThese:
                plotfile.append('    $("#chart%s_div").bind' %str(i) )
                plotfile.extend(['("plothover", function (event, pos, item) {\n',
                                 '    $("#x").text(pos.x.toFixed(2));\n',
                                 '    $("#y").text(pos.y.toFixed(2));\n\n',
                                 'if (true) {\n',
                                 '   if (item) {\n',
                                 '      if (previousPoint != item.datapoint) {\n',
                                 '          previousPoint = item.datapoint;\n\n',
                                 '          $("#tooltip").remove();\n',
                                 ])
                if xlabel == 'Dmin (A)':
                    plotfile.append('            var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),\n')
                else:
                    plotfile.append('            var x = item.datapoint[0].toFixed(2),\n')
                plotfile.extend(['                y = item.datapoint[1].toFixed(2);\n',
                                 '                showTooltip(item.pageX, item.pageY,\n',
                                 '                            item.series.label + " at " + x + " = " + y);\n',
                                 '            }\n',
                                 '        }\n',
                                 '        else {\n',
                                 '               $("#tooltip").remove();\n',
                                 '                 previousPoint = null;\n',
                                 '              }\n',
                                 '    }\n    });\n\n'
                                 ])
        plotfile.append('});\n</script>\n</body>\n</html>\n')
        self.write_file('plot.html', plotfile)
        return('plot.html')

    def parse_aimless (self, logfile):
        """
        Parses the aimless logfile in order to pull out data for graphing
        and the results table.
        Relevant values from teh summary table are stored into a results
        dictionary.
        Returns a list of lists called graphs that contains information on
        data labels and where to pull data from the nested list called tables.
        Returns a nested list called tables, which is a copy of the data
        tables in the aimless logfile.
        Returns a dict called int_results that contains the information
        found in the results summary table of the aimless log file.
        """
        log = smartie.parselog(logfile)
        # The program expect there to be 10 tables in the aimless log file.
        ntables = log.ntables()
        if ntables != 10:
            #raise RuntimeError, '%s tables found in aimless output, program expected 10.' %ntables
            self.logger.debug('%s tables found in aimless output, program exepected 10.' %ntables)

        tables = []
        for i in range(0,ntables):
            data = []
            # Ignore the Anisotropy analysis table (it's not always present
            # and if you don't ignore it, it causes problems when it is not
            # there.)
            if 'Anisotropy analysis' in log.tables()[i].title():
                pass
            else:
                for line in log.tables()[i].data().split('\n'):
                    if line != '':
                        data.append(line.split())
                tables.append(data)

        # Pull out information for the summary table.
        flag = True
        summary = log.keytext(0).message().split('\n')
        # For some reason, 'Anomalous flag switched ON' is not always being found.
        # so this line creates a blank entry of anomalous_report so that it cannot
        # be referenced before assignment.
        anomalous_report = ''

        for line in summary:
            if 'Space group' in line:
                space_group = line.strip().split(': ')[-1]
            elif 'Average unit cell' in line:
                unit_cell = map(float, line.split()[3:])

            elif 'Anomalous flag switched ON' in line:
                anomalous_report = line
            #elif flag == True and 'from half-dataset correlation' in line:
            #    flag = False
            #    res_cut = line

        int_results={
                     'bins_low': map(float, summary[3].split()[-3:]),
                     'bins_high': map(float, summary[4].split()[-3:]),
                     'rmerge_anom': map(float, summary[6].split()[-3:]),
                     'rmerge_norm': map(float, summary[7].split()[-3:]),
                     'rmeas_anom': map(float, summary[8].split()[-3:]),
                     'rmeas_norm': map(float, summary[9].split()[-3:]),
                     'rpim_anom': map(float, summary[10].split()[-3:]),
                     'rpim_norm': map(float, summary[11].split()[-3:]),
                     'rmerge_top': float(summary[12].split()[-3]),
                     'total_obs': map(int, summary[13].split()[-3:]),
                     'unique_obs': map(int, summary[14].split()[-3:]),
                     'isigi': map(float, summary[15].split()[-3:]),
                     'cc-half': map(float, summary[16].split()[-3:]),
                     'completeness': map(float, summary[17].split()[-3:]),
                     'multiplicity': map(float, summary[18].split()[-3:]),
                     'anom_completeness': map(float, summary[20].split()[-3:]),
                     'anom_multiplicity': map(float, summary[21].split()[-3:]),
                     'anom_correlation': map(float, summary[22].split()[-3:]),
                     'anom_slope': [float(summary[23].split()[-3])],
                     'scaling_spacegroup': space_group,
                     'scaling_unit_cell': unit_cell,
                     #'text': res_cut,
                     'text2': anomalous_report
                     }

        # Now create a list for each graph to be plotted.
        # This list should have [title, xlabel, ylabels, xcol, ycols, tableNum]
        # title is the graph title in the aimless logfile,
        # xlabel is the label to be used for the x-axis, ylabels are the labels
        # to be used for the data sets in the graph, xcol is the position within
        # the table where the x-values are , ycols are the position of the y-vaules,
        # and tableNum is the position of the table within the list tables.
        graphs = [
                  ['Mn(k) & 0k (theta=0) v. batch', 'image_number', ['Mn(k)', '0k'], 0, [5,6], 0],
                  ['Relative Bfactor v. batch', 'image_number', ['Bfactor'], 0, [4], 0],
                  ['Rmerge v Batch for all runs', 'image_number', ['Rmerge', 'SmRmerge'], 0, [5,12], 1],
                  ['Maximum resolution limit, I/sigma > 1.0', 'image_number', ['MaxRes','SmMaxRes'], 0, [10,13], 1],
                  ['Cumulative multiplicity', 'image_number', ['CMlplc'], 0, [11], 1],
                  ['Imean & RMS Scatter', 'image_number', ['Mn(I)','RMSdev'], 0, [2,3], 1],
                  ['Imean/RMS scatter', 'image_number', ['I/rms'], 0, [4], 1],
                  ['Number of rejects', 'image_number', ['Nrej'], 0, [7], 1],
                  ['Anom & Imean CCs v resolution', 'Dmin (A)', ['CCanom', 'CC1/2'], 1, [3,6], 2],
                  ['RMS correlation ratio', 'Dmin (A)', ['RCRanom'], 1, [5], 2],
                  #['Imean CCs v resolution', 'Dmin (A)', ['CC_d12', 'CC_d3'], 1, [3,4], 3],
                  #['Mn(I/sd) v resolution', 'Dmin (A)', ['(I/sd)d12', '(I/sd)d3'], 1, [5,6], 3],
                  #['Projected Imean CCs v resolution', 'Dmin (A)', ['CCp1', 'CCp3'], 1, [7,8], 3],
                  ['I/sigma, Mean Mn(I)/sd(Mn(I))', 'Dmin (A)', ['I/RMS','Mn(I/sd)'], 1, [12,13], 3],
                  ['Rmerge, Rfull, Rmeas, Rpim v Resolution', 'Dmin (A)', ['Rmerge', 'Rfull', 'Rmeas', 'Rpim'], 1, [3,4,6,7], 3],
                  ['Average I, RMSdeviation and Sd', 'Dmin (A)', ['AvI', 'RMSdev', 'sd'], 1, [9,10,11], 3],
                  ['Fractional bias', 'Dmin (A)', ['FrcBias'], 1, [14], 3],
                  ['Rmerge, Rmeas, Rpim v Resolution', 'Dmin (A)',
                      ['Rmerge', 'RmergeOv', 'Rmeas', 'RmeasOv', 'Rpim', 'RpimOv'], 1, [3,4,7,8,9,10], 4],
                  ['Rmerge v Intensity', 'Imax', ['Rmerge', 'Rmeas', 'Rpim'], 0, [1,3,4], 5],
                  ['Completeness v Resolution', 'Dmin (A)', ['%poss', 'C%poss', 'AnoCmp', 'AnoFrc'], 1, [6,7,9,10], 6],
                  ['Multiplicity v Resolution', 'Dmin (A)', ['Mlpclct', 'AnoMlt'], 1, [8,11], 6],
                  ['Sigma(scatter/SD), within 5 sd', '<I>', ['SdFc'], 1, [7], 7],
                  ['Sigma(scatter/SD, within 5 SD, all and within', '<I>', ['SdF', 'SdFc'], 1, [4,7], 7],
                  ['Rcp v. batch', 'relative frame difference', ['Rcp'], 1, [-1], 8]
                  ]
        return(graphs, tables, int_results)

    def parse_aimless2 (self, logfile):
	"""
	Parses the aimless logfile in order to pull out data for
	graphing and the results summary table.
	Relevant values for the summary table are stored in a dict.
	Relevant information for creating plots are stored in a dict,
	with the following format for each entry (i.e. each plot):

	{"<*plot label*>":{
	                   "data":{
	                          "parameters":{<*line parameters*>},
	                           "series":[
	                                     {xs : [],
	                                      ys : []
	                                     }
	                                    ]
	                          }
	                   "parameters" : {<*plot parameters*>}
	                  }
	 ...
	 ...
	}
	"""

	log = smartie.parselog(logfile)

	# Pull out information for the results summary table.
	flag = True
	summary = log.keytext(0).message().split("\n")

	# For some reason "Anomalous flag switched ON" is not always
	# found, so the line below creates a blank entry for the
	# the variable that should be created when that phrase is
	# found, eliminating the problem where the program reports that
	# the variable anomalous_report is referenced before assignment.
	anomalous_report = ""

	for line in summary:
		if "Space group" in line:
			space_group = line.strip().split(": ")[-1]
		elif "Average unit cell" in line:
			unit_cell = map(float, line.split()[3:])
		elif "Anomalous flag switched ON" in line:
			anomalous_report = line

	int_results = {
	               "bins_low": map(float, summary[3].split()[-3:]),
                   "bins_high": map(float, summary[4].split()[-3:]),
                   "rmerge_anom": map(float, summary[6].split()[-3:]),
                   "rmerge_norm": map(float, summary[7].split()[-3:]),
                   "rmeas_anom": map(float, summary[8].split()[-3:]),
                   "rmeas_norm": map(float, summary[9].split()[-3:]),
                   "rpim_anom": map(float, summary[10].split()[-3:]),
                   "rpim_norm": map(float, summary[11].split()[-3:]),
                   "rmerge_top": float(summary[12].split()[-3]),
                   "total_obs": map(int, summary[13].split()[-3:]),
                   "unique_obs": map(int, summary[14].split()[-3:]),
                   "isigi": map(float, summary[15].split()[-3:]),
                   "cc-half": map(float, summary[16].split()[-3:]),
                   "completeness": map(float, summary[17].split()[-3:]),
                   "multiplicity": map(float, summary[18].split()[-3:]),
                   "anom_completeness": map(float, summary[20].split()[-3:]),
                   "anom_multiplicity": map(float, summary[21].split()[-3:]),
                   "anom_correlation": map(float, summary[22].split()[-3:]),
                   "anom_slope": [float(summary[23].split()[-3])],
                   "scaling_spacegroup": space_group,
                   "scaling_unit_cell": unit_cell,
                   "text2": anomalous_report
                  }
        # Smartie can pull table information based on a regular
        # expression pattern that matches the table title from
        # the aimless log file.
        # NOTE : the regular expression must match the beginning
        # of the table's title, but does not need to be the entire
        # title.
        #
        # We will use this to pull out the data from tables we are
        # interested in.
        #
        # The beginning of the titles for all common tables in the
        # aimless log file are given below, but not all of them
        # are currently used to generate a plot.

        scales = "=== Scales v rotation"
        rfactor = "Analysis against all Batches"
        cchalf = "Correlations CC(1/2)"
        anisotropy = "Anisotropy analysis"
        vresolution = "Analysis against resolution, XDSdataset"
        anomalous = "Analysis against resolution, with & without"
        intensity = "Analysis against intensity"
        completeness = "Completeness & multiplicity"
        deviation = "Run 1, standard deviation"
        rcp = "Radiation damage"

        plots = {
            "Rmerge vs Frame" :
		{
                "data" :
		    [ {
                    "parameters" :
		        {
                         "linecolor" : "3",
                         "linelabel" : "Rmerge",
                         "linetype"  : "11",
                         "linewidth" : "3"
		        },
                    "series" :
			[ {
                           "xs" : map(int, log.tables(rfactor)[0].col("N")),
                           "ys" : map(float, log.tables(rfactor)[0].col("Rmerge"))
                        } ]
                    },
                    {
                     "parameters" :
		     	{
                         "linecolor" : "4",
                         "linelabel" : "SmRmerge",
                         "linetype"  : "11",
                         "linewidth" : "3"
			 },
                     "series" :
			[ {
                         "xs" : map(int, log.tables(rfactor)[0].col("N")),
                         "ys" : map(float, log.tables(rfactor)[0].col("SmRmerge"))
                        } ]
                    } ],
                "parameters" :
		    {
                    "toplabel" : "Rmerge vs Batch for all Runs",
                    "xlabel"   : "Image Number"
                    }
                },
            "Imean/RMS scatter" :
		{
                "data" :
		    [ {
		    "parameters" :
		        {
			"linecolor" : "3",
			"linelabel" : "I/rms",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
		        [ {
			"xs" : log.tables(rfactor)[0].col("N"),
			"ys" : log.tables(rfactor)[0].col("I/rms")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "Imean / RMS scatter",
		    "xlabel"   : "Image Number"
		    }
		},
	    "Anomalous & Imean CCs vs Resolution" :
		{
		"data" :
		    [ {
		    "parameters" :
		        {
			"linecolor" : "3",
			"linelabel" : "CCanom",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
		        [ {
			"xs" : log.tables(cchalf)[0].col("1/d^2"),
			"ys" : log.tables(cchalf)[0].col("CCanom")
			} ]
		    },
		    {
		    "parameters" :
		        {
			"linecolor" : "4",
			"linelabel" : "CC1/2",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
		        [ {
			"xs" : log.tables(cchalf)[0].col("1/d^2"),
			"ys" : log.tables(cchalf)[0].col("CC1/2")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "Anomalous & Imean CCs vs. Resolution",
		    "xlabel"   : "Dmid (Angstroms)"
		    }
		},
	    "RMS correlation ration" :
		{
		"data" :
		    [ {
		    "parameters" :
		        {
			"linecolor" : "3",
			"linelabel" : "RCRanom",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
		       	[ {
			"xs" : log.tables(cchalf)[0].col("1/d^2"),
			"ys" : log.tables(cchalf)[0].col("RCRanom")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "RMS correlation ratio",
		    "xlabel"   : "Dmid (Angstroms)"
		    }
		},
	    "I/sigma, Mean Mn(I)/sd(Mn(I))" :
		{
		"data" :
		    [ {
		    "parameters" :
		        {
			"linecolor" : "3",
			"linelabel" : "I/RMS",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
		        [ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("I/RMS")
			} ]
		    },
		    {
		    "parameters" :
		        {
			"linecolor" : "4",
			"linelabel" : "Mn(I/sd)",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
		        [ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("Mn(I/sd)")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "I/sigma, Mean Mn(I)/sd(Mn(I))",
		    "xlabel"   : "Dmid (Angstroms)"
		    }
		},
	   "Rmerge, Rfull, Rmeas, Rpim vs. Resolution" :
	        {
	        "data" :
	            [ {
		    "parameters" :
		        {
			"linecolor" : "3",
			"linelabel" : "Remerge",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("Rmrg")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "4",
			"linelabel" : "Rfull",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("Rfull")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "5",
			"linelabel" : "Rmeas",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("Rmeas")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "6",
			"linelabel" : "Rpim",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("Rpim")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "Rmerge, Rfull, Rmeas, Rpim vs. Resolution",
		    "xlabel"   : "Dmid (Angstroms)"
		    }
		},
	    "Average I, RMS deviation, and Sd" :
		{
		"data" :
		    [ {
		    "parameters" :
			{
			"linecolor" : "3",
			"linelabel" : "Average I",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("AvI")
			} ]
		    },
		    {
		    "parameters" :
		    	{
		    	"linecolor" : "4",
		    	"linelabel" : "RMS deviation",
		    	"linetype"  : "11",
		    	"linewidth" : "3"
		    	},
		    "series" :
			[ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("RMSdev")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "5",
			"linelabel" : "std. dev.",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(vresolution)[0].col("1/d^2"),
			"ys" : log.tables(vresolution)[0].col("sd")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "Average I, RMS dev., and std. dev.",
		    "xlabel"   : "Dmid (Ansgstroms)"
		    }
		},
	    "Completeness" :
		{
		"data" :
		    [ {
		    "parameters" :
			{
			"linecolor" : "3",
			"linelabel" : "%poss",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(completeness)[0].col("1/d^2"),
			"ys" : log.tables(completeness)[0].col("%poss")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "4",
			"linelabel" : "C%poss",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(completeness)[0].col("1/d^2"),
			"ys" : log.tables(completeness)[0].col("C%poss")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "5",
			"linelabel" : "AnoCmp",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(completeness)[0].col("1/d^2"),
			"ys" : log.tables(completeness)[0].col("AnoCmp")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "6",
			"linelabel" : "AnoFrc",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(completeness)[0].col("1/d^2"),
			"ys" : log.tables(completeness)[0].col("AnoFrc")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "Completeness vs. Resolution",
		    "xlabel"   : "Dmid (Angstroms)"
		    }
		},
	    "Redundancy" :
		{
		"data" :
		    [ {
		    "parameters" :
			{
			"linecolor" : "3",
			"linelabel" : "multiplicity",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(completeness)[0].col("1/d^2"),
			"ys" : log.tables(completeness)[0].col("Mlplct")
			} ]
		    },
		    {
		    "parameters" :
			{
			"linecolor" : "4",
			"linelabel" : "anomalous multiplicity",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(completeness)[0].col("1/d^2"),
			"ys" : log.tables(completeness)[0].col("AnoMlt")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "Redundancy",
		    "xlabel"   : "Dmid (Angstroms)"
		    }
		},
	    "Radiation Damage" :
		{
		"data" :
		    [ {
		    "parameters" :
			{
			"linecolor" : "3",
			"linelabel" : "Rcp",
			"linetype"  : "11",
			"linewidth" : "3"
			},
		    "series" :
			[ {
			"xs" : log.tables(rcp)[0].col("Batch"),
			"ys" : log.tables(rcp)[0].col("Rcp")
			} ]
		    } ],
		"parameters" :
		    {
		    "toplabel" : "Rcp vs. Batch",
		    "xlabel"   : "Relative frame difference"
		    }
		}
		}

		# Return to the main program.
	return (plots, int_results)

    def aimless(self, mtzin, resolution=False):
        """
        Runs aimless on the data, including the scaling step.
        """
        self.logger.debug('FastIntegration::aimless')
        self.tprint(arg="  Running Aimless",
                    level=99,
                    color="white")

        mtzout = mtzin.replace('pointless','aimless')
        logfile = mtzout.replace('mtz','log')
        comfile = mtzout.replace('mtz','com')

        aimless_file = ['#!/bin/tcsh\n',
                        #'/share/apps/necat/programs/ccp4-6.3.0/ccp4-6.3.0/bin/aimless hklin %s hklout %s << eof > %s\n' % (mtzin, mtzout, logfile),
                        'aimless hklin %s hklout %s << eof > %s\n' % (mtzin, mtzout, logfile),
                        'anomalous on\n',
                        'scales constant\n',
                        'sdcorrection norefine full 1 0 0 partial 1 0 0\n',
                        'cycles 0\n']#, Change made on Feb. 20, 2015 to exclude bins resolution
                        #'bins resolution 10\n']
        if resolution != False:
            aimless_file.append('resolution %s\n' % resolution)
        aimless_file.append('eof')
        self.write_file(comfile, aimless_file)
        os.chmod(comfile, stat.S_IRWXU)
        cmd = './%s' % comfile
        os.system(cmd)
        return(logfile)

    def pointless(self):
        """
        Runs pointless on the default reflection file, XDS_ASCII.HKl
        to produce an mtz file suitable for input to aimless.
        """
        self.logger.debug("FastIntegration::pointless")
        self.tprint(arg="  Running Pointless", level=10, color="white")

        hklfile = 'XDS_ASCII.HKL'
        mtzfile = '_'.join([self.image_data['image_prefix'], 'pointless.mtz'])
        logfile = mtzfile.replace('mtz', 'log')

        cmd = ('pointless xdsin %s hklout %s << eof > %s\n SETTING C2 \n eof'
        #cmd = ('/home/necat/programs/ccp4-6.4.0/ccp4-6.4.0/bin/pointless xdsin %s hklout %s << eof > %s\n SETTING C2 \n eof'
        #cmd = ('pointless-1.10.13.linux64 xdsin %s hklout %s << eof > %s\n SETTING C2 \n eof'
               % (hklfile, mtzfile, logfile))
        self.logger.debug('cmd = %s' %cmd)
        p = subprocess.Popen(cmd, shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        tmp = open(logfile, 'r').readlines()
        return_value='Failed'
        for i in range(-10,-1):
            if tmp[i].startswith('P.R.Evans'):
                return_value=mtzfile
                break
        return(return_value)

    def parse_xdsstat (self, log, tables_length):
        """
        Parses the output of xdsstat (XDSSTAT.LP) to pull out the Rd
        information

        """
        self.logger.debug('FastIntegration::parsse_xdsstat')

        rd_table = []
        xdsstat = open(log,'r').readlines()
        for line in xdsstat:
            if 'DIFFERENCE' in line:
                split_line = line.split()
                # extract Framediff, R_d, Rd_notfriedel, Rd_friedel.
                table_line = [split_line[0], split_line[2], split_line[4], split_line[6] ]
                rd_table.append(table_line)
        title = 'Rd vs frame_difference'
        xlabel = 'Frame Difference'
        ylabels = ['Rd', 'Rd_notfriedel', 'Rd_friedel']
        xcol = 0
        ycols = [1,2,3]
        tableNum = tables_length
        rd_graph = (title, xlabel, ylabels, xcol, ycols, tableNum)

        return(rd_graph, rd_table)

    def xdsstat(self):
        """
        Runs xdsstat, a program that extracts some extra statistics
        from the results of XDS CORRECT.

        In order for this to run, xdsstat should be installed in the user's path.
        And a script called xdsstat.sh should also be created and available in the path.

        Information about the availability of xdssstat can be obtained at the xdswiki:
        http://strucbio.biologie.uni-konstanz.de/xdswiki/index.php/Xdsstat#Availability

        xdsstat.sh is a simple three line shell script:

        #!/bin/tcsh
        xdsstat << eof > XDSSTAT.LP
        XDS_ASCII.HKL
        eof

        It runs xdsstat on the default reflection file XDS_ASCII.HKL and sends the
        output to the file XDSSTAT.LP
        """
        self.logger.debug('FastIntegration::xdsstat')
        self.tprint(arg="  Running xdsstat", level=10, color="white")

        # Check to see if xdsstat exists in the path
        test = find_executable("xdsstat.sh")
        if test == None:
            self.logger.debug('    xdsstat.sh is not in the defined PATH')
            # Write xdsstat.sh
            xdsststsh = ["#!/bin/bash\n",
                         "xdsstat << eof > XDSSTAT.LP\n",
                         "XDS_ASCII.HKL\n",
                         "eof\n"]
            self.write_file("xdsstat.sh", xdsststsh)
            os.chmod("./xdsstat.sh", stat.S_IRWXU)

        try:
            job = Process(target=Utils.processLocal, args=(('xdsstat.sh'), self.logger))
            job.start()
            while job.is_alive():
                time.sleep(1)
        except IOError as e:
            self.logger.debug('    xdsstat.sh failed to run properly')
            self.logger.debug(e)
            return('Failed')
        if os.path.isfile('XDSSTAT.LP'):
            return('XDSSTAT.LP')
        else:
            self.logger.debug('    XDSSTAT.LP does not exist')
        return('Failed')

    def finish_data (self, results):
        """
        Final creation of various files (e.g. an mtz file with R-flag added,
        .sca files with native or anomalous data treatment)
        """
        in_file = os.path.join(results['dir'], results['mtzfile'])
        self.logger.debug('FastIntegration::finish_data - in_file = %s'
                          % in_file)

        # Truncate the data.
        comfile = ['#!/bin/csh\n',
                   'truncate hklin %s hklout truncated.mtz << eof > truncate.log\n'
                   % in_file,
                   'ranges 60\n',
                   'eof\n']
        self.write_file('truncate.sh', comfile)
        os.chmod('truncate.sh', stat.S_IRWXU)
        p = subprocess.Popen('./truncate.sh', shell=True)
        sts = os.waitpid(p.pid,0)[1]

        # Set the free R flag.
        comfile = ['#!/bin/csh\n',
                   'freerflag hklin truncated.mtz hklout freer.mtz <<eof > freer.log\n',
                   'END\n',
                   'eof']
        self.write_file('freer.sh', comfile)
        os.chmod('freer.sh', stat.S_IRWXU)
        p = subprocess.Popen('./freer.sh', shell=True)
        sts = os.waitpid(p.pid,0)[1]

        # Create the merged scalepack format file.
        comfile = ['#!/bin/csh\n',
                   'mtz2various hklin truncated.mtz hklout NATIVE.sca ',
                   '<< eof > mtz2scaNAT.log\n',
                   'OUTPUT SCALEPACK\n',
                   'labin I=IMEAN SIGI=SIGIMEAN\n',
                   'END\n',
                   'eof']
        self.write_file('mtz2scaNAT.sh', comfile)
        os.chmod('mtz2scaNAT.sh', stat.S_IRWXU)
        p = subprocess.Popen('./mtz2scaNAT.sh', shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        self.fixMtz2Sca('NATIVE.sca')
        Utils.fixSCA(self, 'NATIVE.sca')

        # Create the unmerged scalepack format file.
        comfile = ['#!/bin/csh\n',
                   'mtz2various hklin truncated.mtz hklout ANOM.sca ',
                   '<< eof > mtz2scaANOM.log\n',
                   'OUTPUT SCALEPACK\n',
                   'labin I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-) SIGI(-)=SIGI(-)\n',
                   'END\n',
                   'eof']
        self.write_file('mtz2scaANOM.sh', comfile)
        os.chmod('mtz2scaANOM.sh', stat.S_IRWXU)
        p = subprocess.Popen('./mtz2scaANOM.sh', shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        self.fixMtz2Sca('ANOM.sca')
        Utils.fixSCA(self, 'ANOM.sca')

        # Create a mosflm matrix file
        correct_file = os.path.join(results['dir'], 'CORRECT.LP')
        Xds2Mosflm(xds_file=correct_file, mat_file="reference.mat")

        # Run Shelxc for anomalous signal information
        #if float(results['summary']['bins_high'][-1]) > 4.5:
        #    shelxc_results = None
        #else:
        #    sg = results['summary']['scaling_spacegroup']
        #    cell = ' '.join(results['summary']['scaling_unit_cell'])
        #    sca = 'ANOM.sca'
        #    shelxc_results = self.process_shelxC(cell, sg, sca)
        #    if shelxc_results != None:
        #        try:
        #            self.insert_shelx_results(shelxc_results)
        #        except:
        #            pass
        # Clean up the filesystem.
        # Move some files around
        if os.path.isdir('%s/xds_lp_files' % self.dirs['work']) == False:
            os.mkdir('%s/xds_lp_files' % self.dirs['work'])
        os.system('cp %s/*.LP %s/xds_lp_files/' % (results['dir'], self.dirs['work']))

        tar_name = '_'.join([self.image_data['image_prefix'], str(self.image_data['run_number'])])
        results_dir = os.path.join(self.dirs['work'], tar_name)
        if os.path.isdir(results_dir) == False:
            os.mkdir(results_dir)
        prefix = '%s/%s_%s' %(results_dir, self.image_data['image_prefix'],
                              self.image_data['run_number'])
        os.system('cp freer.mtz %s_free.mtz' % prefix)
        os.system('cp NATIVE.sca %s_NATIVE.sca' % prefix)
        os.system('cp ANOM.sca %s_ANOM.sca' % prefix)
        os.system('cp %s/*aimless.log %s_aimless.log' %(results['dir'], prefix))
        os.system('cp %s/*aimless.com %s_aimless.com' %(results['dir'], prefix))
        os.system('cp %s/*pointless.mtz %s_mergable.mtz' %(results['dir'], prefix))
        os.system('cp %s/*pointless.log %s_pointless.log' %(results['dir'], prefix))
        os.system('cp %s/XDS.LOG %s_XDS.LOG' %(results['dir'], prefix))
        os.system('cp %s/XDS.INP %s_XDS.INP' %(results['dir'], prefix))
        os.system('cp %s/CORRECT.LP %s_CORRECT.LP' %(results['dir'], prefix))
        os.system('cp %s/INTEGRATE.LP %s_INTEGRATE.LP' %(results['dir'], prefix))
        os.system('cp %s/XDSSTAT.LP %s_XDSSTAT.LP' %(results['dir'], prefix))
        os.system('cp %s/XDS_ASCII.HKL %s_XDS.HKL' %(results['dir'], prefix))

        # Remove any integration directories.
        os.system('rm -rf wedge_*')

        # Remove extra files in working directory.
        os.system('rm -f *.mtz *.sca *.sh *.log junk_*')

        # Create a downloadable tar file.
        tar_dir = tar_name
        tar_name += '.tar.bz2'
        tarname = os.path.join(self.dirs['work'], tar_name)
        print 'tar -cjf %s %s' %(tar_name, tar_dir)
        print os.getcwd()
        os.chdir(self.dirs['work'])
        print os.getcwd()
        os.system('tar -cjf %s %s' %(tar_name, tar_dir))

        # Tarball the XDS log files
        lp_name = 'xds_lp_files.tar.bz2'
        print "tar -cjf %s xds_lp_files/" % lp_name
        os.system("tar -cjf %s xds_lp_files/" % lp_name)
        # Remove xds_lp_files directory
        os.system('rm -rf xds_lp_files')
        # If ramdisks were used, erase files from ram_disks.
        if self.ram_use == True and self.settings['ram_cleanup'] == True:
            command = 'rm -rf /dev/shm/%s' %self.image_data['image_prefix']
            for node in self.ram_nodes[0]:
                command2 = 'ssh -x %s "%s"' %(node, command)
                p = subprocess.Popen(command2, shell=True)
                sts = os.waitpid(p.pid,0)[1]

        tmp = results
        #if shelxc_results != None:
        #    tmp['shelxc_results'] = shelxc_results
        files = {'mergable' : '%s_mergable.mtz' % prefix,
                 'mtzfile' : '%s_free.mtz' % prefix,
                 'ANOM_sca' : '%s_ANOM.sca' % prefix,
                 'NATIVE_sca' : '%s_NATIVE.sca' % prefix,
                 'scala_log' : '%s_scala.log' % prefix,
                 'scala_com' : '%s_scala.com' % prefix,
                 'xds_data' : '%s_XDS.HKL' % prefix,
                 'xds_log' : '%s_XDS.LOG' % prefix,
                 'xds_com' : '%s_XDS.INP' % prefix,
                 'downloadable' : tarname
                 }
        tmp['files'] = files

        return(tmp)

    def fixMtz2Sca (self, scafile):
        """
        Corrects the scalepack file generated by mtz2various by removing
        whitespace in the spacegroup name.
        """
        self.logger.debug('FastIntegration::fixMtz2Sca scafile = %s' % scafile)
        inlines = open(scafile, 'r').readlines()
        symline = inlines[2]
        newline = (symline[:symline.index(symline.split()[6])]
                   + ''.join(symline.split()[6:]) + '\n')
        inlines[2] = newline
        self.write_file(scafile, inlines)
        return()

    def run_analysis (self, data, dir):
        """
        Runs "pdbquery" and xtriage on the integrated data.
        data = the integrated mtzfile
        dir = the working integration directory
        """
        self.logger.debug('FastIntegration::run_analysis')
        self.logger.debug('                 data = %s' % data)
        self.logger.debug('                 dir = %s' % dir)
        analysis_dir = os.path.join(dir, 'analysis')
        if os.path.isdir(analysis_dir) == False:
            os.mkdir(analysis_dir)
        run_dict = {'fullname'  : self.image_data['fullname'],
        #           'fullname'  : self.first_image
                    'total'     : self.image_data['total'],
                    'osc_range' : self.image_data['osc_range'],
                    'x_beam'    : self.image_data['x_beam'],
                    'y_beam'    : self.image_data['y_beam'],
                    'two_theta' : self.image_data.get("twotheta", 0),
                    'distance'  : self.image_data['distance']
                   }
        pdb_input = []
        pdb_dict = {}
        pdb_dict['run'] = run_dict
        pdb_dict['dir'] = analysis_dir
        pdb_dict['data'] = data
        pdb_dict["agent_directories"] = self.dirs.get("agent_directories", False)
        pdb_dict['control'] = self.controller_address
        pdb_dict['process_id'] = self.process_id
        pdb_input.append(pdb_dict)
        self.logger.debug('    Sending pdb_input to Autostats')
        try:
            T = AutoStats(pdb_input, self.logger)
            self.logger.debug('I KNOW WHO YOU ARE')
        except:
            self.logger.debug('    Execution of AutoStats failed')
            return('Failed')
        return('Success')

    def process_shelxC (self, unitcell, spacegroup, scafile):
        """
        Runs shelxC.  Determines an appropriate cutoff for anomalous signal.
        Inserts table of shelxC results into the results summary page.
        """
        self.logger.debug('FastIntegration::process_shelxC')
        command = ('shelxc junk << EOF\nCELL %s\nSPAG %s\nSAD %s\nEOF'
                   % (unitcell, spacegroup, scafile) )
        shelx_log = []
        output0 = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        for line in output0.stdout:
            shelx_log.append(line.strip())
            self.logger.debug(line)
        results = self.parse_shelxC(shelx_log)
        res = False
        for i,v in enumerate(results['shelx_dsig']):
            dsig = float(v)
            if dsig > 1.0:
                res =results['shelx_res'][i]
        results['shelx_rescut'] = res
        #self.insert_shelx_results(results)
        return(results)

    def parse_shelxC(self, logfile):
        """
        Parses the shelxc output.
        """
        self.logger.debug('FastIntegration::parse_shelxC')
        shelxc_results={}
        for line in logfile:
            if line.startswith('Resl'):
                if line.split()[2] == '-':
                    shelxc_results['shelx_res'] = line.split()[3::2]
                else:
                    shelxc_results['shelx_res'] = line.split()[2:]
                #shelxc_results['shelx_res'] = line.split()[3::2]
                shelxc_results['shelx_res'] = line.split()[2:]
            elif line.startswith('N(data)'):
                shelxc_results['shelx_data'] = line.split()[1:]
            elif line.startswith('<I/sig>'):
                shelxc_results['shelx_isig'] = line.split()[1:]
            elif line.startswith('%Complete'):
                shelxc_results['shelx_comp'] = line.split()[1:]
            elif line.startswith('<d"/sig>'):
                shelxc_results['shelx_dsig'] = line.split()[1:]
        return(shelxc_results)

    def insert_shelx_results (self, results):
        """
        Inserts shelxC results into the results summary webpage.
        """
        self.logger.debug('FastIntegration::insert_shelx_results')

        htmlfile = open('results.php', 'r').readlines()
        if results['shelx_rescut'] == False:
            text = ('\nAnalysis of ShelxC results finds no resolution shell '
                    + 'where d"/sig is greater than 1.0.\n')
            htmlfile.insert(-10, text)
        else:
            text = ('\nAnalsysis of ShelxC results finds d"/sig greater than '
                    + '1.0 for at least one resolution shell.\n')
            htmlfile.insert(-10, text)
            shelxc = ('<div align ="center">\n' +
                      '<h3 class="green">ShelxC analysis of data</h3>\n' +
                      '<table class="integrate">\n' +
                      '<tr><th>Resl.</th>')
            for item in results['shelx_res']:
                shelxc += ('<td>%s</td>' % item)
            shelxc += ('</tr>\n<tr class="alt"><th>N(data)</th>')
            for item in results['shelx_data']:
                shelxc += ('<td>%s</td>' % item)
            shelxc +=('</tr>\n<tr><th>IsigI</th>')
            for item in results['shelx_isig']:
                shelxc += ('<td>%s</td>' % item)
            shelxc += ('</tr>\n<tr class="alt"><th>%Complete</th>')
            for item in results['shelx_comp']:
                shelxc += ('<td>%s</td>' % item)
            shelxc += ('</tr>\n<tr><th>d"/sig</th>')
            for item in results['shelx_dsig']:
                shelxc += ('<td>%s</td>' % item)
            shelxc += ('</tr>\n<caption>For zero signal d"/sig should be '
                          + 'about 0.80</caption>\n</table></div><br>\n')
            htmlfile.insert(-9, shelxc)
        self.write_file('results.php', htmlfile)
        return()

    def parse_integrateLP (self):
        """
        Parse the INTEGRATE.LP file and extract information
        about the mosaicity.
        """
        self.logger.debug('FastIntegration::parse_integrateLP')

        lp = open('INTEGRATE.LP', 'r').readlines()

        for linenum, line in enumerate(lp):
            if 'SUGGESTED VALUES FOR INPUT PARAMETERS' in line:
                avg_mosaicity_line = lp[linenum + 2]
        avg_mosaicity = avg_mosaicity_line.strip().split(' ')[-1]
        return(avg_mosaicity)

    def parse_correctLP (self):
        """
        Parses the CORRECT.LP file to extract information
        """
        self.logger.debug('FastIntegration::parse_correctLP')

        lp = open('CORRECT.LP', 'r').readlines()
        for i, line in enumerate(lp):
            if 'ISa\n' in line:
                isa_line = lp[i + 1]
                break
        ISa = isa_line.strip().split()[-1]
        return(ISa)

    def find_xds_symm (self, xdsdir, xdsinp):
        """
        Checks xds results for consistency with user input spacegroup.
        If inconsistent, tries to force user input spacegroup on data.
        """
        sym_dict = {'P1' : 1,
                    'P2' : 3, 'P21' : 4,
                    'C2' : 5,
                    'P222' : 16, 'P2221' : 17, 'P21212' : 18, 'P212121' : 19,
                    'C222' : 21, 'C2221' : 20,
                    'F222' : 22,
                    'I222' : 23, 'I212121' : 24,
                    'P4' : 75, 'P41' : 76, 'P42' : 77, 'P43' : 78,
                    'P422' : 89, 'P4212' : 90,
                    'P4122' : 91, 'P41212' : 92, 'P4222' : 93, 'P42212' : 94,
                    'P4322' : 95, 'P43212' : 96,
                    'I4' : 79, 'I41' : 80, 'I422' : 97, 'I4122' : 98,
                    'P3' : 143, 'P31' : 144, 'P32' : 145, 'P312' : 149,
                    'P321' : 150, 'P3112' : 151, 'P3121' : 152, 'P3212' : 153,
                    'P3221' : 154, 'P6' : 168, 'P61' : 169, 'P65' : 170,
                    'P62' : 171, 'P64' : 172, 'P63' : 173, 'P622' : 177,
                    'P6122' : 178, 'P6522' : 179, 'P6222' : 180, 'P6422' : 181,
                    'P6322' : 182,
                    'R3' : 146, 'R32' : 155,
                    'P23' : 195, 'P213' : 198, 'P432' : 207, 'P4232' : 208,
                    'P4332' : 212, 'P4132' : 213,
                    'F23' : 196, 'F432' : 209, 'F4132' : 210,
                    'I23' : 197, 'I213' : 199, 'I432' : 211, 'I4132' : 214
                    }
        sg_num = sym_dict[self.spacegroup]
        logfile = open('XDS.LOG', 'r').readlines()
        for num in (len(logfile),0,-1):
            if 'SPACE_GROUP_NUMBER=' in logfile(num):
                line = logfile(num).split('=')
                break
        if sg_num != int(line[-1]):
            self.modify_xdsinput_for_symm(xdsinp, sg_num, 'IDXREF.LP')
            self.tprint(arg="\n  Integrating with user-input spacegroup forced", level=99, color="white", newline=False)
            self.xds_run(xdsdir)
            newinp = self.check_for_xds_errors(xdsdir, xdsinp)
            if newinp == False:
                self.logger.debug('  Unknown xds error occurred. Please check for cause!')
                return('Failed')
        return(newinp)

    def modify_xdsinput_for_symm(self, xdsinp, sg_num, logfile):
        """
        Modifys the XDS input to rerun integration in user input spacegroup
        """
        if sg_num == 1:
            bravais = 'aP'
        elif sg_num >= 3 <= 4:
            bravais = 'mP'
        elif sg_num == 5:
            bravais = 'mC'
        elif sg_num >= 16 <= 19:
            bravais = 'oP'
        elif sg_num >= 20 <= 21:
            bravais = 'oC'
        elif sg_num == 22:
            bravais = 'oF'
        elif sg_num >= 23 <= 24:
            bravais = 'oI'
        elif sg_num >= 75 <= 78 or sg_num >= 89 <= 96:
            bravais = 'tP'
        elif sg_num >= 79 <= 80 or sg_num >= 97 <=98:
            bravais = 'tI'
        elif sg_num >= 143 <= 145 or sg_num >= 149 <= 154 or sg_num >= 168 <= 182:
            bravais = 'hP'
        elif sg_num == 146 or sg_num == 155:
            bravais = 'hR'
        elif sg_num == 195 or sg_num == 198 or sg_num >= 207 <= 208 or sg_num >= 212 <= 213:
            bravais = 'cP'
        elif sg_num == 196 or sg_num >= 209 <= 210:
            bravais = 'cF'
        elif sg_num == 197 or sg_num == 199 or sg_num == 211 or sg_num == 214:
            bravais = 'cI'

        # Now search IDXREF.LP for matching cell information.
        idxref = open(logfile, 'r').readlines()
        for line in idxref:
            if bravais in line and '*' in line:
                splitline = line.split()
                break
        cell = ('%s %s %s %s %s %s' %(splitline[4:]))
        xdsinp[-2] = 'JOB=INTEGRATE CORRECT\n\n'
        xdsinp.append('SPACE_GROUP_NUMBER=%s' % sg_num)
        xdsinp.append('UNIT_CELL_CONSTANTS=%s' % cell)
        self.write_file('XDS.INP', xdsinp)
        return()




class DataHandler(threading.Thread):
    """
    Handles the data that is received from the incoming clientsocket

    Creates a new process by instantiating a subclassed multiprocessing.Process
    instance which will act on the information which is passed to it upon
    instantiation.  That class will then send back results on the pipe
    which it is passed and Handler will send that up the clientsocket.
    """
    def __init__(self, input, tprint=False, logger=False, verbose=True):

        threading.Thread.__init__(self)

        self.input = input
        self.verbose = verbose

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("DataHandler.__init__")

        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        self.start()

    def run(self):
        # Create a pipe to allow interprocess communication.
        #parent_pipe,child_pipe = Pipe()
        # Instantiate the integration case
        tmp = RapdAgent(None, self.input, self.tprint, self.logger)
        # Print out what would be sent back to the RAPD caller via the pipe
        # self.logger.debug parent_pipe.recv()

if __name__ == '__main__':
    # Set up logging
    LOG_FILENAME = '/gpfs5/users/necat/David/process/temp3/fast_integration.logger'
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler
                      )
    # Construct test input
    command = 'INTEGRATE'
    dirs = { 'images' : \
             '/gpfs6/users/necat/test_data/lyso/',
             'data_root_dir' : 'gpfs6/users/necat/',
             'work' : '/gpfs5/users/necat/David/process/temp3/',
             'html' : '/gpfs5/users/necat/David/process/temp3/',
             'user' : '/home/dneau/RAPD_testing/test/'}
    image_data = {'osc_start' : '0.00',
                  'osc_range' : '0.10',
                  'size1' : '2463',
                  'size2' : '2527',

                  'image_prefix' : 'lysozym-1',
                  'beamline' : '24_ID_C',
                  'ID' : 'lysozym-1_1',
                  'detector' : 'PILATUS',
                  'distance' : '380.00',
                  'x_beam' : '215.1',
                  'y_beam' : '211.2',
                  'pixel_size' : '0.172',
                  'wavelength' : '0.9999',
                  'run_number' : '1',
                  'twotheta' : 0.0,
                  'ccd_image_saturation' : '65535',
                  'directory' : '/gpfs6/users/necat/test_data/lyso/',
                  'directory' : '/gpfs6/users/necat/test_data/lyso/',
                  'process_id' : '0',
                  'fullname' : \
                  '/gpfs6/users/yale/Pyle_Aug11/image/marco/GIIi/mm2-2/mm2-2_1_005.img' }
    run_data = {'distance' : '380.0',
                'image_prefix' : 'lysozym-1',
                'run_number' : '1',
                'start' : 1,
                'time' : 1.0,
                'directory' : '/gpfs6/users/necat/test_data/lyso/',
                'total' : 500}
    data = {'image_data' : image_data,
            'run_data' : run_data}
    settings = {'spacegroup' : 'P41212',
                'work_directory' : '/home/dneau/RAPD_testing/test/mosflm_test',
                'work_dir_override' : 'False',
                'anomalous' : 'False',
                'multiprocessing' : 'True',
                'ram_integrate' : False,
                'ram_nodes' : [['compute-0-15', 'compute-0-1', 'compute-0-2', 'compute-0-3', 'compute-0-4',
                                'compute-0-5','compute-0-6', 'compute-0-7', 'compute-0-8', 'compute-0-9',
                                'compute-0-10', 'compute-0-11', 'compute-0-12', 'compute-0-13',
                                'compute-0-14'],
                                [1, 61, 121, 181, 241, 301, 361, 421, 481, 541, 601, 661, 721, 781, 841],
                                [60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900]
                                ],
                'ram_cleanup' : False
                }
    controller_address = ['127.0.0.1' , 50001]
    input = [command, dirs, data, settings, controller_address]
    # Call the handler.
    T = DataHandler(input, logger)

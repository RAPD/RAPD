"""
RAPD plugin for fast integration with XDS
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

# This is an active rapd plugin
RAPD_PLUGIN = True

# This handler's request type
PLUGIN_TYPE = "INTEGRATE"
PLUGIN_SUBTYPE = "CORE"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "bd11f4401eaa11e697c3ac87a3333966"
VERSION = "2.0.0"

# Standard imports
from distutils.spawn import find_executable
import json
import logging
import logging.handlers
import math
import multiprocessing
from multiprocessing import Process
import os
# import os.path
from pprint import pprint
# import shutil
import stat
import subprocess
import sys
import threading
import time

import numpy

# RAPD imports
from plugins.subcontractors.xdsme.xds2mos import Xds2Mosflm
from plugins.subcontractors.aimless import parse_aimless
from plugins.subcontractors.xds import get_avg_mosaicity_from_integratelp, get_isa_from_correctlp
from utils.communicate import rapd_send
import utils.exceptions as exceptions
# from utils.numbers import try_int, try_float
import utils.credits as rcredits
from utils.processes import local_subprocess
import utils.text as text
import utils.xutils as Utils
import utils.spacegroup as spacegroup

# Import RAPD plugins
import plugins.analysis.commandline
import plugins.analysis.plugin

# Software dependencies
VERSIONS = {
    "aimless": (
        "version 0.5",
        ),
    "freerflag": (
        "version 2.2",
    ),
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    ),
    "mtz2various": (
        "version 1.1",
    ),
    "pointless": (
        "version 1.10",
        ),
    "truncate": (
        "version 7.0",
    ),
    "xds": (
        "VERSION Nov 1, 2016",
        ),
    "xds_par": (
        # "VERSION May 1, 2016",
        "VERSION Nov 1, 2016",
        ),
}

class RapdPlugin(Process):
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

    spacegroup = False
    low_res = False
    hi_res = False

    results = {}

    def __init__(self, site, command, tprint=False, logger=False):
        """
        Initialize the plugin

        Keyword arguments
        site -- full site settings
        command -- dict of all information for this plugin to run
        """

        # pprint(command)
        # sys.exit()

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
        self.preferences = self.command.get("preferences")
        self.controller_address = self.command.get("return_address", False)

        # Store into results
        self.results["command"] = command
        self.results["process"] = {
            "process_id": self.command.get("process_id"),
            "status": 1}

        self.dirs = self.command["directories"]
        self.image_data = self.command.get("data").get("image_data")
        self.run_data = self.command.get("data").get("run_data")
        self.process_id = self.command["process_id"]

        self.logger.debug("self.image_data = %s", self.image_data)

        if self.preferences.get("start_frame", False):
            self.image_data["start"] = self.preferences.get("start_frame")
        else:
            self.image_data["start"] = self.run_data.get("start")
        # print "self.image_data[\"start\"]", self.image_data["start"]

        if self.preferences.get("end_frame", False):
            self.image_data["total"] = self.preferences.get("end_frame") - \
                                       self.image_data["start"] + 1
        else:
            self.image_data["total"] = self.run_data.get("total")
        # print "self.image_data[\"total\"]", self.image_data["total"]

        self.image_data['image_template'] = self.run_data['image_template']

        # Check for 2theta tilt:
        if 'twotheta' in self.run_data:
            self.image_data['twotheta'] = self.run_data['twotheta']
            # self.image_data['start'] = self.preferences['request']['frame_start']
            # self.image_data['total'] = str( int(self.preferences['request']['frame_start'])
            #                         + int(self.preferences['request']['frame_finish']) - 1)
        if self.preferences.get('spacegroup', False):
            self.spacegroup = self.preferences['spacegroup']

        if self.preferences.get("hi_res", False):
            self.hi_res = self.preferences.get("hi_res")

        if self.preferences.get("low_res", False):
            self.low_res = self.preferences.get("low_res")

        if 'multiprocessing' in self.preferences:
            self.cluster_use = self.preferences['multiprocessing']
            if self.cluster_use == 'True':
                self.cluster_use = True
            elif self.cluster_use == 'False':
                self.cluster_use = False
        else:
            self.cluster_use = False

        if 'ram_integrate' in self.preferences:
            self.ram_use = self.preferences['ram_integrate']
            if self.ram_use == 'True':
                self.ram_use = True
            elif self.ram_use == 'False':
                self.ram_use = False
            if self.ram_use == True:
                self.ram_nodes = self.preferences['ram_nodes']
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

        if 'standalone' in self.preferences:
            self.standalone = self.preferences['standalone']
            if self.standalone == 'True':
                self.standalone = True
            elif self.standalone == 'False':
                self.standalone = False
        else:
            self.standalone = False

        if 'work_dir_override' in self.preferences:
            if (self.preferences['work_dir_override'] == True
                    or self.preferences['work_dir_override'] == 'True'):
                self.dirs['work'] = self.preferences['work_directory']

        if 'beam_center_override' in self.preferences:
            if (self.preferences['beam_center_override'] == True
                    or self.preferences['beam_center_override'] == 'True'):
                self.image_data['x_beam'] = self.preferences['x_beam']
                self.image_data['y_beam'] = self.preferences['y_beam']

        # Some detectord need flipped for XDS
        if self.preferences.get('flip_beam', False):
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
        # self.start()

    def run(self):
        self.logger.debug('Fastintegration::run')
        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """
        Things to do before main proces runs.
        1. Change to the correct working directory.
        2. Read in detector specific parameters.
        """
        self.logger.debug('FastIntegration::preprocess')
        self.tprint(0, "progress")
        if os.path.isdir(self.dirs['work']) == False:
            os.makedirs(self.dirs['work'])
        os.chdir(self.dirs['work'])

        self.xds_default = self.create_xds_input(self.preferences['xdsinp'])

        self.check_dependencies()

    def check_dependencies(self):
        """Make sure dependencies are all available"""

        # Any of these missing, dead in the water
        for executable in ("aimless", "freerflag", "mtz2various", "pointless", "truncate", "xds"):
            if not find_executable(executable):
                self.tprint("Executable for %s is not present, exiting" % executable,
                            level=30,
                            color="red")
                self.results["process"]["status"] = -1
                self.results["error"] = "Executable for %s is not present" % executable
                self.write_json(self.results)
                raise exceptions.MissingExecutableException(executable)

        # If no gnuplot turn off printing
        if self.preferences.get("show_plots", True) and (not self.preferences.get("json", False)):
            if not find_executable("gnuplot"):
                self.tprint("\nExecutable for gnuplot is not present, turning off plotting",
                            level=30,
                            color="red")
                self.preferences["show_plots"] = False

    def process(self):
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
            return

        xds_input = self.xds_default

        if self.command["command"] == 'XDS':
            integration_results = self.xds_total(xds_input)
        else:
            if os.path.isfile(self.last_image) == True:
                if self.ram_use == True:
                    integration_results = self.ram_total(xds_input)
                else:
                    integration_results = self.xds_total(xds_input)
            else:
                if self.ram_use == True:
                    integration_results = self.ram_integrate(xds_input)
                elif (self.image_data['detector'] == 'ADSC' or
                      self.cluster_use == False):
                    integration_results = self.xds_split(xds_input)
                else:
                    integration_results = self.xds_processing(xds_input)
            os.chdir(self.dirs['work'])

        if integration_results == 'False':
            # Do a quick clean up?
            pass
        else:
            final_results = self.finish_data(integration_results)

        # Set up the results for return
        self.results['process'] = {'plugin_process_id': self.process_id,
                                   'status': 100}
        self.results['results'] = final_results

        self.logger.debug(self.results)
        #self.sendBack2(results)

        self.write_json(self.results)

        self.print_credits()

        self.run_analysis_plugin()

        # return
        #
        # # Skip this for now
        # analysis = self.run_analysis(final_results['files']['mtzfile'], self.dirs['work'])
        # analysis = 'Success'
        # if analysis == 'Failed':
        #     self.logger.debug(analysis)
        #     # Add method for dealing with a failure by run_analysis.
        # elif analysis == 'Success':
        #     self.logger.debug(analysis)
        #     self.results["status"] = "SUCCESS"
        #     self.logger.debug(self.results)
        #     # self.sendBack2(results)
        #     if self.controller_address:
        #         rapd_send(self.controller_address, self.results)
        #
        # return

    def run_analysis_plugin(self):
        """Set up and run the analysis plugin"""

        self.logger.debug("Setting up analysis plugin")
        self.tprint("\nLaunching ANALYSIS plugin", level=30, color="blue")

        # Construct the pdbquery plugin command
        class AnalysisArgs(object):
            """Object containing settings for plugin command construction"""
            clean = True
            datafile = self.results["results"]["files"]["mtzfile"]
            pdbquery = True
            show_plots = self.preferences["show_plots"]
            run_mode = "subprocess-interactive"
            sample_type = "default"
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
        analysis_result = plugin.RapdPlugin(analysis_command,
                                            self.tprint,
                                            self.logger)

        self.results["analysis"] = analysis_result

    def postprocess(self):
        """After it's all done"""

        self.tprint(100, "progress")

    def ram_total(self, xdsinput):
        """
        This function controls processing by XDS when the complete data
        is present and distributed to ramdisks on the cluster
        """
        self.logger.debug('Fastintegration::ram_total')
        first = int(self.image_data['start'])
        last = int(self.image_data['start']) + int(self.image_data['total']) -1
        data_range = '%s %s' %(first, last)
        directory = 'wedge_%s_%s' %(first, last)
        xdsdir = os.path.join(self.dirs['work'], directory)
        if os.path.isdir(xdsdir) == False:
            os.mkdir(xdsdir)
        os.chdir(xdsdir)

        # Figure out how many images are on the first node.
        # If greater than self.procs, simply set up spot ranges with a number
        # of images equal to self.procs from the first and last ram nodes.
        # If less than self.procs, reduce self.procs and set up spot ranges
        # with all of the images on the first and last ram nodes.
        num_images = self.ram_nodes[2][0] - self.ram_nodes[1][0] + 1
        if num_images < self.procs:
            self.procs = num_images
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

        newinp = self.check_for_xds_errors(xdsdir, xdsinp)
        if newinp == False:
            self.logger.debug('  Unknown xds error occurred. Please check for cause!')
            self.tprint(arg="Unknown xds error occurred. Please check for cause!",
                        level=10,
                        color="red")
            raise Exception("Unknown XDS error")
        else:
            # Find a suitable cutoff for resolution
            # Returns False if no new cutoff, otherwise returns the value of
            # the high resolution cutoff as a float value.
            new_rescut = self.find_correct_res(xdsdir, 1.0)
            # sys.exit()
            if new_rescut != False:
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.nocutoff' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.nocutoff' %xdsdir)
                newinp[-2] = 'JOB=CORRECT\n\n'
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
                newinp[-2] = 'JOB=INTEGRATE CORRECT\n\n'
                newinp[-3] = '\n'
                self.write_file('XDS.INP', newinp)
                self.xds_ram(self.ram_nodes[0][0])
                final_results = self.run_results(xdsdir)

            final_results['status'] = 'SUCCESS'
            return final_results


    def change_xds_inp(self, xds_input, new_line):
        """Modify the XDS.INP lines with the input line"""

        param = new_line.split("=")[0].strip()
        xds_output = []
        found = False
        for line in xds_input:
            if param+"=" in line:
                found = True
                xds_output.append(new_line)
            else:
                xds_output.append(line)

        # Append the line if it is new
        if not found:
            xds_output.append(new_line)

        return xds_output

    def xds_total(self, xdsinput):
        """
        This function controls processing by XDS when the complete data
        set is already present on the computer system.
        """
        self.logger.debug('Fastintegration::xds_total')
        self.tprint(arg="\nXDS processing", level=99, color="blue")

        first = int(self.image_data['start'])
        last = int(self.image_data['start']) + int(self.image_data['total']) -1
        data_range = '%s %s' %(first, last)
        self.logger.debug('start = %s, total = %s',
                          self.image_data['start'],
                          self.image_data['total'])
        self.logger.debug('first - %s, last = %s', first, last)
        self.logger.debug('data_range = %s', data_range)
        directory = 'wedge_%s_%s' % (first, last)
        xdsdir = os.path.join(self.dirs['work'], directory)
        if os.path.isdir(xdsdir) == False:
            os.mkdir(xdsdir)

        xdsinp = xdsinput[:]
        if self.low_res or self.hi_res:
            if not self.low_res:
                low_res = 200.0
            else:
                low_res = self.low_res
            if not self.hi_res:
                hi_res = 0.9
            else:
                hi_res = self.hi_res
            xdsinp = self.change_xds_inp(
                xdsinp,
                "INCLUDE_RESOLUTION_RANGE=%.2f %.2f\n" % (low_res, hi_res))
        xdsinp = self.change_xds_inp(
            xdsinp,
            "MAXIMUM_NUMBER_OF_PROCESSORS=%s\n" % self.procs)
        xdsinp = self.change_xds_inp(
            xdsinp,
            "MAXIMUM_NUMBER_OF_JOBS=%s\n" % self.jobs)
        xdsinp = self.change_xds_inp(xdsinp, "JOB=XYCORR INIT COLSPOT \n\n")
        xdsinp = self.change_xds_inp(xdsinp, "DATA_RANGE=%s\n" % data_range)
        xdsfile = os.path.join(xdsdir, 'XDS.INP')
        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Searching for peaks",
                    level=99,
                    color="white",
                    newline=False)
        self.xds_run(xdsdir)

        # Index
        xdsinp[-2] = ("JOB=IDXREF \n\n")
        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Indexing",
                    level=99,
                    color="white",
                    newline=False)
        self.xds_run(xdsdir)

        # Integrate
        # Override spacegroup?
        if self.spacegroup != False:
            # Check consistency of spacegroup, and modify if necessary.
            xdsinp = self.find_xds_symm(xdsdir, xdsinp)
        else:
            xdsinp = self.change_xds_inp(
                xdsinp,
                "JOB=DEFPIX INTEGRATE CORRECT \n\n")

        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Integrating",
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

        # Prepare the display of results.
        prelim_results = self.run_results(xdsdir)
        self.tprint("\nPreliminary results summary", 99, "blue")
        self.print_results(prelim_results)
        self.tprint(33, "progress")

        # Grab the spacegroup from the Pointless output and convert to number for XDS
        sg_let_pointless = prelim_results["summary"]["scaling_spacegroup"]
        sg_num_pointless = spacegroup.ccp4_to_number[sg_let_pointless]

        # XDS-determined spacegroup
        sg_num_xds = prelim_results["xparm"]["sg_num"]
        sg_let_xds = spacegroup.number_to_ccp4[sg_num_xds]


        # Do Pointless and XDS agree on spacegroup?
        spacegoup_agree = True
        if sg_num_pointless != sg_num_xds:
            self.tprint("Pointless and XDS disagree on spacegroup %s vs %s" %
                        (sg_let_pointless, sg_let_xds),
                        99,
                        "red")
            if self.preferences["spacegroup_decider"] in ("auto", "pointless"):
                self.tprint(" Using the pointless spacegroup %s" % sg_let_pointless, 99, "red")
            else:
                self.tprint(" Using the XDS spacegroup %s" % sg_let_xds, 99, "red")
            spacegoup_agree = False

        if self.preferences["spacegroup_decider"] in ("auto", "pointless"):
            newinp = self.change_xds_inp(
                newinp,
                "UNIT_CELL_CONSTANTS=%.2f %.2f %.2f %.2f %.2f %.2f\n" %
                tuple(prelim_results["summary"]["scaling_unit_cell"]))
            newinp = self.change_xds_inp(
                newinp,
                "SPACE_GROUP_NUMBER=%d\n" % sg_num_pointless)

        # Already have hi res cutoff
        if self.hi_res:
            new_rescut = self.hi_res
        # Find a suitable cutoff for resolution
        else:
            if self.low_res:
                low_res = self.low_res
            else:
                low_res = 200.0
            # Returns False if no new cutoff, otherwise returns the value of
            # the high resolution cutoff as a float value.
            new_rescut = self.find_correct_res(xdsdir, 1.0)
            # sys.exit()
            newinp = self.change_xds_inp(newinp, "JOB= INTEGRATE CORRECT \n\n")
            # newinp[-2] = 'JOB= INTEGRATE CORRECT \n\n'
            if new_rescut != False:
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.nocutoff' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.nocutoff' %xdsdir)
                newinp = self.change_xds_inp(
                    newinp,
                    "%sINCLUDE_RESOLUTION_RANGE=%.2f %.2f\n" % (newinp[-2], low_res, new_rescut))
                # newinp[-2] = '%sINCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % (newinp[-2], new_rescut)
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
                self.tprint(66, "progress")

        # Polish up xds processing by moving GXPARM.XDS to XPARM.XDS
        # and rerunning xds.
        #
        # If low resolution, don't try to polish the data, as this tends to blow up.
        polishing_rounds = 0
        if new_rescut <= 4.5:
            # Don't use the GXPARM if changing the spacegroup on the first polishing round
            if spacegoup_agree or \
               self.preferences["spacegroup_decider"] == "xds" or \
               polishing_rounds > 0:
                os.rename('%s/GXPARM.XDS' % xdsdir, '%s/XPARM.XDS' % xdsdir)
            os.rename('%s/CORRECT.LP' % xdsdir, '%s/CORRECT.LP.old' % xdsdir)
            os.rename('%s/XDS.LOG' % xdsdir, '%s/XDS.LOG.old' % xdsdir)
            self.write_file(xdsfile, newinp)
            self.tprint(arg="  Polishing",
                        level=99,
                        color="white",
                        newline=False)
            self.xds_run(xdsdir)
            # final_results = self.run_results(xdsdir)
        else:
            # Check to see if a new resolution cutoff should be applied
            new_rescut = self.find_correct_res(xdsdir, 1.0)
            if new_rescut != False:
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.oldcutoff' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.oldcutoff' %xdsdir)
                newinp[-2] = '%sINCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % (newinp[-2], new_rescut)
                self.write_file(xdsfile, newinp)
                self.tprint(arg="  New resolution cutoff", level=99, color="white", newline=False)
                self.xds_run(xdsdir)
        polishing_rounds += 1
        final_results = self.run_results(xdsdir)

        # Put data into the commanline
        self.tprint("\nFinal results summary", 99, "blue")
        self.print_results(final_results)
        self.print_plots(final_results)
        self.tprint(90, "progress")

        final_results['status'] = 'ANALYSIS'
        return final_results

    def xds_split(self, xdsinput):
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

        file_template = os.path.join(self.image_data['directory'], self.image_template)
        # Figure out how many digits needed to pad image number.
        # First split off the <image number>.<extension> portion of the file_template.
        numimg = self.image_template.split('_')[-1]
        # Then split off the image number portion.
        num = numimg.split('.')[0]
        # Then find the length of the number portion
        pad = len(num)
        replace_string = ''
        for _ in range(0, pad, 1):
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
                    xds_job = Process(target=self.xds_wedge,
                                      args=(proc_dir, frame_count, xdsinput))
                    xds_job.start()
                frame_count += 1
                look_for_file = file_template.replace(replace_string,
                                                      '%0*d' %(pad, frame_count))
            elif timer.is_alive() == False:
                self.logger.debug('     Image %s not found after waiting %s seconds.',
                                  look_for_file,
                                  wait_time)
                self.logger.debug('     RAPD assumes the data collection has been aborted.')
                self.logger.debug('         Launching a final xds job with last image detected.')
                self.image_data['last'] = frame_count - 1
                results = self.xds_total(xdsinput)
                return results

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

        return results

    def xds_processing(self, xdsinput):
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
        last_frame = + int(self.image_data['total']) - int(self.image_data['start']) + 1

        frame_count = first_frame
        # Maximum wait time for next image is exposure time + 15 seconds.
        #wait_time = int(math.ceil(float(self.image_data['time']))) + 15
        # Maximum wait time for next image is exposure time + 60 seconds.
        if self.image_data['detector'] == 'PILATUS' or self.image_data['detector'] == 'HF4M':
            wait_time = int(math.ceil(float(self.image_data['time']))) + 15
        else:
            wait_time = int(math.ceil(float(self.image_data['time']))) + 60
        try:
            wedge_size = int(10 // float(self.image_data['osc_range']))
        except:
            self.logger.debug('xds_processing:: dynamic wedge size allocation failed!')
            self.logger.debug('                 Setting wedge size to 10.')
            wedge_size = 10

        file_template = os.path.join(self.image_data['directory'], self.image_template)
        # Figure out how many digits needed to pad image number.
        # First split off the <image number>.<extension> portion of the file_template.
        numimg = self.image_template.split('_')[-1]
        # Then split off the image number portion.
        num = numimg.split('.')[0]
        # Then find the length of the number portion
        pad = len(num)
        replace_string = ''
        for _ in range(0, pad, 1):
            replace_string += '?'

        look_for_file = file_template.replace(replace_string,
                                              '%0*d' % (pad, frame_count))

        timer = Process(target=time.sleep, args=(wait_time,))
        timer.start()
        # Create the process xds_job (runs a timer with no delay).
        # This is so xds_job exists when it is checked for later on.
        # Eventually xds_job is replaced by the actual integration jobs.
        xds_job = Process(target=time.sleep, args=(0,))
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
                timer = Process(target=time.sleep, args=(wait_time,))
                timer.start()
                # If frame_count is a tenth image, launch and xds job
                # remainder = ((frame_count + 1) - first_frame) % wedge_size
                # self.logger.debug('	remainder = %s' % remainder)
                if xds_job.is_alive == True:
                    self.logger.debug('		xds_job.is_alive = True')
                if (((frame_count + 1) - first_frame) % wedge_size == 0 and
                        xds_job.is_alive() == False):
                    proc_dir = 'wedge_%s_%s' %(first_frame, frame_count)
                    xds_job = Process(target=self.xds_wedge,
                                      args=(proc_dir, frame_count, xdsinput))
                    xds_job.start()
                # Increment the frame count to look for next image
                frame_count += 1
                look_for_file = file_template.replace(replace_string,
                                                      '%0*d' % (pad, frame_count))
            # If next frame does not exist, check to see if timer has expired.
            # If timer has expired, assume an abort has occurred.
            elif timer.is_alive() == False:
                self.logger.debug('     Image %s not found after waiting %s seconds.',
                                  look_for_file,
                                  wait_time)
                # There have been a few cases, particularly with Pilatus's
                # Furka file transfer has failed to copy an image to disk.
                # So check for the next two files before assuming there has
                # been an abort.
                self.logger.debug('     RAPD assumes the data collection has been aborted.')
                self.logger.debug('     RAPD checking for next two subsequent images to be sure.')
                frame_count += 1
                look_for_file = file_template.replace(replace_string, '%0*d' % (pad, frame_count))
                if os.path.isfile(look_for_file) == True:
                    timer = Process(target=time.sleep, args=(wait_time,))
                    timer.start()
                    # Increment the frame count to look for next image
                    frame_count += 1
                    look_for_file = file_template.replace(replace_string,
                                                          '%0*d' %(pad, frame_count))
                else:
                    self.logger.debug(
                        '    RAPD did not fine the next image, checking for one more.')
                    frame_count += 1
                    look_for_file = file_template.replace(replace_string,
                                                          '%0*d' % (pad, frame_count))
                    if os.path.isfile(look_for_file) == True:
                        timer = Process(target=time.sleep, args=(wait_time,))
                        timer.start()
                        frame_count += 1
                        look_for_file = file_template.replace(
                            replace_string,
                            '%0*d' % (pad, frame_count))
                    else:
                        self.logger.debug('         RAPD did not find the next image either.')
                        self.logger.debug(
                            '         Launching a final xds job with last image detected.')
                        self.image_data['total'] = frame_count - 2 - first_frame
                        results = self.xds_total(xdsinput)
                        return results

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

        return results

    def xds_wedge(self, directory, last, xdsinput):
        """
        This function controls processing by XDS for an intermediate wedge
        """
        self.logger.debug('Fastintegration::xds_wedge')
        self.tprint(arg="\nXDS processing", level=99, color="blue")

        first = int(self.image_data['start'])
        data_range = '%s %s' % (first, last)
        xdsdir = os.path.join(self.dirs['work'], directory)
        if os.path.isdir(xdsdir) == False:
            os.mkdir(xdsdir)

        xdsinp = xdsinput[:]
        #xdsinp = self.find_spot_range(first, last, self.image_data['osc_range'], xdsinput[:])
        xdsinp.append('MAXIMUM_NUMBER_OF_PROCESSORS=%s\n' % self.procs)
        xdsinp.append('MAXIMUM_NUMBER_OF_JOBS=%s\n' % self.jobs)
        #xdsinp.append('MAXIMUM_NUMBER_OF_JOBS=1\n')
        xdsinp.append('JOB=XYCORR INIT COLSPOT !IDXREF DEFPIX INTEGRATE CORRECT\n\n')
        xdsinp.append('DATA_RANGE=%s\n' % data_range)
        xdsfile = os.path.join(xdsdir, 'XDS.INP')
        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Searching for peaks wedge", level=99, color="white", newline=False)
        self.xds_run(xdsdir)

        #xdsinp[-3]=('MAXIMUM_NUMBER_OF_JOBS=%s\n'  % self.jobs)
        xdsinp[-2] = ('JOB=IDXREF DEFPIX INTEGRATE CORRECT\n\n')
        self.write_file(xdsfile, xdsinp)
        self.tprint(arg="  Integrating", level=99, color="white", newline=False)
        self.xds_run(xdsdir)

        # If known xds_errors occur, catch them and take corrective action
        newinp = 'check_again'
        while newinp == 'check_again':
            newinp = self.check_for_xds_errors(xdsdir, xdsinp)
        if newinp == False:
            self.logger.debug('  Unknown xds error occurred for %s.', directory)
            self.logger.debug('  Please check for cause!')
            return
        else:
            # Find a suitable cutoff for resolution
            # Returns False if no new cutoff, otherwise returns the value of
            # the high resolution cutoff as a float value.
            new_rescut = self.find_correct_res(xdsdir, 1.0)
            # sys.exit()
            if new_rescut != False:
                os.rename('%s/CORRECT.LP' %xdsdir, '%s/CORRECT.LP.nocutoff' %xdsdir)
                os.rename('%s/XDS.LOG' %xdsdir, '%s/XDS.LOG.nocutoff' %xdsdir)
                newinp[-2] = 'JOB=INTEGRATE CORRECT\n'
                newinp[-2] = '%sINCLUDE_RESOLUTION_RANGE=200.0 %.2f\n' % (newinp[-2], new_rescut)
                self.write_file(xdsfile, newinp)
                self.tprint(arg="  Reintegrating", level=99, color="white", newline=False)
                self.xds_run(xdsdir)
            results = self.run_results(xdsdir)
        return results

    def create_xds_input(self, xds_dict):
        """
    	This function takes the dict holding XDS keywords and values
    	and converts them into a list of strings that serves as the
    	basis for writing out an XDS.INP file.
    	"""

        self.logger.debug("FastIntegration::create_xds_input")

        # print self.image_data["start"]
        # print self.image_data["total"]

        last_frame = self.image_data['start'] + self.image_data["total"] - 1
        self.logger.debug('last_frame = %s', last_frame)
        # print last_frame
        # self.logger.debug('detector_type = %s' % detector_type)
        background_range = '%s %s' % (int(self.image_data['start']),
                                      int(self.image_data['start']) + 4)

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
        self.last_image = file_template.replace('?', '%d'.zfill(pad) % last_frame, 1)
    	# Remove the remaining '?'
        self.last_image = self.last_image.replace('?', '')
    	# Repeat the last two steps for the first image's filename.
        self.first_image = file_template.replace('?', str(self.image_data['start']).zfill(pad), 1)
        self.first_image = self.first_image.replace('?', '')

    	# Begin constructing the list that will represent the XDS.INP file.
        xds_input = ['!===== DATA SET DEPENDENT PARAMETERS =====\n',
                     'ORGX=%.2f ORGY=%.2f ! Beam Center (pixels)\n' % (x_beam, y_beam),
                     'DETECTOR_DISTANCE=%.2f ! (mm)\n' %
                     (float(self.image_data['distance'])),
                     'OSCILLATION_RANGE=%.2f ! (degrees)\n' %
                     (float(self.image_data['osc_range'])),
                     'X-RAY_WAVELENGTH=%.5f ! (Angstroems)\n' %
                     (float(self.image_data['wavelength'])),
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

        return xds_input

    def write_file(self, filename, file_input):
        """
        Writes out file_input as filename.
        file_input should be a list containing the desired contents
        of the file to be written.
        """
        self.logger.debug('FastIntegration::write_file')
        self.logger.debug('    Filename = %s', filename )
        with open(filename, 'w') as file:
            file.writelines(file_input)
        return

    def find_spot_range(self, first, last, osc, input):
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
        self.logger.debug('     first_frame = %s', first)
        self.logger.debug('     last_frame = %s', last)
        self.logger.debug('     frame_width = %s', osc)

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
                spot2_start = int((int(last) - int(first) + 1) / 2)
            else:
                spot2_start = int(90 / float(osc))
            spot2_end = spot2_start + int(5 / float(osc)) - 1
            input.append('SPOT_RANGE=%s %s\n\n' %(spot2_start, spot2_end))
        return input

    def xds_run(self, directory):
        """
        Launches the running of xds.
        """
        self.logger.debug('FastIntegration::xds_run')
        self.logger.debug('     directory = %s', directory)
        self.logger.debug('     detector = %s', self.image_data['detector'])

        xds_command = 'xds_par'

        os.chdir(directory)
        # TODO skip processing for now
        if self.cluster_use == True:
            xds_proc = Process(target=BLspec.processCluster,
                               args=(self, (xds_command, 'XDS.LOG', '8', 'phase2.q')))
        else:
            xds_proc = multiprocessing.Process(target=local_subprocess,
                                               args=(({"command": xds_command,
                                                       "logfile": "XDS.LOG",
                                                      },)))
        xds_proc.start()
        while xds_proc.is_alive():
            time.sleep(1)
            self.tprint(arg=".", level=99, color="white", newline=False)
        self.tprint(arg=" done", level=99, color="white")
        os.chdir(self.dirs['work'])

        return

    def xds_ram(self, first_node):
        """
        Launches xds_par via ssh on the first_node.
        This ensures that xds runs properly when trying to use
        data distributed to the cluster's ramdisks
        """
        self.logger.debug('FastIntegration::xds_ram')
        my_command = ('ssh -x %s "cd $PWD && xds_par > XDS.LOG"' % first_node)
        self.logger.debug('		%s', my_command)
        p = subprocess.Popen(my_command,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.wait()

        return

    def find_correct_res(self, directory, isigi):
        """
        Looks at CORRECT.LP to find a resolution cutoff, where I/sigma is
        approximately 1.5
        """
        self.logger.debug('     directory = %s', directory)
        self.logger.debug('     isigi = %s', isigi)
        self.tprint(arg="  Determining resolution cutoff ",
                    level=99,
                    color="white",
                    newline=False)

        new_hi_res = False
        correctlp = os.path.join(directory, 'CORRECT.LP')
        try:
            correct_log = open(correctlp, 'r').readlines()
        except IOError as e:
            self.logger.debug('Could not open CORRECT.LP')
            self.logger.debug(e)
            return new_hi_res

        flag = 0
        IsigI = 0
        hires = 0

        # Read from the bottom of CORRECT.LP up, looking for the first
        # occurence of "total", which signals that you've found the
        # last statistic table given giving I/sigma values in the file.
        for i in range(len(correct_log)-1, 0, -1):
            # print hires, correct_log[i].strip()
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
                    #    return False
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
                            # print numpy.interp([isigi], [prev_IsigI, IsigI], [prev_hires, hires])
                            break
                else: # If first character in line is not a digit, you;ve
                    # read through the entire table, so break.
                    new_hi_res = hires
                    break
        self.logger.debug('     prev_hires = %s     prev_IsigI = %s' % (prev_hires, prev_IsigI))
        self.logger.debug('     hires = %s          IsigI = %s' %(hires, IsigI))
        self.logger.debug('	New cutoff = %s' % new_hi_res)
        hi_res = float(new_hi_res)

        self.tprint(arg="new cutoff = %4.2f %s" % (hi_res, text.aring),
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
        xdslog = open('XDS.LOG', 'r').readlines()
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
                    first, last = tmp.split()
                    if int(last) == (int(self.image_data('start'))
                                     + int(self.image_data('total')) - 1):
                        self.logger.debug(
                            '         FAILURE: Already using the full data range available.')
                        return False
                    else:
                        input[-1] = 'SPOT_RANGE=%s %s' % (first, (int(last) + 1))
                        self.write_file('XDS.INP', input)
                        os.system('mv XDS.LOG initialXDS.LOG')
                        self.tprint(arg="\n  Extending spot range",
                                    level=10,
                                    color="white",
                                    newline=False)
                        self.xds_run(dir)
                        return input
                elif 'SOLUTION IS INACCURATE' in line or 'INSUFFICIENT PERCENTAGE' in line:
                    self.logger.debug('    Found inaccurate indexing solution error')
                    self.logger.debug('    Will try to continue anyway')
                    self.tprint(
                        arg="  Found inaccurate indexing solution error - try to continue anyway",
                        level=30,
                        color="red")

                    # Inaccurate indexing solution, can try to continue with DEFPIX,
                    # INTEGRATE, and CORRECT anyway
                    self.logger.debug(' The length of input is %s' % len(input))
                    if 'JOB=DEFPIX' in input[-2]:
                        self.logger.debug('Error = %s' %line)
                        self.logger.debug(
                            'XDS failed to run with inaccurate indexing solution error.')
                        self.tprint(
                            arg="\n  XDS failed to run with inaccurate indexing solution error.",
                            level=30,
                            color="red")
                        return False
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
                        return input
                elif 'SPOT SIZE PARAMETERS HAS FAILED' in line:
                    self.logger.debug('	Found failure in determining spot size parameters.')
                    self.logger.debug(
                        '	Will use default values for REFLECTING_RANGE and BEAM_DIVERGENCE.')
                    self.tprint(arg="\n  Found failure in determining spot size parameters.",
                                level=99,
                                color="red")

                    input.append('\nREFLECTING_RANGE=1.0 REFLECTING_RANGE_E.S.D.=0.10\n')
                    input.append('BEAM_DIVERGENCE=0.9 BEAM_DIVERGENCE_E.S.D.=0.09\n')
                    self.write_file('XDS.INP', input)
                    os.system('mv XDS.LOG initialXDS.LOG')
                    self.tprint(
                        arg="  Integrating after failure in determining spot size parameters",
                        level=99,
                        color="white",
                        newline=False)
                    self.xds_run(dir)
                    return input
                else:
                    # Unanticipated Error, fail the error check by returning False.
                    self.logger.debug('Error = %s' %line)
                    return False
        return input

    def write_forkscripts(self, node_list, osc):
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
        for x in range(0, ntask, 1):
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
        return

    def parse_xparm(self, infile="GXPARM.XDS"):
        """Parse out the XPARM file for information"""

        if not os.path.exists(infile):
            return False

        in_lines = open(infile, "r").readlines()
        results = {}
        line_counter = 1
        for line in in_lines:
            # print line_counter, line.rstrip()
            sline = line.strip().split()

            if line_counter == 2:
                results["starting_frame"] = int(sline[0])
                results["starting_angle"], results["osc_range"] = [float(x) for x in sline[1:3]]
                results["rotation_axis_direction"] = [float(x) for x in sline[3:]]

            elif line_counter == 3:
                results["wavelength"] = float(sline[0])
                results["incident_beam_direction"] = [float(x) for x in sline[1:]]

            elif line_counter == 4:
                sg_num = int(sline[0])
                a, b, c, alpha, beta, gamma = [float(x) for x in sline[1:]]
                # print ">>", sg_num, a, b, c, alpha, beta, gamma, "<<"
                results["sg_num"] = sg_num
                results["a"] = a
                results["b"] = b
                results["c"] = c
                results["alpha"] = alpha
                results["beta"] = beta
                results["gamma"] = gamma

            elif line_counter == 5:
                results["a_axis_unrotated_coords"] = [float(x) for x in sline]

            elif line_counter == 6:
                results["b_axis_unrotated_coords"] = [float(x) for x in sline]

            elif line_counter == 7:
                results["c_axis_unrotated_coords"] = [float(x) for x in sline]

            elif line_counter == 8:
                results["number_detector_segments"] = int(sline[0])
                results["number_fast_pixels"] = int(sline[1])
                results["number_slow_pixels"] = int(sline[2])
                results["pixel_size_fast"] = float(sline[3])
                results["pixel_size_slow"] = float(sline[4])

            elif line_counter == 9:
                results["orgx"], results["orgx"], results["f"] = [float(x) for x in sline]

            elif line_counter == 10:
                results["detector_x_axis"] = [float(x) for x in sline]

            elif line_counter == 11:
                results["detector_y_axis"] = [float(x) for x in sline]

            elif line_counter == 12:
                results["detector_z_axis"] = [float(x) for x in sline]

            line_counter += 1

        return results

    def run_results(self, directory):
        """
        Takes the results from xds integration/scaling and prepares
        tables and plots for the user interface.
        """

        self.logger.debug('FastIntegration::run_results')

        os.chdir(directory)

        orig_rescut = False

        # Open up the GXPARM for info
        xparm = self.parse_xparm()

        # Run pointless to convert XDS_ASCII.HKL to mtz format.
        mtzfile = self.pointless()

        # Run dummy run of aimless to generate various stats and plots.
        # i.e. We don't use aimless for actual scaling, it's already done by XDS.
        if mtzfile != 'Failed':
            aimless_log = self.aimless(mtzfile)
        else:
            self.logger.debug('    Pointless did not run properly!')
            self.logger.debug('    Please check logs and files in %s', self.dirs['work'])
            return 'Failed'

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

        # If manually overiding the hi_res
        if self.preferences.get("hi_res", False):
            res_cut = self.preferences.get("hi_res")
        # Determine from data
        else:
            res_cut = resline.split('=')[1].split('A')[0].strip()
            res_cut2 = resline2.split('=')[1].split('A')[0].strip()
            if float(res_cut2) < float(res_cut):
                res_cut = res_cut2

        # Run aimless with a higher resolution cutoff if the suggested resolution
        # is greater than the initial resolution + 0.05.
        if float(res_cut) > float(current_resolution) + 0.05:
            # Save information on original resolution suggestions
            orig_rescut = resline
            # rerun aimless
            aimless_log = self.aimless(mtzfile, res_cut)

        graphs, summary = parse_aimless(aimless_log)

        wedge = directory.split('_')[-2:]
        summary['wedge'] = '-'.join(wedge)

        # Parse INTEGRATE.LP and add information about mosaicity to summary.
        summary['mosaicity'] = get_avg_mosaicity_from_integratelp()

        # Parse CORRECT.LP and add information from that to summary.
        summary['ISa'] = get_isa_from_correctlp()

        # Parse CORRECT.LP and pull out per wedge statistics
        #self.parse_correct()

        #scalamtz = mtzfile.replace('pointless','scala')
        #scalalog = scalamtz.replace('mtz','log')
        scalamtz = mtzfile.replace('pointless', 'aimless')
        _ = scalamtz.replace('mtz', 'log')

        results = {'status': 'WORKING',
                   'plots': graphs,
                   'summary': summary,
                   'mtzfile': scalamtz,
                   'xparm': xparm,
                   'dir': directory,
                  }
        self.logger.debug("Returning results!")
        self.logger.debug(results)

         # Set up the results for return
        self.results['process'] = {
            'plugin_process_id':self.process_id,
            'status':50
            }
        self.results['results'] = results
        self.logger.debug(self.results)

        # self.sendBack2(tmp)
        if self.controller_address:
            rapd_send(self.controller_address, self.results)

        return results

    def aimless(self, mtzin, resolution=False):
        """
        Runs aimless on the data, including the scaling step.
        """
        self.logger.debug('FastIntegration::aimless')
        self.tprint(arg="  Running Aimless",
                    level=99,
                    color="white")

        mtzout = mtzin.replace('pointless', 'aimless')
        logfile = mtzout.replace('mtz', 'log')
        comfile = mtzout.replace('mtz', 'com')

        aimless_file = ['#!/bin/tcsh\n',
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
        # os.system(cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        return logfile

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
        if self.spacegroup:
            cmd = ("pointless xdsin %s hklout %s << eof > %s\nSETTING C2\n\SPACEGROUP HKLIN\n eof"
                   % (hklfile, mtzfile, logfile))
        else:
            cmd = ('pointless xdsin %s hklout %s << eof > %s\n SETTING C2 \n eof'
                   % (hklfile, mtzfile, logfile))
        self.logger.debug("cmd = %s", cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        # sts = os.waitpid(p.pid, 0)[1]
        tmp = open(logfile, "r").readlines()
        return_value = "Failed"
        for i in range(-10, -1):
            if tmp[i].startswith('P.R.Evans'):
                return_value = mtzfile
                break
        return return_value

    def finish_data(self, results):
        """
        Final creation of various files (e.g. an mtz file with R-flag added,
        .sca files with native or anomalous data treatment)
        """
        in_file = os.path.join(results['dir'], results['mtzfile'])
        self.logger.debug('FastIntegration::finish_data - in_file = %s', in_file)

        # Truncate the data.
        comfile = ['#!/bin/csh\n',
                   'truncate hklin %s hklout truncated.mtz << eof > truncate.log\n'
                   % in_file,
                   'ranges 60\n',
                   'eof\n']
        self.write_file('truncate.sh', comfile)
        os.chmod('truncate.sh', stat.S_IRWXU)
        p = subprocess.Popen('./truncate.sh',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.wait()

        # Set the free R flag.
        comfile = ['#!/bin/csh\n',
                   'freerflag hklin truncated.mtz hklout freer.mtz <<eof > freer.log\n',
                   'END\n',
                   'eof']
        self.write_file('freer.sh', comfile)
        os.chmod('freer.sh', stat.S_IRWXU)
        p = subprocess.Popen('./freer.sh',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.wait()

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
        p = subprocess.Popen('./mtz2scaNAT.sh',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.wait()
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
        p = subprocess.Popen('./mtz2scaANOM.sh',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.wait()
        self.fixMtz2Sca('ANOM.sca')
        Utils.fixSCA(self, 'ANOM.sca')

        # Create a mosflm matrix file
        correct_file = os.path.join(results['dir'], 'CORRECT.LP')
        Xds2Mosflm(xds_file=correct_file, mat_file="reference.mat")

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
        # os.system('cp %s/XDSSTAT.LP %s_XDSSTAT.LP' %(results['dir'], prefix))
        os.system('cp %s/XDS_ASCII.HKL %s_XDS.HKL' %(results['dir'], prefix))

        # Remove any integration directories.
        os.system('rm -rf wedge_*')

        # Remove extra files in working directory.
        os.system('rm -f *.mtz *.sca *.sh *.log junk_*')

        # Create a downloadable tar file.
        tar_dir = tar_name
        tar_name += '.tar.bz2'
        tarname = os.path.join(self.dirs['work'], tar_name)
        # print 'tar -cjf %s %s' %(tar_name, tar_dir)
        # print os.getcwd()
        os.chdir(self.dirs['work'])
        # print os.getcwd()
        os.system('tar -cjf %s %s' %(tar_name, tar_dir))

        # Tarball the XDS log files
        lp_name = 'xds_lp_files.tar.bz2'
        # print "tar -cjf %s xds_lp_files/" % lp_name
        os.system("tar -cjf %s xds_lp_files/" % lp_name)
        # Remove xds_lp_files directory
        os.system('rm -rf xds_lp_files')
        # If ramdisks were used, erase files from ram_disks.
        if self.ram_use == True and self.preferences['ram_cleanup'] == True:
            remove_command = 'rm -rf /dev/shm/%s' % self.image_data['image_prefix']
            for node in self.ram_nodes[0]:
                command2 = 'ssh -x %s "%s"' % (node, remove_command)
                p = subprocess.Popen(command2,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                p.wait()

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

        return tmp

    def fixMtz2Sca(self, scafile):
        """
        Corrects the scalepack file generated by mtz2various by removing
        whitespace in the spacegroup name.
        """
        self.logger.debug('FastIntegration::fixMtz2Sca scafile = %s', scafile)
        inlines = open(scafile, 'r').readlines()
        symline = inlines[2]
        newline = (symline[:symline.index(symline.split()[6])]
                   + ''.join(symline.split()[6:]) + '\n')
        inlines[2] = newline
        self.write_file(scafile, inlines)
        return

    def run_analysis(self, data_to_analyze, dir):
        """
        Runs "pdbquery" and xtriage on the integrated data.
        data_to_analyze = the integrated mtzfile
        dir = the working integration directory
        """
        self.logger.debug('FastIntegration::run_analysis')
        self.logger.debug('                 data = %s', data_to_analyze)
        self.logger.debug('                 dir = %s', dir)
        analysis_dir = os.path.join(dir, 'analysis')
        if os.path.isdir(analysis_dir) == False:
            os.mkdir(analysis_dir)
        run_dict = {'fullname'  : self.image_data['fullname'],
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
        pdb_dict['data'] = data_to_analyze
        pdb_dict["plugin_directories"] = self.dirs.get("plugin_directories", False)
        pdb_dict['control'] = self.controller_address
        pdb_dict['process_id'] = self.process_id
        pdb_input.append(pdb_dict)
        self.logger.debug('    Sending pdb_input to Autostats')
        # try:
        T = AutoStats(pdb_input, self.logger)
        self.logger.debug('I KNOW WHO YOU ARE')
        # except:
        #     self.logger.debug('    Execution of AutoStats failed')
        #     return('Failed')
        return "Success"

    def find_xds_symm(self, xdsdir, xdsinp):
        """
        Checks xds results for consistency with user input spacegroup.
        If inconsistent, tries to force user input spacegroup on data.

        Returns new input file for intgration
        """

        # Change to directory
        os.chdir(xdsdir)

        new_inp = self.modify_xdsinput_for_symm(xdsinp, self.spacegroup, "IDXREF.LP")

        # Make sure we end in the right place
        os.chdir(self.dirs['work'])

        return new_inp

    def modify_xdsinput_for_symm(self, xdsinp, sg_num, logfile):
        """
        Modifys the XDS input to rerun integration in user input spacegroup
        """
        sg_num = int(sg_num)

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
        elif sg_num >= 79 <= 80 or sg_num >= 97 <= 98:
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
            # print line
            if bravais in line and '*' in line:
                splitline = line.split()
                # print splitline
                # print splitline[4:]
                break
        cell = ('%s %s %s %s %s %s' % tuple(splitline[4:]))
        xdsinp[-2] = 'JOB=DEFPIX INTEGRATE CORRECT\n\n'
        xdsinp.append('SPACE_GROUP_NUMBER=%d\n' % sg_num)
        xdsinp.append('UNIT_CELL_CONSTANTS=%s\n' % cell)
        # self.write_file('XDS.INP', xdsinp)
        return xdsinp

    def print_results(self, results):
        """Print out results to the terminal"""

        if isinstance(results, dict):

            # Print summary
            summary = results["summary"]
            # pprint(summary)
            self.tprint("  Spacegroup: %s" % summary["scaling_spacegroup"], 99, "white")
            self.tprint("  Unit cell: %5.1f %5.1f %5.1f %5.2f %5.2f %5.2f" %
                        tuple(summary["scaling_unit_cell"]), 99, "white")
            self.tprint("  Mosaicity: %5.3f" % summary["mosaicity"], 99, "white")
            self.tprint("  ISa: %5.2f" % summary["ISa"], 99, "white")
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

    def print_plots(self, results):
        """
        Display plots on the commandline

        Possible titles
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
        """

        # Plot as long as JSON output is not selected
        if self.preferences.get("show_plots", True) and (not self.preferences.get("json", False)):

            plots = results["plots"]

            # Determine the open terminal size
            term_size = os.popen('stty size', 'r').read().split()

            plot_type = "Rmerge vs Frame"
            if plot_type in plots:

                plot_data = plots[plot_type]["data"]
                # plot_params = plots[plot_type]["parameters"]

                # Get each subplot
                raw = False
                # smoothed = False
                for subplot in plot_data:
                    if subplot["parameters"]["linelabel"] == "Rmerge":
                        raw = subplot

                # Determine plot extent
                y_array = numpy.array(raw["series"][0]["ys"])
                y_max = y_array.max() * 1.1
                y_min = 0 # max(0, (y_array.min() - 10))
                x_array = numpy.array(raw["series"][0]["xs"])
                x_max = x_array.max()
                x_min = x_array.min()

                gnuplot = subprocess.Popen(["gnuplot"],
                                           stdin=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                gnuplot.stdin.write("""set term dumb %d,%d
                                       set title 'Rmerge vs. Batch'
                                       set xlabel 'Image #'
                                       set ylabel 'Rmerge' rotate by 90 \n""" %
                                    (int(term_size[1])-20, 30))

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
                    for i, j in zip(xs, ys):
                        gnuplot.stdin.write("%f %f\n" % (i, j))
                    gnuplot.stdin.write("e\n")

                # Now plot!
                gnuplot.stdin.flush()
                time.sleep(2)
                gnuplot.terminate()


    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        self.tprint(rcredits.HEADER,
                    level=99,
                    color="blue")

        programs = ["AIMLESS", "CCP4", "CCTBX", "POINTLESS", "XDS"]
        info_string = rcredits.get_credits_text(programs, "    ")

        self.tprint(info_string, level=99, color="white")

    def write_json(self, results):
        """Write a file with the JSON version of the results"""

        json_string = json.dumps(results)

        # Output to terminal?
        if self.preferences["json"]:
            print json_string

        # Write a file
        with open("result.json", 'w') as outfile:
            outfile.writelines(json_string)


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
        # Instantiate the integration case
        RapdPlugin(None, self.input, self.tprint, self.logger)

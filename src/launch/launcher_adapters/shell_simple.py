"""
Provides a simple launcher adapter that will launch processes in a shell
"""

"""
This file is part of RAPD

Copyright (C) 2016-2021 Cornell University
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

__created__ = "2016-03-02"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import logging
import os
from subprocess import Popen

# RAPD imports
import utils.launch_tools as launch_tools
from utils.modules import load_module

class LauncherAdapter(object):
    """
    An adapter for launcher process.

    Will launch requested job in shell on the current machine
    """

    def __init__(self, site, message, settings):
        """
        Initialize the adapter
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.site = site
        self.message = message
        self.settings = settings

        self.run()

    def run(self):
        """
        Orchestrate the adapter's actions
        """
        # Check if command is ECHO
        if self.message['command'] == 'ECHO':
            # Load the simple_echo module
            echo = load_module(seek_module='launch.launcher_adapters.echo_simple')
            # send message to simple_echo
            echo.LauncherAdapter(self.site, self.message, self.settings)
        else:
            # Adjust the message to this site
            #self.fix_command()
            self.message = launch_tools.fix_command(self.message)
    
            # Put the command into a file
            #command_file = launch_tools.write_command_file(self.settings["launch_dir"],
            command_file = launch_tools.write_command_file(os.path.join(self.settings["launch_dir"],'command_files'),
                                                           self.message["command"],
                                                           self.message)
    
            # Set the site tag from input
            site_tag = launch_tools.get_site_tag(self.message).split('_')[0]
    
            # Call the launch process on the command file
            self.logger.debug("rapd.launch -s %s %s", site_tag, command_file)
            Popen(["rapd.launch", "-s",site_tag, command_file])
            # Can use a queue to get the PID of the launched job
            #Process(target=local_subprocess,
            #        kwargs={"command": "rapd.launch -s %s %s" %(site_tag, command_file)
            #                }).start()

def Launcher_Adapter(site,message,settings):
    # Check if command is ECHO
    if message['command'] == 'ECHO':
        # Load the simple_echo module
        echo = load_module(seek_module='launch.launcher_adapters.echo_simple')
        # send message to simple_echo
        echo.LauncherAdapter(site, message, settings)
    else:
        # Adjust the message to this site
        #self.fix_command()
        message = launch_tools.fix_command(message)

        # Put the command into a file
        command_file = launch_tools.write_command_file(settings["launch_dir"],
                                                       message["command"],
                                                       message)

        # Set the site tag from input
        site_tag = launch_tools.get_site_tag(message).split('_')[0]

        # Call the launch process on the command file
        #self.logger.debug("rapd.launch -s %s %s", site_tag, command_file)
        Popen(["rapd.launch", "-s",site_tag, command_file], shell=True)
        # Can use a queue to get the PID of the launched job
        #Process(target=local_subprocess,
        #        kwargs={"command": "rapd.launch -s %s %s" %(site_tag, command_file)
        #                }).start()


if __name__ == "__main__":
    #import multiprocessing
    #import threading
    #event = multiprocessing.Event()
    #event.set()
    #threading.Thread(target=run_job).start()
    import utils.site
    import importlib
    import utils.log

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    # Get site - commandline wins
    if environmental_vars["RAPD_SITE"]:
        site = environmental_vars["RAPD_SITE"]

    # Determine the site_file
    site_file = utils.site.determine_site(site_arg=site)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Instantiate the logger
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="shell_simple")

    logger.debug("Commandline arguments:")
    
    launcher = {"ip_address": "10.1.255.254", #compute-0-0
                "tag":'shell',
                #"pool_size": 2,
                'adapter': 'shell_simple',
                "job_types":("ALL", ),
                #"job_types":("INDEX", ),
                "site_tag":('NECAT_C', 'NECAT_E'),
                "job_list": 'RAPD_SHELL_JOBS_2',
                'launch_dir': '/gpfs6/users/necat/rapd2'}
    message = {u'preferences': {u'json': False, u'cleanup': False, u'run_mode': u'server'}, u'process': {u'image2_id': False, u'status': 0, u'source': u'server', u'session_id': u'5d0d3df5a1d39d64739db2b4', u'parent_id': False, u'image1_id': u'5d126219f468332e49622984', u'result_id': u'5d126219f468332e49622985'}, u'directories': {u'data_root_dir': u'/gpfs9/users/uci/rjin_E_4463', u'work': u'single/2019-06-25/JIN002_2_PAIR:1', u'launch_dir': u'/gpfs6/users/necat/rapd2', u'plugin_directories': [u'sites.plugins', u'plugins']}, u'command': u'INDEX', u'image1': {u'tau': None, u'run_id': None, u'period': 0.0013333, u'rapd_detector_id': u'necat_dectris_eiger16m', u'sample_mounter_position': u'D2', u'excluded_pixels': None, u'threshold': 6331.0, u'osc_start': None, u'axis': u'omega', u'image_prefix': u'JIN002_2_PAIR', u'size1': 4150, u'size2': 4371, u'osc_range': 1.0, u'site_tag': u'NECAT_E', u'beam_x': 2059.73, u'sensor_thickness': 0.45, u'detector': u'Eiger-16M', u'count_cutoff': 502255, u'trim_file': None, u'md2_aperture': 0.05, u'n_excluded_pixels': 1198784, u'x_beam_size': 0.05, u'data_root_dir': u'/gpfs9/users/uci/rjin_E_4463', u'y_beam_size': 0.02, u'twotheta': 0.0, u'directory': u'/epu/rdma/gpfs9/users/uci/rjin_E_4463/images/Kay/Baohua/snaps/JIN002_2_PAIR_0_000001', u'beam_y': 2191.33, u'wavelength': 0.97918, u'gain': None, u'date': u'2019-06-25T13:04:04.011963', u'run_number_in_template': True, u'detector_sn': u'E-32-0108', u'pixel_size': 0.075, u'y_beam': 154.47975, u'distance': 450.0, u'run_number': 0, u'image_template': u'JIN002_2_PAIR_0_??????.cbf', u'transmission': 10.2, u'collect_mode': u'SNAP', u'flat_field': u'(nil)', u'flux': 510000000000, u'time': 1.0, u'x_beam': 164.34975, u'fullname': u'/epu/rdma/gpfs9/users/uci/rjin_E_4463/images/Kay/Baohua/snaps/JIN002_2_PAIR_0_000001/JIN002_2_PAIR_0_000001.cbf', u'_id': u'5d126219f468332e49622984', u'ring_current': 91.8, u'image_number': 1}, u'site_parameters': {u'DETECTOR_DISTANCE_MAX': 1000.0, u'BEAM_CENTER_Y': [154.638326268, -0.000168035275208, -2.07093201008e-06, 1.46530757459e-09], u'BEAM_APERTURE_SHAPE': u'circle', u'DETECTOR_DISTANCE_MIN': 150.0, u'BEAM_CENTER_DATE': u'2018-10-16', u'DIFFRACTOMETER_OSC_MIN': 0.05, u'BEAM_CENTER_X': [165.515302163, -0.00428244190922, 2.97724490799e-06, 7.48384066914e-10], u'BEAM_SIZE_Y': 0.02, u'BEAM_SIZE_X': 0.05, u'DETECTOR_TIME_MIN': 0.05, u'BEAM_FLUX': 5000000000000.0, u'BEAM_SHAPE': u'ellipse'}}

    
    LAUNCHER_MANAGER = LauncherAdapter(site=SITE,
                                       message=message,
                                       settings=launcher)

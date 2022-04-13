"""
Provides a simple launcher adapter that will launch processes in a shell
"""

"""
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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
    message = {'preferences': {'json': False, 'cleanup': False, 'run_mode': 'server'}, 'process': {'image2_id': False, 'status': 0, 'source': 'server', 'session_id': '5d0d3df5a1d39d64739db2b4', 'parent_id': False, 'image1_id': '5d126219f468332e49622984', 'result_id': '5d126219f468332e49622985'}, 'directories': {'data_root_dir': '/gpfs9/users/uci/rjin_E_4463', 'work': 'single/2019-06-25/JIN002_2_PAIR:1', 'launch_dir': '/gpfs6/users/necat/rapd2', 'plugin_directories': ['sites.plugins', 'plugins']}, 'command': 'INDEX', 'image1': {'tau': None, 'run_id': None, 'period': 0.0013333, 'rapd_detector_id': 'necat_dectris_eiger16m', 'sample_mounter_position': 'D2', 'excluded_pixels': None, 'threshold': 6331.0, 'osc_start': None, 'axis': 'omega', 'image_prefix': 'JIN002_2_PAIR', 'size1': 4150, 'size2': 4371, 'osc_range': 1.0, 'site_tag': 'NECAT_E', 'beam_x': 2059.73, 'sensor_thickness': 0.45, 'detector': 'Eiger-16M', 'count_cutoff': 502255, 'trim_file': None, 'md2_aperture': 0.05, 'n_excluded_pixels': 1198784, 'x_beam_size': 0.05, 'data_root_dir': '/gpfs9/users/uci/rjin_E_4463', 'y_beam_size': 0.02, 'twotheta': 0.0, 'directory': '/epu/rdma/gpfs9/users/uci/rjin_E_4463/images/Kay/Baohua/snaps/JIN002_2_PAIR_0_000001', 'beam_y': 2191.33, 'wavelength': 0.97918, 'gain': None, 'date': '2019-06-25T13:04:04.011963', 'run_number_in_template': True, 'detector_sn': 'E-32-0108', 'pixel_size': 0.075, 'y_beam': 154.47975, 'distance': 450.0, 'run_number': 0, 'image_template': 'JIN002_2_PAIR_0_??????.cbf', 'transmission': 10.2, 'collect_mode': 'SNAP', 'flat_field': '(nil)', 'flux': 510000000000, 'time': 1.0, 'x_beam': 164.34975, 'fullname': '/epu/rdma/gpfs9/users/uci/rjin_E_4463/images/Kay/Baohua/snaps/JIN002_2_PAIR_0_000001/JIN002_2_PAIR_0_000001.cbf', '_id': '5d126219f468332e49622984', 'ring_current': 91.8, 'image_number': 1}, 'site_parameters': {'DETECTOR_DISTANCE_MAX': 1000.0, 'BEAM_CENTER_Y': [154.638326268, -0.000168035275208, -2.07093201008e-06, 1.46530757459e-09], 'BEAM_APERTURE_SHAPE': 'circle', 'DETECTOR_DISTANCE_MIN': 150.0, 'BEAM_CENTER_DATE': '2018-10-16', 'DIFFRACTOMETER_OSC_MIN': 0.05, 'BEAM_CENTER_X': [165.515302163, -0.00428244190922, 2.97724490799e-06, 7.48384066914e-10], 'BEAM_SIZE_Y': 0.02, 'BEAM_SIZE_X': 0.05, 'DETECTOR_TIME_MIN': 0.05, 'BEAM_FLUX': 5000000000000.0, 'BEAM_SHAPE': 'ellipse'}}

    
    LAUNCHER_MANAGER = LauncherAdapter(site=SITE,
                                       message=message,
                                       settings=launcher)

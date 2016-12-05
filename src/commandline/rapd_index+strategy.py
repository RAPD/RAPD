"""
Wrapper for launching an index & strategy on images
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

__created__ = "2016-11-17"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import importlib
import sys

# RAPD imports
# import utils.commandline
import utils.log
# import utils.lock
# import utils.site
import utils.text as text
import commandline_utils
import detectors.detector_utils as detector_utils


def construct_command():
    """
    Put together the command for the agent
    """

    # The task to be carried out
    command = { "command":"AUTOINDEX+STRATEGY" }

    # Where to do the work
    command["directories"] = { "work": os.path.abspath(os.path.curdir) }

    # Image data

    #       "header1":{
    #           #"wavelength": "0.9792", #RADDOSE
    #   	   	"wavelength": 1.000, #RADDOSE
    #   	   	"detector":'ray300',
    #   	   	#"binning": "2x2", #LABELIT
    #   	   	"binning": "none", #
    #   	   	"time": "1.00",  #BEST
    #   	   	"twotheta": "0.00", #LABELIT
    #   	   	"transmission": "20",  #BEST
    #   	   	'osc_range': 1.0,
    #   	   	'distance' : 200.0,
    #   	   	'count_cutoff': 65535,
    #   	   	'omega_start': 0.0,
    #   	   	#"beam_center_x": "216.71", #PILATUS
    #   	   	#"beam_center_y": "222.45", #PILATUS
    #   	   	#"beam_center_x": "150.72", #Q315
    #   	   	#"beam_center_y": "158.68", #Q315
    #   	   	#"beam_center_x": "172.80", #HF4M
    #   	   	#"beam_center_y": "157.18", #HF4M
    #   	   	"beam_center_x": "151.19", #22ID
    #   	        "beam_center_y": "144.82", #22ID
    #   	   	#"beam_center_x": "150.25", #22BM
    #   	   	#"beam_center_y": "151.35", #22BM
    #   	   	"flux":'1.6e11', #RADDOSE
    #   	   	"beam_size_x":"0.07", #RADDOSE
    #   	   	"beam_size_y":"0.03", #RADDOSE
    #   	   	"gauss_x":'0.03', #RADDOSE
    #   	   	"gauss_y":'0.01', #RADDOSE
    #   		"fullname": "/panfs/panfs0.localdomain/archive/ID_16_06_01_staff_test/Se-Tryp_SER16-pn10/SER-16_Pn10_1.0001",
    #   	   	#"fullname": "/panfs/panfs0.localdomain/archive/BM_16_03_03_staff_staff/Tryp/SERX12_Pn1_r1_1.0001",
    #   	   	#"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_23_chrzas/21281_p422x01/image/21281.0001",
    #   	   	#"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_04_chrzas_feb_4_2016/SER4-TRYP_Pn3/SER4-TRYP_Pn3.0001",
    #   	   	#"fullname": "/gpfs6/users/necat/Jon/RAPD_test/Temp/mar/SER4-TRYP_Pn3.0001",
      #
    #   	   	#minikappa
    #   	   	#Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
    #   	   	#"mk3_phi":"0.0", #
    #   	   	#"mk3_kappa":"0.0", #
    #   	   	"phi": "0.000",
    #   	   	"STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
    #   	   	"STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
    #   	   	"axis_align": 'long',	 #long,all,a,b,c,ab,ac,bc #XOAlign
 #  		},
    #       "header2":{#"wavelength": "0.9792", #RADDOSE
 #  	    "wavelength": 1.000, #RADDOSE
 #  	    "detector":'ray300',
 #  	    #"binning": "2x2", #LABELIT
 #  	    "binning": "none", #
 #  	    "time": "1.00",  #BEST
 #  	    "twotheta": "0.00", #LABELIT
 #  	    "transmission": "20",  #BEST
 #  	    'osc_range': 1.0,
 #  	    'distance' : 200.0,
 #  	    'count_cutoff': 65535,
 #  	    'omega_start': 0.0,
 #  	    #"beam_center_x": "216.71", #PILATUS
 #  	    #"beam_center_y": "222.45", #PILATUS
 #  	    #"beam_center_x": "150.72", #Q315
 #  	    #"beam_center_y": "158.68", #Q315
 #  	    #"beam_center_x": "172.80", #HF4M
 #  	    #"beam_center_y": "157.18", #HF4M
 #  	    "beam_center_x": "151.19", #22ID
 #  	    "beam_center_y": "144.82", #22ID
 #  	    #"beam_center_x": "150.25", #22BM
 #  	    #"beam_center_y": "151.35", #22BM
 #  	    "flux":'1.6e11', #RADDOSE
 #  	    "beam_size_x":"0.07", #RADDOSE
 #  	    "beam_size_y":"0.03", #RADDOSE
 #  	    "gauss_x":'0.03', #RADDOSE
 #  	    "gauss_y":'0.01', #RADDOSE
 #  	    "fullname": "/panfs/panfs0.localdomain/archive/ID_16_06_01_staff_test/Se-Tryp_SER16-pn10/SER-16_Pn10_1.0090",
 #  	    #"fullname": "/panfs/panfs0.localdomain/archive/BM_16_03_03_staff_staff/Tryp/SERX12_Pn1_r1_1.0090",
 #  	    #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_23_chrzas/21281_p422x01/image/21281.0020",
 #  	    #"fullname": "/panfs/panfs0.localdomain/archive/ID_16_02_04_chrzas_feb_4_2016/SER4-TRYP_Pn3/SER4-TRYP_Pn3.0050",
 #  	    #"fullname": "/gpfs6/users/necat/Jon/RAPD_test/Temp/mar/SER4-TRYP_Pn3.0050",
      #
 #  	    #minikappa
 #  	    #Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
 #  	    #"mk3_phi":"0.0", #
 #  	    #"mk3_kappa":"0.0", #
 #  	    "phi": "0.000",
 #  	    "STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
 #  	    "STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
 #  	    "axis_align": 'long',    #long,all,a,b,c,ab,ac,bc #XOAlign
 #  	    },
 #  	  "preferences":{"strategy_type": 'best', #Preferred program for strategy
 #  	  		#"strategy_type": 'mosflm', #
 #  	  	  	"crystal_size_x": "100", #RADDOSE
 #  		 	 "crystal_size_y": "100", #RADDOSE
 #  		  	"crystal_size_z": "100", #RADDOSE
 #  			  "shape": "2.0", #BEST
 #  			  "sample_type": "Protein", #LABELIT, BEST
 #  			  "best_complexity": "none", #BEST
 #  			  "susceptibility": "1.0", #BEST
 #  			  "index_hi_res": 0.0, #LABELIT
 #  			  "spacegroup": "None", #LABELIT, BEST, beam_center
 #  			  #"spacegroup": "R3", #
 #  			  "solvent_content": 0.55, #RADDOSE
 #  			  "beam_flip": "False", #NECAT, when x and y are sent reversed.
 #  			  "multiprocessing":"True", #Specifies to use 4 cores to make Autoindex much faster.
 #  			  "x_beam": "0",#Used if position not in header info
 #  			  "y_beam": "0",#Used if position not in header info
 #  			  "aimed_res": 0.0, #BEST to override high res limit
 #  			  "a":0.0, ##LABELIT
 #  			  "b":0.0, ##LABELIT
 #  			  "c":0.0, ##LABELIT
 #  			  "alpha":0.0, #LABELIT
 #  			  "beta":0.0, #LABELIT
 #  			  "gamma":0.0, #LABELIT
      #
 #  			  #Change these if user wants to continue dataset with other crystal(s).
 #  			  "reference_data_id": None, #MOSFLM
 #  			  #"reference_data_id": 1,#MOSFLM
 #  			  #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30','P41212']],#MOSFLM
 #  			  'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',0.0,20.0,'junk','P3'],['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',40.0,50.0,'junk2','P3']],#MOSFLM
 #  			  #MOSFLM settings for multisegment strategy (like give me best 30 degrees to collect). Ignored if "mosflm_rot" !=0.0
 #  			  "mosflm_rot": 0.0, #MOSFLM
 #  			  "mosflm_seg":1, #MOSFLM
 #  			  "mosflm_start":0.0,#MOSFLM
 #  			  "mosflm_end":360.0,#MOSFLM
 #  			  },			     # Settings for calculations
 #  	  "return_address":("127.0.0.1", 50001),      # Location of control process
    #   }


def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Launch an index & strategy on input image(s)"""
    parser = argparse.ArgumentParser(parents=[commandline_utils.dp_parser],
                                     description=commandline_description)

    # Index only
    parser.add_argument("--index_only",
                        action="store",
                        dest="index_only",
                        help="Specify only indexing, no strategy calculation")

    # Strategy type
    parser.add_argument("--strategy_type",
                        action="store",
                        dest="strategy_type",
                        nargs=1,
                        choices=["best", "mosflm"],
                        help="Type of strategy")

    # Complexity of BEST strategy
    parser.add_argument("--best_complexity",
                        action="store",
                        dest="best_complexity",
                        nargs=1,
                        choices=["min", "full"],
                        help="Complexity of BEST strategy")

    # Number of mosflm segments
    parser.add_argument("--mosflm_segments",
                        action="store",
                        dest="mosflm_segments",
                        nargs=1,
                        choices=[1, 2, 3, 4, 5],
                        help="Number of mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_range",
                        action="store",
                        dest="mosflm_range",
                        nargs=1,
                        type=float,
                        help="Rotation range for mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_start",
                        action="store",
                        dest="mosflm_start",
                        nargs=1,
                        type=float,
                        help="Start of allowable rotation range for mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_end",
                        action="store",
                        dest="mosflm_end",
                        nargs=1,
                        type=float,
                        help="End of allowable rotation range for mosflm segments")


    return parser.parse_args()

def main():
    """ The main process
    Setup logging and instantiate the model"""

    # Get the commandline args
    commandline_args = get_commandline()
    # tprint(commandline_args)

    # verbosity
    if commandline_args.verbose:
        verbosity = 5
    else:
        verbosity = 1

    # Set up terminal printer
    tprint = utils.log.get_terminal_printer(verbosity=verbosity)

    # Print out commandline args
    if verbosity > 2:
        tprint("\n" + text.info + "Commandline arguments" + text.stop, 3)
        for key, val in vars(commandline_args).iteritems():
            tprint("  %s : %s" % (key, val), 3)

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    if verbosity > 2:
        tprint("\n" + text.info + "Environmental variables" + text.stop, 3)
        for key, val in environmental_vars.iteritems():
            tprint("  " + key + " : " + val, 3)

    # The data files to be processed
    data_files = commandline_utils.analyze_data_sources(sources=commandline_args.sources,
                                                        mode="index")
    if verbosity > 2:
        tprint("\n" + text.info + "Data files" + text.stop, 3)
        if len(data_files) == 0:
            tprint("  None", 3)
        else:
            for data_file in data_files:
                tprint("  " + data_file, 3)

    # List sites?
    if commandline_args.listsites:
        print "\n" + text.info + "Available sites:" + text.stop
        commandline_utils.print_sites(left_buffer="  ")
        if not commandline_args.listdetectors:
            sys.exit()

    # List detectors?
    if commandline_args.listdetectors:
        print "\n" + text.info + "Available detectors:" + text.stop
        commandline_utils.print_detectors(left_buffer="  ")
        sys.exit()

    # Need data
    if len(data_files) == 0 and commandline_args.test == False:
        raise Exception, "No files input for indexing."

    # Too much data?
    if len(data_files) > 2:
        raise Exception, "Too many files for indexing. 1 or 2 images accepted."

    # Get site - commandline wins over the environmental variable
    site = False
    if commandline_args.site:
        site = commandline_args.site
    elif environmental_vars.has_key("RAPD_SITE"):
        site = environmental_vars["RAPD_SITE"]

    detector = False
    if commandline_args.detector:
        detector = commandline_args.detector
        detector_utils.load_detector(detector)

    # If no site or detector, try to figure out the detector
    if not (site or detector):
        print "Have to figure out the detector"

    # If no site, error
    # if site == False:
    #     print text.error+"Could not determine a site. Exiting."+text.stop
    #     sys.exit(9)

    # Determine the site_file
    # site_file = utils.site.determine_site(site_arg=site)

    # Error out if no site_file to import
    # if site_file == False:
    #     print text.error+"Could not find a site file. Exiting."+text.stop
    #     sys.exit(9)

    # Import the site settings
    # print "Importing %s" % site_file
    # SITE = importlib.import_module(site_file)

	# Single process lock?
    # utils.lock.file_lock(SITE.CONTROL_LOCK_FILE)

    # Set up logging
    # if commandline_args.verbose:
    #     log_level = 10
    # else:
    #     log_level = SITE.LOG_LEVEL
    # logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
    #                               logfile_id="rapd_control",
    #                               level=log_level)
    #
    # logger.debug("Commandline arguments:")
    # for pair in commandline_args._get_kwargs():
    #     logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the model
    # MODEL = Model(SITE=SITE,
    #               overwatch_id=commandline_args.overwatch_id)

if __name__ == "__main__":

	# # Set up terminal printer
    # tprint = utils.log.get_terminal_printer(verbosity=1)

    main()

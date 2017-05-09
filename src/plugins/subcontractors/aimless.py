"""Functions for parsing aimless logs"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
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

__created__ = "2017-05-09"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
import os
# import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
import sys
# import time
# import unittest
# import urllib2
# import uuid

# Import smartie.py from the installed CCP4 package
# smartie.py is a python script for parsing log files from CCP4
sys.path.append(os.path.join(os.environ["CCP4"], "share", "smartie"))
import smartie

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits

# Software dependencies
VERSIONS = {
    # "eiger2cbf": ("160415",)
}

def parse_aimless(logfile):
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
            unit_cell = [try_float(x) for x in line.split()[3:]]
        elif "Anomalous flag switched ON" in line:
            anomalous_report = line

    int_results = {
        "bins_low": [try_float(x) for x in summary[3].split()[-3:]],
        "bins_high": [try_float(x) for x in summary[4].split()[-3:]],
        "rmerge_anom": [try_float(x) for x in summary[6].split()[-3:]],
        "rmerge_norm": [try_float(x) for x in summary[7].split()[-3:]],
        "rmeas_anom": [try_float(x) for x in summary[8].split()[-3:]],
        "rmeas_norm": [try_float(x) for x in summary[9].split()[-3:]],
        "rpim_anom": [try_float(x) for x in summary[10].split()[-3:]],
        "rpim_norm": [try_float(x) for x in summary[11].split()[-3:]],
        "rmerge_top": float(summary[12].split()[-3]),
        "total_obs": [try_int(x) for x in summary[13].split()[-3:]],
        "unique_obs": [try_int(x) for x in summary[14].split()[-3:]],
        "isigi": [try_float(x) for x in summary[15].split()[-3:]],
        "cc-half": [try_float(x) for x in summary[16].split()[-3:]],
        "completeness": [try_float(x) for x in summary[17].split()[-3:]],
        "multiplicity": [try_float(x) for x in summary[18].split()[-3:]],
        "anom_completeness": [try_float(x) for x in summary[20].split()[-3:]],
        "anom_multiplicity": [try_float(x) for x in summary[21].split()[-3:]],
        "anom_correlation": [try_float(x) for x in summary[22].split()[-3:]],
        "anom_slope": [try_float(summary[23].split()[-3])],
        "scaling_spacegroup": space_group,
        "scaling_unit_cell": unit_cell,
        "text2": anomalous_report,
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
        "Rmerge vs Frame": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "Rmerge",
                        "linetype": "11",
                        "linewidth": "3"
                       },
                    "series": [
                        {
                            "xs": [int(x) for x in log.tables(rfactor)[0].col("Batch")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(rfactor)[0].col("Rmerge")]
                            }
                        ]},
                {"parameters": {
                    "linecolor": "4",
                    "linelabel": "SmRmerge",
                    "linetype": "11",
                    "linewidth": "3",
                    },
                 "series": [
                     {"xs" : [try_int(x) for x in log.tables(rfactor)[0].col("Batch")],
                      "ys" : [try_float(x, 0.0) for x in log.tables(rfactor)[0].col("SmRmerge")]
                     }
                 ]
                },
            ],
            "parameters": {
                "toplabel": "Rmerge vs Batch for all Runs",
                "xlabel": "Image Number",
                },
            },
        "Imean/RMS scatter": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "I/rms",
                        "linetype": "11",
                        "linewidth": "3",
                    },
                    "series": [
                        {
                            "xs" : [int(x) for x in log.tables(rfactor)[0].col("N")],
                            "ys" : [try_float(x, 0.0) for x in \
                                   log.tables(rfactor)[0].col("I/rms")],
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "Imean / RMS scatter",
                "xlabel": "Image Number",
            }
        },
        "Anomalous & Imean CCs vs Resolution": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "CCanom",
                        "linetype": "11",
                        "linewidth": "3",
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(cchalf)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(cchalf)[0].col("CCanom")],
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "CC1/2",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(cchalf)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(cchalf)[0].col("CC1/2")],
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "Anomalous & Imean CCs vs. Resolution",
                "xlabel": "Dmid (Angstroms)"
            }
        },
        "RMS correlation ration": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "RCRanom",
                        "linetype": "11",
                        "linewidth": "3",
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(cchalf)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(cchalf)[0].col("RCRanom")]
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "RMS correlation ratio",
                "xlabel": "Dmid (Angstroms)",
            }
        },
        "I/sigma, Mean Mn(I)/sd(Mn(I))": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "I/RMS",
                        "linetype": "11",
                        "linewidth": "3",
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("I/RMS")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "Mn(I/sd)",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("Mn(I/sd)")]
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "I/sigma, Mean Mn(I)/sd(Mn(I))",
                "xlabel": "Dmid (Angstroms)"
            }
        },
        "Rmerge, Rfull, Rmeas, Rpim vs. Resolution": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "Remerge",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("Rmrg")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "Rfull",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("Rfull")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "5",
                        "linelabel": "Rmeas",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("Rmeas")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "6",
                        "linelabel": "Rpim",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("Rpim")]
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "Rmerge, Rfull, Rmeas, Rpim vs. Resolution",
                "xlabel": "Dmid (Angstroms)"
            }
        },
        "Average I, RMS deviation, and Sd": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "Average I",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_int(x, 0) for x in log.tables(vresolution)[0].col("AvI")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "RMS deviation",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("RMSdev")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "5",
                        "linelabel": "std. dev.",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(vresolution)[0].col("sd")]
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "Average I, RMS dev., and std. dev.",
                "xlabel": "Dmid (Ansgstroms)"
            }
        },
        "Completeness": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "%poss",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("%poss")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "C%poss",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("C%poss")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "5",
                        "linelabel": "AnoCmp",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("AnoCmp")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "6",
                        "linelabel": "AnoFrc",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("AnoFrc")]
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "Completeness vs. Resolution",
                "xlabel": "Dmid (Angstroms)"
            }
        },
        "Redundancy": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "multiplicity",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("Mlplct")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "anomalous multiplicity",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("1/d^2")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(completeness)[0].col("AnoMlt")]
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "Redundancy",
                "xlabel": "Dmid (Angstroms)"
            }
        },
        "Radiation Damage": {
            "data": [
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "Rcp",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [int(x) for x in log.tables(rcp)[0].col("Batch")],
                            "ys": [try_float(x, 0.0) for x in log.tables(rcp)[0].col("Rcp")]
                        }
                    ]
                }
            ],
            "parameters": {
                "toplabel": "Rcp vs. Batch",
                "xlabel": "Relative frame difference"
            }
        }
    }

	# Return to the main program.
    return (plots, int_results)

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-c", "--commandline",
                           action="store_true",
                           dest="commandline",
                           help="Generate commandline argument parsing")

    # File name to be generated
    my_parser.add_argument(action="store",
                           dest="file",
                           nargs="?",
                           default=False,
                           help="Name of file to be generated")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        my_parser.print_help()
        my_parser.exit()

    return my_parser.parse_args()

if __name__ == "__main__":

    # Execute code
    main()

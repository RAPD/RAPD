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
from pprint import pprint
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

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits
from utils.r_numbers import try_int, try_float

# Import smartie.py from the installed CCP4 package
# smartie.py is a python script for parsing log files from CCP4
try:
    sys.path.append(os.path.join(os.environ["CCP4"], "share", "smartie"))
except KeyError as e:
    print "\nError importing smartie from CCP4."
    print "Environmental variable %s not set. Exiting." % e
    exit(9)
import smartie

# Software dependencies
VERSIONS = {
    # "eiger2cbf": ("160415",)
}

def parse_aimless(logfile):
    """
	Parses the aimless logfile in order to pull out data for
	graphing and the results summary table.

    logfile should be input as the name of the log file

	Relevant values for the summary table are stored in a dict.
        key = name of result value
        value = list of three numbers,  1 - Overall
                                        2 - Inner Shell
                                        3 - Outer Shell
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
    # anomalous_report = ""
    int_results = {"anomalous_report": ""}
    for line in summary:
        # print line, len(line)
        if "Space group" in line:
            int_results["scaling_spacegroup"] = line.strip().split(": ")[-1]
        elif "Average unit cell" in line:
            int_results["scaling_unit_cell"] = [try_float(x) for x in line.split()[3:]]
        elif "Anomalous flag switched ON" in line:
            int_results["text2"] = line
        elif "Low resolution limit" in line:
            int_results["bins_low"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "High resolution limit" in line:
            int_results["bins_high"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Rmerge" in line and "within" in line:
            int_results["rmerge_anom"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Rmerge" in line and "all" in line:
            int_results["rmerge_norm"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Rmeas" in line and "within" in line:
            int_results["rmeas_anom"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Rmeas" in line and "all" in line:
            int_results["rmeas_norm"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Rpim" in line and "within" in line:
            int_results["rpim_anom"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Rpim" in line and "all" in line:
            int_results["rpim_norm"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Rmerge in top intensity bin" in line:
            int_results["rmerge_top"] = try_float(line.split()[-3], 0)
        elif "Total number of observations" in line:
            int_results["total_obs"] = [try_int(x, 0) for x in line.split()[-3:]]
        elif "Total number unique" in line:
            int_results["unique_obs"] = [try_int(x, 0) for x in line.split()[-3:]]
        elif "Mean((I)/sd(I))" in line:
            int_results["isigi"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Mn(I) half-set correlation CC(1/2)" in line:
            int_results["cc-half"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Completeness" in line:
            int_results["completeness"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Multiplicity" in line:
            int_results["multiplicity"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Anomalous completeness" in line:
            int_results["anom_completeness"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Anomalous multiplicity" in line:
            int_results["anom_multiplicity"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "DelAnom correlation between half-sets" in line:
            int_results["anom_correlation"] = [try_float(x, 0) for x in line.split()[-3:]]
        elif "Mid-Slope of Anom Normal Probability" in line:
            int_results["anom_slope"] = [try_float(x, 0) for x in line.split()[-3:]]

    # This now unused due to shifting output
    # int_results = {
    #     "bins_low":           [try_float(x, 0) for x in summary[3].split()[-3:]],
    #     "bins_high":          [try_float(x, 0) for x in summary[4].split()[-3:]],
    #     "rmerge_anom":        [try_float(x, 0) for x in summary[6].split()[-3:]],
    #     "rmerge_norm":        [try_float(x, 0) for x in summary[7].split()[-3:]],
    #     "rmeas_anom":         [try_float(x, 0) for x in summary[8].split()[-3:]],
    #     "rmeas_norm":         [try_float(x, 0) for x in summary[9].split()[-3:]],
    #     "rpim_anom":          [try_float(x, 0) for x in summary[10].split()[-3:]],
    #     "rpim_norm":          [try_float(x, 0) for x in summary[11].split()[-3:]],
    #     "rmerge_top":         float(summary[12].split()[-3]),
    #     "total_obs":          [try_int(x) for x in summary[13].split()[-3:]],
    #     "unique_obs":         [try_int(x) for x in summary[14].split()[-3:]],
    #     "isigi":              [try_float(x, 0) for x in summary[15].split()[-3:]],
    #     "cc-half":            [try_float(x, 0) for x in summary[16].split()[-3:]],
    #     "completeness":       [try_float(x, 0) for x in summary[17].split()[-3:]],
    #     "multiplicity":       [try_float(x, 0) for x in summary[18].split()[-3:]],
    #     "anom_completeness":  [try_float(x, 0) for x in summary[21].split()[-3:]],
    #     "anom_multiplicity":  [try_float(x, 0) for x in summary[22].split()[-3:]],
    #     "anom_correlation":   [try_float(x, 0) for x in summary[23].split()[-3:]],
    #     "anom_slope":         [try_float(summary[24].split()[-3])],
    #     "scaling_spacegroup": space_group,
    #     "scaling_unit_cell":  unit_cell,
    #     "text2":              anomalous_report,
    #     }
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
    # scales = "=== Scales v rotation"
    rfactor = "Analysis against all Batches"
    cchalf = "Correlations CC(1/2)"
    # anisotropy = "Anisotropy analysis"
    vresolution = "Analysis against resolution,"
    # anomalous = "Analysis against resolution, with & without"
    # rresolution = "Analysis against resolution for each run"
    # intensity = "Analysis against intensity"
    completeness = "Completeness & multiplicity"
    # deviation = "Run 1, standard deviation" # and 2, 3, ...
    # all_deviation = "All runs, standard deviation"
    # effect = "Effect of parameter variance on sd(I)"
    rcp = "Radiation damage"

    # pprint(dir(log))
    # for table in log.tables():
    #     print table.title()

    # Grab plots - None is plot missing
    plots = {}
    try:
        plots["Rmerge vs Frame"] = {
            "x_data": [int(x) for x in \
                       log.tables(rfactor)[0].col("Batch")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(rfactor)[0].col("Rmerge")],
                    "label": "Rmerge",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(rfactor)[0].col("SmRmerge")],
                    "label": "Smoothed",
                    "pointRadius": 0
                }
            ],
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
                            "xs": [int(x) for x in \
                                  log.tables(rfactor)[0].col("Batch")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(rfactor)[0].col("Rmerge")]
                            }
                        ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "SmRmerge",
                        "linetype": "11",
                        "linewidth": "3",
                        },
                    "series": [
                        {
                            "xs": [try_int(x) for x in \
                                  log.tables(rfactor)[0].col("Batch")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(rfactor)[0].col("SmRmerge")]
                        }
                    ]
                },
                {
                    "parameters": {
                        "linecolor": "3",
                        "linelabel": "Rmerge",
                        "linetype": "11",
                        "linewidth": "3"
                    },
                    "series": [
                        {
                            "xs": [int(x) for x in \
                                  log.tables(rfactor)[0].col("Batch")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(rfactor)[0].col("Rmerge")]
                            }
                        ]
                },
                {
                    "parameters": {
                        "linecolor": "4",
                        "linelabel": "SmRmerge",
                        "linetype": "11",
                        "linewidth": "3",
                        },
                    "series": [
                        {
                            "xs": [try_int(x) for x in \
                                  log.tables(rfactor)[0].col("Batch")],
                            "ys": [try_float(x, 0.0) for x in \
                                  log.tables(rfactor)[0].col("SmRmerge")]
                        }
                    ]
                },
            ],
            "parameters": {
                "selectlabel": "Rmerge",
                "toplabel": "Rmerge vs Batch for all Runs",
                "xlabel": "Batch #",
                "ylabel": "Rmerge",
            },
        }
    # Plot not present
    except IndexError:
        plots["Rmerge vs Frame"] = None

    try:
        plots["Imean/RMS scatter"] = {
            "x_data": [int(x) for x in log.tables(rfactor)[0].col("N")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(rfactor)[0].col("I/rms")],
                    "label": "I/rms",
                    "pointRadius": 0
                }
            ],
            # "data": [
            #     {
            #         "parameters": {
            #             "linecolor": "3",
            #             "linelabel": "I/rms",
            #             "linetype": "11",
            #             "linewidth": "3",
            #         },
            #         "series": [
            #             {
            #                 "xs" : [int(x) for x in log.tables(rfactor)[0].col("N")],
            #                 "ys" : [try_float(x, 0.0) for x in \
            #                        log.tables(rfactor)[0].col("I/rms")],
            #             }
            #         ]
            #     }
            # ],
            "parameters": {
                "selectlabel": "Imean/RMS",
                "toplabel": "Imean / RMS scatter",
                "xlabel": "Batch Number",
                "ylabel": "Imean/RMS"
            }
        }
    # Plot not present
    except IndexError:
        plots["Imean/RMS scatter"] = None

    try:
        plots["Anomalous & Imean CCs vs Resolution"] = {
            "x_data": [try_float(x, 0.0) for x in \
                       log.tables(cchalf)[0].col("1/d^2")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(cchalf)[0].col("CCanom")],
                    "label": "CCanom",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(cchalf)[0].col("CC1/2")],
                    "label": "CC1/2",
                    "pointRadius": 0
                }
            ],
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
                "selectlabel": "CC",
                "toplabel": "Anomalous & Imean CCs vs. Resolution",
                "xlabel": "Dmid (Angstroms)",
                "ylabel": "CC"
            }
        }
    # Plot not present
    except IndexError:
        plots["Anomalous & Imean CCs vs Resolution"] = None

    try:
        plots["RMS correlation ratio"] = {
            "x_data": [try_float(x, 0.0) for x in \
                      log.tables(cchalf)[0].col("1/d^2")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                            log.tables(cchalf)[0].col("RCRanom")],
                    "label": "RCRanom",
                    "pointRadius": 0
                }
            ],
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
                "selectlabel": "RCR",
                "toplabel": "RMS correlation ratio",
                "xlabel": "1/d^2",
                "ylabel": "RCR"
            }
        }
    # Plot not present
    except IndexError:
        plots["RMS correlation ratio"] = None

    try:
        plots["I/sigma, Mean Mn(I)/sd(Mn(I))"] = {
            "x_data": [try_float(x, 0.0) for x in \
                       log.tables(vresolution)[0].col("1/d^2")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("Mn(I/sd)")],
                    "label": "Mn(I/sd)",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("I/RMS")],
                    "label": "I/RMS",
                    "pointRadius": 0
                }
            ],
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
                "selectlabel": "I/&sigma;I",
                "toplabel": "I/sigma, Mean Mn(I)/sd(Mn(I))",
                "xlabel": "1/d^2",
                "ylabel": ""
            }
        }
    # Plot not present
    except IndexError:
        plots["I/sigma, Mean Mn(I)/sd(Mn(I))"] = None

    try:
        plots["rs_vs_res"] = {
            "x_data": [try_float(x, 0.0) for x in \
                       log.tables(vresolution)[0].col("1/d^2")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("Rmrg")],
                    "label": "Rmerge",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("Rfull")],
                    "label": "Rfull",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("Rmeas")],
                    "label": "Rmeas",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("Rpim")],
                    "label": "Rpim",
                    "pointRadius": 0
                },
            ],
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
                "selectlabel": "R Factors",
                "toplabel": "Rmerge, Rfull, Rmeas, Rpim vs. Resolution",
                "xlabel": "Dmid (Angstroms)",
                "ylabel": ""
            }
        }
    # Plot not present
    except IndexError:
        plots["rs_vs_res"] = None

    try:
        plots["Average I, RMS deviation, and Sd"] = {
            "x_data": [try_float(x, 0.0) for x in \
                       log.tables(vresolution)[0].col("1/d^2")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("RMSdev")],
                    "label": "RMSdev",
                    "pointRadius": 0
                },
                {
                    "data": [try_int(x, 0) for x in \
                             log.tables(vresolution)[0].col("AvI")],
                    "label": "AvgI",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(vresolution)[0].col("sd")],
                    "label": "SD",
                    "pointRadius": 0
                }
            ],
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
                "selectlabel": "I vs Res",
                "toplabel": "Average I, RMS dev., and std. dev.",
                "xlabel": "Dmid (Ansgstroms)",
                "ylabel": ""
            }
        }
    # Plot not present
    except IndexError:
        plots["Average I, RMS deviation, and Sd"] = None

    try:
        plots["Completeness"] = {
            "x_data": [try_float(x, 0.0) for x in \
                       log.tables(completeness)[0].col("1/d^2")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(completeness)[0].col("%poss")],
                    "label": "All",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                          log.tables(completeness)[0].col("C%poss")],
                    "label": "C%poss",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(completeness)[0].col("AnoCmp")],
                    "label": "AnoCmp",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(completeness)[0].col("AnoFrc")],
                    "label": "AnoFrc",
                    "pointRadius": 0
                }
            ],
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
                "selectlabel": "Completeness",
                "toplabel": "Completeness vs. Resolution",
                "xlabel": "Dmid (Angstroms)",
                "ylabel": "Percent"
            }
        }
    # Plot not present
    except IndexError:
        plots["Completeness"] = None

    try:
        plots["Redundancy"] = {
            "x_data": [try_float(x, 0.0) for x in \
                       log.tables(completeness)[0].col("1/d^2")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(completeness)[0].col("Mlplct")],
                    "label": "All",
                    "pointRadius": 0
                },
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(completeness)[0].col("AnoMlt")],
                    "label": "Anomalous",
                    "pointRadius": 0
                },
            ],
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
                "selectlabel": "Redundancy",
                "toplabel": "Redundancy",
                "xlabel": "Dmid (Angstroms)",
                "ylabel": ""
            }
        }
    # Plot not present
    except IndexError:
        plots["Redundancy"] = None

    try:
        plots["Radiation Damage"] = {
            "x_data": [int(x) for x in \
                       log.tables(rcp)[0].col("Batch")],
            "y_data": [
                {
                    "data": [try_float(x, 0.0) for x in \
                             log.tables(rcp)[0].col("Rcp")],
                    "label": "RCP",
                    "pointRadius": 0
                }
            ],
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
                            "xs": [int(x) for x in \
                                   log.tables(rcp)[0].col("Batch")],
                            "ys": [try_float(x, 0.0) for x in \
                                   log.tables(rcp)[0].col("Rcp")]
                        }
                    ]
                }
            ],
            "parameters": {
                "selectlabel": "RCP",
                "toplabel": "Rcp vs. Batch",
                "xlabel": "Relative frame difference",
                "ylabel": ""
            }
        }
    # Plot not present
    except IndexError:
        plots["Radiation Damage"] = None

    # Return to the main program.
    return (plots, int_results)

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    args = get_commandline()
    print args

    pprint(parse_aimless(args.file))

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Parse an aimless log file"
    parser = argparse.ArgumentParser(description=commandline_description)

    # Directory or files
    parser.add_argument(action="store",
                        dest="file",
                        default=False,
                        help="Template for image files")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        parser.print_help()
        parser.exit()

    return parser.parse_args()

if __name__ == "__main__":

    # Execute code
    main()

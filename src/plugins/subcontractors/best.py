"""Methiods for running BEST"""

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

__created__ = "2017-08-25"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
# import argparse
# import from collections import OrderedDict
# import datetime
from distutils.spawn import find_executable
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
import subprocess
# import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
from utils.r_numbers import try_int, try_float

# Information for BEST detector-inf.dat that may be missing
BEST_INFO = {
    "q4": "q4          q4      188.00 0.0816000 2304 2304   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
    "q4-2x":       "q4-2x       q4-2x   188.00 0.1632000 1152 1152   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
    "q210":        "q210        q210    210.00 0.0512000 4096 4096   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
    "q210-2x":     "q210-2x     q210-2x 210.00 0.1024000 2048 2048   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
    "q315":        "q315        q315    315.00 0.0512000 6144 6144   2.5   0 1.30 0.0 36.0 0.030  512 DC DA 0  0",
    "q315-2x":     "q315-2x     q315-2x 315.00 0.1024000 3072 3072   2.5   0 1.30 0.0 10.0 0.030  512 DC DA 0  0",
    "mar165":      "mar165      mar165  161.95 0.0794140 2048 2048   7.0   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "mar225":      "mar225      mar225  225.00 0.0730000 3072 3072   2.6   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "rax225":      "rax225      rax225  225.00 0.0730000 3072 3072 120.0  60 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "pck225":      "pck225      mar225  225.00 0.0730000 3072 3072   2.6   0 1.40 0.0 10.0 0.035  pck DC DA 0  0",
    "mar325":      "mar325      mar325  325.02 0.0793500 4096 4096   2.6   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "mar2300":     "mar2300     mpck150 345.00 0.1500000 2300 2300  80.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "image2300":   "image2300   mimg150 345.00 0.1500000 2300 2300  80.0   0 1.30 0.0 10.0 0.045 4600 AD AB 1  1",
    "mar2000":     "mar2000     mpck150 300.00 0.1500000 2000 2000  66.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "image2000":   "image2000   mimg150 300.00 0.1500000 2000 2000  66.0   0 1.30 0.0 10.0 0.045 4000 AD AB 1  1",
    "mar1600":     "mar1600     mpck150 240.00 0.1500000 1600 1600  48.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "image1600":   "image1600   mimg150 240.00 0.1500000 1600 1600  48.0   0 1.30 0.0 10.0 0.045 3200 AD AB 1  1",
    "mar1200":     "mar1200     mpck150 180.00 0.1500000 1200 1200  34.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "image1200":   "image1200   mimg150 180.00 0.1500000 1200 1200  34.0   0 1.30 0.0 10.0 0.045 2400 AD AB 1  1",
    "mar3450":     "mar3450     mpck100 345.00 0.1000000 3450 3450 108.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "image3450":   "image3450   mimg100 345.00 0.1000000 3450 3450 108.0   0 1.30 0.0 10.0 0.045 6900 AD AB 1  1",
    "mar3000":     "mar3000     mpck100 300.00 0.1000000 3000 3000  87.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "image3000":   "image3000   mimg100 300.00 0.1000000 3000 3000  87.0   0 1.30 0.0 10.0 0.045 6000 AD AB 1  1",
    "mar2400":     "mar2400     mpck100 240.00 0.1000000 2400 2400  62.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "image2400":   "image2400   mimg100 240.00 0.1000000 2400 2400  62.0   0 1.30 0.0 10.0 0.045 4800 AD AB 1  1",
    "mar1800":     "mar1800     mpck100 180.00 0.1000000 1800 1800  42.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
    "mx300":       "mx300       mar300  300.00 0.0730000 8192 8192   2.6   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "mx300hs":     "mx300hs     mar300  300.00 0.0781250 3840 3840 0.001   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "image1800":   "image1800   mimg100 180.00 0.1000000 1800 1800  42.0   0 1.30 0.0 10.0 0.045 3600 AD AB 1  1",
    "raxis":       "raxis       raxis   300.00 0.1000000 3000 2990 180.0  60 1.30 0.0 17.0 0.045 6000 DC DA 1  0",
    "ESRF_ID14-1": "ESRF_ID14-1 q210    209.72 0.102400  2048 2048  2.6   0 1.50 0.0 20.0 0.035  512 DC DA 0  0",
    "ESRF_ID14-2": "ESRF_ID14-2 q4      188.01 0.081600  2304 2304  2.6   0 1.50 0.0 20.0 0.035  512 DC DA 0  0",
    "ESRF_ID14-3": "ESRF_ID14-3 q4r     188.01 0.081600  2304 2304  2.6   0 1.50 0.0 20.0 0.035  512 DC DA 0  0",
    "ESRF_ID14-4": "ESRF_ID14-4 q315    315.15 0.102588  3072 3072  2.5   0 1.50 0.0 39.0 0.050  512 DC DA 0  0",
    "ESRF_BM14":   "ESRF_BM14   mar225  224.84 0.073190  3072 3072  4.2   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "ESRF_ID23-1": "ESRF_ID23-1 q315    315.15 0.102588  3072 3072  2.5   0 1.50 0.0 40.0 0.050  512 DC DA 0  0",
    "ESRF_ID23-2": "ESRF_ID23-2 mar225  225.04 0.073254  3072 3072  3.0   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "ESRF_ID29":   "ESRF_ID29   q315    315.00 0.102588  3072 3072  2.5   0 1.50 0.0 40.0 0.050  512 DC DA 0  0",
    "pilatus6m":   "pilatus6m   6m      434.64 0.172000  2463 2527  0.004 0 0.50 0.0  0.0 0.030  pck DC DA 0  0",
    "pilatus2m":   "pilatus2m   2m      254.00 0.172000  1475 1679  0.004 0 0.50 0.0  0.0 0.020  pck DC DA 0  0",
    "eiger9m":     "eiger9m     9m      245.20 0.075000  3110 3269  0.000003  0 0.50 0.0  0.0 0.030  pck DC DA 0  0",
    "eiger16m":    "eiger16m    16m     327.80 0.075000  4150 4371  0.000003  0 0.50 0.0  0.0 0.030  pck DC DA 0  0",
    "eiger2-16m":  "eiger2-16m  2-16m   327.80 0.075000  4148 4362  0.0000001 0 0.50 0.0  0.0 0.030  pck DC DA 0  0",
}

def get_best_version():
    """
    Returns the version of Best that is to be run
    """

    p = subprocess.Popen(["best"],
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, __ = p.communicate()

    # Parse for version information
    version = False
    for line in stdout.split("\n"):
        if line.startswith(" Version"):
            version = line.split()[1]
            break

    return version


def check_best_detector(detector, tprint=False):
    """Check that the detector we need is in the BEST configuration file"""

    best_executable = find_executable("best")

    # the detector-inf.dat could be a couple places
    # With the executable
    loc1 = os.path.join(os.path.dirname(best_executable), "detector-inf.dat")
    # In the SBGRID hiding place
    loc2 = os.path.sep.join(best_executable.split(os.path.sep)[:3]+["best", get_best_version(), "detector-inf.dat"])

    # Read the detector info file to see if the detector is in it
    for location in (loc1, loc2):
        if os.path.exists(location):
            lines = open(location, "r").readlines()
            found = False
            for line in lines:
                if line.startswith(detector+" "):
                    found = True
                    break
                elif line.startswith("end"):
                    break
            break

    if not found:
        if tprint:
            tprint(arg="!!!",
                   level=30,
                   color="red")
            tprint(arg="!!! Detector %s missing from the BEST detector information file !!!" %
                   detector,
                   level=30,
                   color="red")
            tprint(arg="Add \"%s\" \n to file %s to get BEST running" %
                   (BEST_INFO[detector], location),
                   level=30,
                   color="red")
            tprint(arg="!!!",
                   level=30,
                   color="red")

    return found

def parse_best_plots(inp):
    """Parse Best plots file for plots"""

    # Definitions for the expected values
    cast_vals = {
        "Relative Error and Intensity Plot": {
            "Rel.Error": {"x": try_float, "y": try_float},
            "Rel.Intensity": {"x": try_float, "y": try_float},
        },
        "Wilson Plot": {
            "Theory": {"x": try_float, "y": try_float},
            "Experiment": {"x": try_float, "y": try_float},
            "Pred.low errors": {"x": try_float, "y": try_float},
            "Pred.high errors": {"x": try_float, "y": try_float},
        },
        "Maximal oscillation width": {
            "resol": {"x": try_int, "y": try_float},
            "linelabel": (lambda x: x.replace("resol.  ", "")+"A"),
        },
        "Minimal oscillation ranges for different completenesses": {
            "compl": {"x": try_float, "y": try_int},
            "linelabel": (lambda x: x.replace("compl -", "").replace(".%", "%")),
        },
        "Total exposure time vs resolution": {
            "Expon.trend": {"x": try_float, "y": try_float},
            "Predictions": {"x": try_float, "y": try_float}
        },
        "Average background intensity per second": {
            "Background": {"x": try_float, "y": try_float},
            "Predictions": {"x": try_float, "y": try_float}
        },
        "Intensity decrease due to radiation damage": {
            "Rel.Intensity": {"x": try_float, "y": try_float},
            "resol": {"x": try_float, "y": try_float}
        },
        "Rdamage vs.cumulative exposure time": {
            "R-factor": {"x": try_float, "y": try_float},
            "resol": {"x": try_float, "y": try_float}
        }
    }

    # The final product
    parsed_plots = {}
    # Each plot in the file
    plot = False
    # Each curve
    curve_x = False
    curve_y = False
    # Is the loop in a curve?
    in_curve = False

    # Go through the lines
    for line in inp:
        line = line.strip()

        # Start of a plot
        if line.startswith("$"):
            # print line
            # Save the plot is we are transitioning to a new plot
            if plot:
                # If this is not the first plot, the curve needs to be saved
                if curve_x:
                    # print "  save curve"
                    # Remove the raw_label from the curve parameters
                    __ = curve_y.pop("raw_label", None)
                    # Save the y data
                    plot["y_data"].append(curve_y)
                    # Save the x data
                    if not plot["x_data"]:
                        plot["x_data"] = curve_x
                # print "  save plot"
                parsed_plots[plot["parameters"]["toplabel"]] = plot

            # Not in a curve
            in_curve = False
            curve_y = False
            curve_x = False

            # Create a new plot
            plot = {"y_data": [],
                    "x_data": False,
                    "parameters": {},
                   }

        elif line.startswith("%"):
            # print line
            strip_line = line[1:].strip()
            key = strip_line[:strip_line.index("=")].strip()
            val = strip_line[strip_line.index("=")+1:].replace("'", "").strip()

            # If in a curve, then these are curve parameters
            if in_curve:
                # linelabel is a special label because it is displayed to users
                if key == "linelabel":
                    curve_y["raw_label"] = val
                    # If the label is massaged, do so
                    if "linelabel" in cast_vals[plot["parameters"]["toplabel"]]:
                        curve_y["label"] = cast_vals[plot["parameters"]["toplabel"]]["linelabel"](val)
                    else:
                        curve_y["label"] = val
            # Not in a curve, so plot parameters
            else:
                plot["parameters"][key] = val
                # print key, val

        # A new curve has been found
        elif line.startswith("#"):
            # print line
            # If this is not the first curve for the plot, save the curve now
            if curve_x:
                # print "  save curve"
                # Remove the raw_label from the curve parameters
                __ = curve_y.pop("raw_label", None)
                # Save the y data
                plot["y_data"].append(curve_y)
                # Save the x data
                if not plot["x_data"]:
                    plot["x_data"] = curve_x
            in_curve = True
            # curve = {"parameters": {}, "series": [{"xs": [], "ys": []}]}
            curve_y = {"data": [], "label": False}
            curve_x = []


        elif len(line) > 0:
            split_line = line.split()

            # print curve_y["raw_label"]
            if curve_y["raw_label"].startswith("resol"):
                x = cast_vals[plot["parameters"]["toplabel"]]["resol"]["x"](split_line[0].strip())
                y = cast_vals[plot["parameters"]["toplabel"]]["resol"]["y"](split_line[1].strip())
            elif curve_y["raw_label"].startswith("compl"):
                x = cast_vals[plot["parameters"]["toplabel"]]["compl"]["x"](split_line[0].strip())
                y = cast_vals[plot["parameters"]["toplabel"]]["compl"]["y"](split_line[1].strip())
            else:
                x = cast_vals[plot["parameters"]["toplabel"]][curve_y["raw_label"]]["x"](split_line[0].strip())
                y = cast_vals[plot["parameters"]["toplabel"]][curve_y["raw_label"]]["y"](split_line[1].strip())

            curve_x.append(x)
            curve_y["data"].append(y)

    # Run to the end of the file
    # print "  save curve"
    __ = curve_y.pop("raw_label", None)
    plot["y_data"].append(curve_y)
    if not plot["x_data"]:
        plot["x_data"] = curve_x
        # print "  save plot"
    parsed_plots[plot["parameters"]["toplabel"]] = plot

    output = {
        "wilson": parsed_plots["Wilson Plot"],
        "max_delta_omega": parsed_plots.get("Maximal oscillation width", False),
        "rad_damage": parsed_plots.get("Relative Error and Intensity Plot", False),
        "exposure": parsed_plots.get("Total exposure time vs resolution", False),
        "background": parsed_plots.get("Average background intensity per second", False),
        #   "rad_damage_int_decr": rad_damage_int_decr,
        #   "rad_damage_rfactor_incr": rad_damage_rfactor_incr,
        "osc_range": parsed_plots.get("Minimal oscillation ranges for different completenesses", False)}

    # pprint(output)
    return output

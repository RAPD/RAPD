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
# import glob
# import json
# import logging
# import multiprocessing
# import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
# import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
from utils.r_numbers import try_int, try_float

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
                print key, val

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

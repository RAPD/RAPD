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
# import pprint
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

def parse_best_plots(inp):
    """Parse Best plots file for plots"""

    # self.logger.debug("Parse::ParseOutputBestPlots")

    print "ParseOutputBestPlots"

    # Definitions for the expected values
    cast_vals = {
        "Relative Error and Intensity Plot": {
            "Rel.Error": {"x": try_float, "y": try_float},
            "Rel.Intensity": {"x": try_float, "y": try_float}
        },
        "Wilson Plot": {
            "Theory": {"x": try_float, "y": try_float},
            "Experiment": {"x": try_float, "y": try_float},
            "Pred.low errors": {"x": try_float, "y": try_float},
            "Pred.high errors": {"x": try_float, "y": try_float}
        },
        "Maximal oscillation width": {
            "resol": {"x": try_int, "y": try_float},
            "linelabel": (lambda x: x.replace("resol.  ", "")+"A")
        },
        "Minimal oscillation ranges for different completenesses": {
            "compl": {"x": try_float, "y": try_int},
            "linelabel": (lambda x: x.replace("compl -", "").replace(".%", "%"))
        },
        # "Minimal oscillation ranges for different completenesses": {
        #     "compl": {"x": try_float, "y": try_int}
        # },
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

    new_parsed_plots = {}
    new_plot = False
    new_curve = False
    in_curve = False
    parsed_plots = {}
    plot = False
    curve = False
    for line in inp:
        line = line.strip()
        # print line
        if line.startswith("$"):
            if plot:
                parsed_plots[plot["parameters"]["toplabel"]] = plot
                new_parsed_plots[new_plot["parameters"]["toplabel"]] = new_plot
            if curve:
                plot["data"].append(curve)
                curve = False
                new_curve_y = False
                new_curve_x = False

            in_curve = False
            plot = {"parameters": {}, "data": []}
            new_plot = {"y_data": [],
                        "x_data": False,
                        "parameters": {}}

        elif line.startswith("%"):
            strip_line = line[1:].strip()
            key = strip_line[:strip_line.index("=")].strip()
            val = strip_line[strip_line.index("=")+1:].replace("'", "").strip()
            if in_curve:
                curve["parameters"][key] = val
                if key == "linelabel":
                    # print new_plot["parameters"]["toplabel"], "cast_vals keys", cast_vals[new_plot["parameters"]["toplabel"]].keys()
                    if "linelabel" in cast_vals[new_plot["parameters"]["toplabel"]]:
                        new_curve_y["label"] = cast_vals[new_plot["parameters"]["toplabel"]]["linelabel"](val)
                    else:
                        new_curve_y["label"] = val
                    # print val, ">>>", new_curve_y["label"]
            else:
                plot["parameters"][key] = val
                new_plot["parameters"][key] = val

        elif line.startswith("#"):
            if curve:
                plot["data"].append(curve)
                new_plot["y_data"].append(new_curve_y)
                if not new_plot["x_data"]:
                    new_plot["x_data"] = new_curve_x
            in_curve = True
            curve = {"parameters": {}, "series": [{"xs": [], "ys": []}]}
            new_curve_y = {"data": [], "label": False}
            new_curve_x = []


        elif len(line) > 0:
            # print line

            split_line = line.split()

            # print curve["parameters"]["linelabel"]
            if curve["parameters"]["linelabel"].startswith("resol"):
                x = cast_vals[plot["parameters"]["toplabel"]]["resol"]["x"](split_line[0].strip())
                y = cast_vals[plot["parameters"]["toplabel"]]["resol"]["y"](split_line[1].strip())
            elif curve["parameters"]["linelabel"].startswith("compl"):
                x = cast_vals[plot["parameters"]["toplabel"]]["compl"]["x"](split_line[0].strip())
                y = cast_vals[plot["parameters"]["toplabel"]]["compl"]["y"](split_line[1].strip())
            else:
                x = cast_vals[plot["parameters"]["toplabel"]][curve["parameters"]["linelabel"]]["x"](split_line[0].strip())
                y = cast_vals[plot["parameters"]["toplabel"]][curve["parameters"]["linelabel"]]["y"](split_line[1].strip())

            curve["series"][0]["xs"].append(x)
            curve["series"][0]["ys"].append(y)
            new_curve_x.append(x)
            new_curve_y["data"].append(y)

    plot["data"].append(curve)
    # pprint(plot)

    new_plot["y_data"].append(new_curve_y)
    if not new_plot["x_data"]:
        new_plot["x_data"] = new_curve_x
    # pprint(new_plot)
    # sys.exit()

    parsed_plots[plot["parameters"]["toplabel"]] = plot
    new_parsed_plots[new_plot["parameters"]["toplabel"]] = new_plot
    # pprint.pprint(parsed_plots)

    output = {
        "wilson": parsed_plots["Wilson Plot"],
        "max_delta_omega": parsed_plots.get("Maximal oscillation width", False),
        "rad_damage": parsed_plots.get("Relative Error and Intensity Plot", False),
        "exposure": parsed_plots.get("Total exposure time vs resolution", False),
        "background": parsed_plots.get("Average background intensity per second", False),
        #   "rad_damage_int_decr": rad_damage_int_decr,
        #   "rad_damage_rfactor_incr": rad_damage_rfactor_incr,
        "osc_range": parsed_plots.get("Minimal oscillation ranges for different completenesses", False)}

    new_output = {
        "wilson": new_parsed_plots["Wilson Plot"],
        "max_delta_omega": new_parsed_plots.get("Maximal oscillation width", False),
        "rad_damage": new_parsed_plots.get("Relative Error and Intensity Plot", False),
        "exposure": new_parsed_plots.get("Total exposure time vs resolution", False),
        "background": new_parsed_plots.get("Average background intensity per second", False),
        #   "rad_damage_int_decr": rad_damage_int_decr,
        #   "rad_damage_rfactor_incr": rad_damage_rfactor_incr,
        "osc_range": new_parsed_plots.get("Minimal oscillation ranges for different completenesses", False)}

    # pprint(output["osc_range"])
    # pprint(new_output["osc_range"])
    # sys.exit()
    return output, new_output

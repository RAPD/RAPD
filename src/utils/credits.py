"""Helpers for printing out credits for software use"""

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

__created__ = "2017-04-24"
__maintainer__ = "YFrank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import sys

CCTBX = [
    "CCTBX - Computational Crystallography Toolbox",
    "Reference: Grosse-Kunstleve et al. (2002) J. Appl. Cryst. 35:126-136",
    "Website: https://cctbx.github.io/\n"
]

PHASER = [
    "Phaser",
    "Reference: McCoy AJ, et al. (2007) J. Appl. Cryst. 40:658-674",
    "Website: http://www.phenix-online.org/documentation/phaser.htm\n"
]

PHENIX = [
    "Phenix",
    "Reference: Sauter NK, et al. (2004) J. Appl. Cryst. 37:399-409",
    "Website:   http://adder.lbl.gov/labelit/\n",
]

MAIN_MODULE = sys.modules[__name__]

def get_credit(requested_program="PHENIX"):
    """Return credit lines for requested program"""
    return getattr(MAIN_MODULE, requested_program.upper())

def get_credits_text(programs, indent=""):
    """Return text for printing out credits"""

    return_text = ""

    for program in programs:
        raw_lines = get_credit(program.upper())
        for line in raw_lines:
            return_text += (indent + line + "\n")

    return return_text

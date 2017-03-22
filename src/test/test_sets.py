"""Listing of available test data sets"""

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

__created__ = "2017-03-20"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

DATA_SERVER = "https://rapd.nec.aps.anl.gov/rapd/test_data/"

DATA_SETS = {
    "APS_NECAT_24-ID-C": {
        "description": "NE-CAT Pilatus 6M data",
        "integrate_template": "thaum1_01s-01d_1_####.cbf",
        "location": "APS_NECAT_24-ID-C.tar.bz2"
    },
    "APS_NECAT_24-ID-E": {
        "description": "NE-CAT EigerX 18M data",
        "location": "APS_NECAT_24-ID-E.tar.bz2"
    },
    "MINIMAL": {
        "description": "Minimal dataset from NE-CAT 24-ID-E to test system quickly",
        "location": "MINIMAL.tar.bz2"
    },
    "UCLA": {
        "location": "UCLA",
        "integrate_template": "prok_pcmbs_margot####.osc"
    },
    "ALL":{
        "location": None
    },
    "DEPENDENCIES": {
        "location": None
    },
}

PLUGINS = {
    "all": True,
    "index": "plugins.index",
    "integrate": "plugins.integrate",
    }

"""
List of detectors understood by RAPD
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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

__created__ = "2016-11-18"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

DETECTORS = {
    ("ADSC", 413): "",                          # ESRF ID14-2
    ("ADSC", 430): "",                          #
    ("ADSC", 446): "adsc_q315",                 # NSLS X25 > X26C
    ("Pilatus-6M", "PILATUS 6M-F S/N 60-0112-F"): {
        "detector": "necat_dectris_pilatus6mf",
        # "site": 'necat_c'
        },
    ("ADSC", 911): {
        "detector": "necat_adsc_q315"           # APS 24-ID-C
        },
    ("ADSC", 916): {
        "detector": "necat_adsc_q315",           # APS 24-ID-E
        # "site": "necat_e"
        },
    ("MARCCD", 0): ["lscat_mar_300",],          # APS 21-ID-F
    ("MARCCD", 3): {
        "detector": "sercat_rayonix_mx225",
        },      # APS 22BM
    ("MARCCD", 101): {                          # APS 22ID
        "detector": "sercat_rayonix_mx300hs",
        "site": "sercat_id"
        }
}

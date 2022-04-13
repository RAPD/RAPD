"""
Spacegroup Utilities
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2017-2018, Cornell University
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
__created__ = "2017-03-13"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
# import os
from pprint import pprint
# import shutil
# import subprocess
# import sys

bravais   = ['1', '5', '3', '22', '23', '21', '16', '79', '75', '143', '146', '196', '197', '195']

xds_bravais_types = {
    "aP": (1,),
    "mP": (3, 4),
    "mC": (5,),
    "mI": (5,),
    "oP": (16, 17, 18, 19),
    "oC": (20, 21),
    "oF": (22,),
    "oI": (23, 24),
    "tP": (75, 76, 77, 78, 89, 90, 91, 92, 93, 94, 95, 96),
    "tI": (79, 80, 97, 98),
    "hP": (
        143,
        144,
        145,
        149,
        150,
        151,
        152,
        153,
        154,
        168,
        169,
        170,
        171,
        172,
        173,
        177,
        178,
        179,
        180,
        181,
        182,
        ),
    "hR": (146, 155),
    "cP": (195, 198, 207, 208, 212, 213),
    "cF": (196, 209, 210),
    "cI": (197, 199, 211, 214)
}

# Reverse lookup for
intl_to_xds_bravais_type = {}
for key, val in xds_bravais_types.items():
    for sg in val:
        if not sg in intl_to_xds_bravais_type:
            intl_to_xds_bravais_type[sg] = ()
        intl_to_xds_bravais_type[sg] += (key,)

subgroups = {"1": [None],
             "5": [None],
             "3": [4],
             "22": [None],
             "23": [24],
             21: [20],
             16: [17, 18, 19],
             79: [80, 97, 98],
             75: [76, 77, 78, 89, 90, 91, 95, 94, 93, 92, 96],
             143: [144,
                   145,
                   149,
                   151,
                   153,
                   150,
                   152,
                   154,
                   168,
                   169,
                   170,
                   171,
                   172,
                   173,
                   177,
                   178,
                   179,
                   180,
                   181,
                   182],
             146: [155],
             196: [None],
             209: [210],
             197: [199],
             211: [214],
             195: [198],
             207: [208, 212, 213],
             }

# Convert from number representation to Letters
intl2std =   {"1": 'P1',      #* Bravais
              "3": 'P2',      #*
              "4": 'P21',
              "5": 'C2',      #*
            #   "5.1": "I121",
            #   "5.2": "A121",  #2005
            #   "5.3": "A112",
            #   "5.4": "B112",  #1005
            #   "5.5": "I112",  #4005
              "16": 'P222',    #*
              "17": 'P2221',
            #   "17.1": "P2212",  #2017
            #   "17.2": "P2122",  #1017
              "18": 'P21212',
            #   "18.1": "P21221", #2018
            #   "18.2": "P22121", #3018
              "19": 'P212121',
              "20": 'C2221',
              "21": 'C222',    #*
              "22": 'F222',    #*
              "23": 'I222',    #*
              "24": 'I212121',
              "75": 'P4',      #*
              "76": 'P41',
              "77": 'P42',
              "78": 'P43',
              "79": 'I4',      #*
              "80": 'I41',
              "89": 'P422',
              "90": 'P4212',
              "91": 'P4122',
              "92": 'P41212',
              "93": 'P4222',
              "94": 'P42212',
              "95": 'P4322',
              "96": 'P43212',
              "97": 'I422',
              "98": 'I4122',
              "143": 'P3',      #*
              "144": 'P31',
              "145": 'P32',
              "146": 'R3',      #*
            #   "146.1": "R3", #1146
            #   "146.2": "H3", #146
              "149": 'P312',
              "150": 'P321',
              "151": 'P3112',
              "152": 'P3121',
              "153": 'P3212',
              "154": 'P3221',
              "155": 'R32',
            #   "155.1": "R32", #1155
            #   "155.2": "H32", #155
              "168": 'P6',
              "169": 'P61',
              "170": 'P65',
              "171": 'P62',
              "172": 'P64',
              "173": 'P63',
              "177": 'P622',
              "178": 'P6122',
              "179": 'P6522',
              "180": 'P6222',
              "181": 'P6422',
              "182": 'P6322',
              "195": 'P23',     #*
              "196": 'F23',     #*
              "197": 'I23',     #*
              "198": 'P213',
              "199": 'I213',
              "207": 'P432',
              "208": 'P4232',
              "209": 'F432',
              "210": 'F4132',
              "211": 'I432',
              "212": 'P4332',
              "213": 'P4132',
              "214": 'I4132',
               }

intl2std_extra = intl2std.update({
    "5.1": "I121",
    "5.2": "A121",      #2005
    "5.3": "A112",
    "5.4": "B112",      #1005
    "5.5": "I112",      #4005
    "17.1": "P2212",    #2017
    "17.2": "P2122",    #1017
    "18.1": "P21221",   #2018
    "18.2": "P22121",   #3018
    "146.1": "R3",      #1146
    "146.2": "H3",      #146
    "155.1": "R32",     #1155
    "155.2": "H32",     #155
})

std2intl = dict((value,key) for key, value in intl2std.items())

std_sgs = ['None','P1','C2','P2','P21','F222','I222','I212121','C222','C2221','P222',
           'P2221','P21212','P212121','I4','I41','I422','I4122','P4','P41','P42','P43',
           'P422','P4212','P4122','P4322','P4222','P42212','P41212','P43212','P3','P31',
           'P32', 'P312','P3112','P3212','P321','P3121','P3221','P6','P61','P65','P62',
           'P64','P63','P622','P6122','P6522','P6222','P6422','P6322','R3','R32','F23',
           'F432','F4132','I23','I213','I432','I4132','P23''P213''P432','P4232','P4332',
           'P4132']



# from __future__ import division
from iotbx.mtz import extract_from_symmetry_lib
from cctbx import sgtbx
from libtbx.utils import format_cpu_times
import libtbx
import sys, os
op = os.path

try:
  import ccp4io_adaptbx
except ImportError:
  ccp4io_adaptbx = None

def build_ccp4_symmetry_table():

    symbol_to_number = {}
    ccp4_to_number = {}

    # Open file
    file_iter = open(op.join(
        extract_from_symmetry_lib.ccp4io_lib_data, "symop.lib"))
    ccp4_id_counts = libtbx.dict_with_default_0()
    ccp4_symbol_counts = libtbx.dict_with_default_0()

    # Run through the file
    for line in file_iter:
        # print "\n", line.rstrip()
        flds = line.split(None, 4)
        ccp4_id = flds[0]
        ccp4_id_counts[ccp4_id] += 1
        space_group_number = int(ccp4_id[-3:])
        order_z = int(flds[1])
        given_ccp4_symbol = flds[3]


        symbol_to_number[given_ccp4_symbol] = space_group_number

        ccp4_symbol_counts[given_ccp4_symbol] += 1
        group = extract_from_symmetry_lib.collect_symops(
          file_iter=file_iter, order_z=order_z)
        assert group.order_z() == order_z
        space_group_info = sgtbx.space_group_info(group=group)
        retrieved_ccp4_symbol = extract_from_symmetry_lib.ccp4_symbol(
          space_group_info=space_group_info,
          lib_name="symop.lib")
        # print "retrieved_ccp4_symbol", retrieved_ccp4_symbol
        assert retrieved_ccp4_symbol == given_ccp4_symbol
        assert space_group_info.type().number() == space_group_number
        if (1):
            from iotbx.pdb import format_cryst1_sgroup
            sgroup = format_cryst1_sgroup(space_group_info=space_group_info)
            # if (len(sgroup) > 11):
            #     print "ccp4 symop.lib setting leads to pdb CRYST1 overflow:",\
            #       ccp4_id, given_ccp4_symbol, sgroup
            # print "sgroup", sgroup
            ccp4_to_number[sgroup] = space_group_number
    # for ccp4_id,count in ccp4_id_counts.items():
    #     if (count != 1):
    #         raise RuntimeError(
    #             'ccp4 id "%s" appears %d times (should be unique).'
    #               % (ccp4_id, count))
    # ccp4_symbol_counts = libtbx.dict_with_default_0()
    # for ccp4_symbol,count in ccp4_symbol_counts.items():
    #     if (count != 1):
    #         raise RuntimeError(
    #             'ccp4 symbol "%s" appears %d times (should be unique).'
    #               % (ccp4_symbol, count))
    return (symbol_to_number, ccp4_to_number)

symbol_to_number, ccp4_to_number = build_ccp4_symmetry_table()

# Reverse lookup for
number_to_ccp4 = {}
for key, val in ccp4_to_number.items():
    number_to_ccp4[val] = key

def get_subgroups(inp):
    """Returns a list of subgroups for a given input Bravais lattice"""

    return subgroups[inp]



if __name__ == "__main__":
    symbol_to_number, ccp4_to_number = build_ccp4_symmetry_table()
    pprint(ccp4_to_number)

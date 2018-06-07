"""
rapd_utils has a number of useful dicts and functions used in rapd
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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
__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import os
#from pprint import pprint
#import shutil
#import subprocess
#import sys

#from utils.text import json
#from bson.objectid import ObjectId
from utils.xutils import convert_unicode, fix_R3_sg

from plugins.subcontractors.rapd_phaser import run_phaser_module
#import plugins.subcontractors.rapd_phaser as rapd_phaser


from iotbx import mtz as iotbx_mtz
from iotbx import pdb as iotbx_pdb
import iotbx.pdb.mmcif as iotbx_mmcif

def get_mtz_info(datafile):
    """
    Get unit cell and SG from input mtz
    """

    sg = False
    cell = False
    vol = False

    # Convert from unicode
    datafile = convert_unicode(datafile)

    # Read datafile
    data = iotbx_mtz.object(datafile)

    # Derive space group from datafile
    sg = fix_R3_sg(data.space_group_name().replace(" ", ""))

    # Wrangle the cell parameters
    cell = [round(x,3) for x in data.crystals()[0].unit_cell_parameters() ]

    # The volume
    vol = data.crystals()[0].unit_cell().volume()

    return (sg, cell, vol)

def get_res(datafile):
    """Return resolution limit of dataset"""

    datafile = convert_unicode(datafile)
    data = iotbx_mtz.object(datafile)

    return float(data.max_min_resolution()[-1])

def get_spacegroup_info(cif_file):
    """Get info from PDB of mmCIF file"""

    # print "get_spacegroup_info", cif_file, os.getcwd()

    cif_file = convert_unicode(cif_file)

    if cif_file[-3:].lower() == "cif":
        fail = False
        cif_spacegroup = False

        try:
            input_file = open(cif_file, "r").read(20480)
            for line in input_file.split('\n'):
                if "_symmetry.space_group_name_H-M" in line:
                    cif_spacegroup = line[32:].strip()[1:-1].upper().replace(" ", "")
                if "_pdbx_database_status.pdb_format_compatible" in line:
                    if line.split()[1] == "N":
                        fail = True
        except IOError:
            return False
        if fail:
            return False
        else:
            return cif_spacegroup
    else:
        return str(iotbx_pdb.input(cif_file).crystal_symmetry().space_group_info()).upper().replace(" ", "")

def get_pdb_info(cif_file, dres, matthews=True, cell_analysis=False, data_file=False):
    """Get info from PDB of mmCIF file"""

    # Get rid of ligands and water so Phenix won't error.
    np = 0
    na = 0
    nmol = 1
    sc = 0.55
    nchains = 0
    res1 = 0.0
    d = {}
    l = []
    
    #print cif_file
    #print dres
    #print matthews
    #print cell_analysis
    #print data_file

    # Read in the file
    cif_file = convert_unicode(cif_file)
    if cif_file[-3:].lower() == 'cif':
        root = iotbx_mmcif.cif_input(file_name=cif_file).construct_hierarchy()
    else:
        root = iotbx_pdb.input(cif_file).construct_hierarchy()

    # Go through the chains
    for chain in root.models()[0].chains():
        # Number of protein residues
        np1 = 0
        # Number of nucleic acid residues
        na1 = 0

        # Sometimes Hetatoms are AA with same segid.
        if l.count(chain.id) == 0:
            l.append(chain.id)
            repeat = False
            nchains += 1
        else:
            repeat = True

        # Count the number of AA and NA in pdb file.
        for rg in chain.residue_groups():
            if rg.atoms()[0].parent().resname in iotbx_pdb.common_residue_names_amino_acid:
                np1 += 1
            if rg.atoms()[0].parent().resname in iotbx_pdb.common_residue_names_rna_dna:
                na1 += 1
            # Not sure if I get duplicates?
            if rg.atoms()[0].parent().resname in \
               iotbx_pdb.common_residue_names_ccp4_mon_lib_rna_dna:
                na1 += 1
        # Limit to 10 chains?!?
        if nchains < 10:
            # Do not split up PDB if run from cell analysis
            if not cell_analysis and not repeat:

                # Save info for each chain.
                if np1 or na1:

                    # Write new pdb files for each chain.
                    temp = iotbx_pdb.hierarchy.new_hierarchy_from_chain(chain)

                    # Long was of making sure that user does not have directory named '.pdb' or
                    # '.cif'
                    #n = os.path.join(os.path.dirname(cif_file), "%s_%s.pdb" % \
                    n = os.path.join(os.path.dirname(cif_file), "%s_%s.cif" % \
                    
                        (os.path.basename(cif_file)[:os.path.basename(cif_file).find('.')], \
                        chain.id))
                    #temp.write_pdb_file(file_name=n)
                    temp.write_mmcif_file(file_name=n)
                    if matthews:
                        # Run Matthews Calc. on chain
                        #phaser_return = run_phaser_module((np1, na1, dres, n, data_file))
                        phaser_return = run_phaser_module(data_file, (np1, na1, dres, n))
                    else:
                        res1 = run_phaser_module(n)

                    d[chain.id] = {'file': n,
                                   'NRes': np1+na1,
                                   'MWna': na1*330,
                                   'MWaa': np1*110,
                                   'MW': na1*330+np1*110,
                                   'NMol': phaser_return.get("z", nmol),
                                   'SC': phaser_return.get("solvent_content", sc),
                                   'res': phaser_return.get("target_resolution", res1)}
        np += np1
        na += na1

    # Run on entire PDB
    if matthews:
        #phaser_return = run_phaser_module((np, na, dres, cif_file, data_file))
        phaser_return = run_phaser_module(data_file, (np, na, dres, cif_file))
    else:
        #phaser_return = run_phaser_module((np, na, dres, cif_file, data_file))
        phaser_return = run_phaser_module(data_file, (np, na, dres, cif_file))
    d['all'] = {'file': cif_file,
                'NRes': np+na,
                'MWna': na*330,
                'MWaa': np*110,
                'MW': na*330+np*110,
                'NMol': phaser_return.get("z", nmol),
                'SC': phaser_return.get("solvent_content", sc),
                'res': phaser_return.get("target_resolution", res1)}
    return d

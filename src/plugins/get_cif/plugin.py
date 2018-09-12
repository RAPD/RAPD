"""get_cif RAPD plugin"""

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
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "GET_CIF"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "e5b33482291111e780c3ac87a3333966"
VERSION = "1.0.0"

# Standard imports
import argparse
import logging
import multiprocessing
import os
import shutil
import subprocess
import time
import urllib2
# Used for PDBe searches
from mysolr import Solr

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.credits as rcredits
import utils.global_vars as rglobals
from utils.text import json
from bson.objectid import ObjectId
from utils.processes import local_subprocess

# Cache of CIF files
#CIF_CACHE = rglobals.CIF_CACHE

# NE-CAT REST PDB server
PDBQ_SERVER = rglobals.PDBQ_SERVER
# USed for PDBe search server
UNLIMITED_ROWS = 10000000

# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

class RapdPlugin(multiprocessing.Process):
    """
    RAPD plugin class
    """

    #pdbq_entries = {}
    pdbs_to_download = []

    def __init__(self, command, tprint=False, logger=False):
        """Initialize the plugin"""

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Keep track of start time
        self.start_time = time.time()
        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        # Some logging
        self.logger.info(command)

        # Store passed-in variables
        self.command = command
        # self.reply_address = self.command["return_address"]
        multiprocessing.Process.__init__(self, name="get_cif")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()
        self.print_credits()

    def preprocess(self):
        """Set up for plugin action"""

        # self.tprint("preprocess")
        self.repository = check_pdbq()

        # Check for existence of pdb codes in the PDBQ database
        self.check_in_pdbq()

        # Check to make sure we are not going to overwrite any files in the local directory
        self.check_path()

    def process(self):
        """Run plugin action"""

        # self.tprint("process")

        self.get_cif_files()

    def postprocess(self):
        """Clean up after plugin action"""

        # self.tprint("postprocess")

    def check_in_pdbq(self):
        """Check if input PDB codes are in the PDBQ database"""

        self.tprint("\nChecking that requested codes are in the PDBQ database",
                    level=30,
                    color="blue")

        #for pdb_code in self.command["input_data"]["pdb_codes"]:
        self.pdbs_to_download = self.repository.check_for_pdbs(self.command["input_data"]["pdb_codes"]).keys()

    def check_in_pdbq_OLD(self):
        """Check if input PDB codes are in the PDBQ database"""

        self.tprint("\nChecking that requested codes are in the PDBQ database",
                    level=30,
                    color="blue")

        for pdb_code in self.command["input_data"]["pdb_codes"]:

            # Query pdbq server
            response = urllib2.urlopen(urllib2.Request("%s/entry/%s" % \
                       (PDBQ_SERVER, pdb_code))).read()

            # Decode search result
            entry = json.loads(response)

            # No entry
            if entry["message"] == None:

                # Print info to console
                self.tprint("  %s not in PDBQ database" % pdb_code,
                            level=50,
                            color="red")

            # Have an entry in PDBQ
            else:

                # Save the entry (NOT USED)
                #self.pdbq_entries[pdb_code] = entry["message"]

                # Put code on the good list
                self.pdbs_to_download.append(pdb_code)

                # Grab the description
                description = entry["message"]["_entity-pdbx_description"][0]

                # Print info to console
                self.tprint("  %s - %s" % (pdb_code, description),
                            level=10,
                            color="white")

    def check_path(self):
        """Make sure that the file does not exist already"""

        for pdb_code in self.pdbs_to_download:

            if self.command["preferences"]["pdb"]:
                target_file = pdb_code.lower() + ".pdb"
            else:
                target_file = pdb_code.lower() + ".cif"

            if os.path.exists(target_file):
                if not self.command["preferences"]["force"]:
                    raise Exception("%s already exists. Erase or run with -f flag.")

    def get_cif_files(self):
        """Retrieve/check for/uncompress/convert structure file"""

        self.tprint("\nRetrieving files from PDBQ server",
                    level=30,
                    color="blue")

        for pdb_code in self.pdbs_to_download:

            # self.tprint("    %s" % pdb_code,
            #             level=30,
            #             color="white")

            # The cif file name
            cif_file = pdb_code.lower() + ".cif"
            # print "cif_file", cif_file

            # Get the gzipped cif file from the PDBQ server
            self.tprint("      Fetching %s" % cif_file, level=10, color="white")
            self.download_cif(pdb_code, cif_file, self.tprint)

            # Convert from cif to pdb
            if self.command["preferences"]["pdb"]:
                # Convert
                conversion_proc = subprocess.Popen(["phenix.cif_as_pdb", cif_file],
                                                     stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE)
                conversion_proc.wait()
                # pdb_file = cif_file.replace(".cif", ".pdb")

                # Remove the CIF file
                os.unlink(cif_file)

    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        # self.tprint("print_credits")

        self.tprint(rcredits.HEADER, level=99, color="blue")

        programs = ["CCTBX"]
        info_string = rcredits.get_credits_text(programs, "    ")
        self.tprint(info_string, level=99, color="white")

class NECATRepository():
    """Class for locat NE-CAT PDB repository"""
    # Save results from all the PDB's so we don't have to keeps querying the same ones..

    def __init__(self, server, tprint=False, logger=False):
        self.server = server
        self.tprint = tprint
        self.logger = logger

    def check_conn(self):
        """Check if it is up"""
        print self.server

        try:
            # Query pdbq server
            response = urllib2.urlopen(urllib2.Request("%s/entry/%s" % \
                       (self.server, '1E1O'))).read()
    
            # Decode search result
            #entry = json.loads(response)
            return True

        except urllib2.URLError as pdbq_error:
            if self.tprint:
                self.tprint("  Error connecting to NE-CAT PDBQ server %s" % pdbq_error,
                            level=30,
                            color="red")
            return False

    def check_for_pdbs(self, pdb_list):
        """Check if PDB file in PDB repository and pass back molecular description"""
        output_dict = {}
        
        # Make a new list with all upper case PDB codes
        pdb_list = [pdb.upper() for pdb in pdb_list]
        # Change list to comma separated string.
        pdb_str = ','.join(pdb.upper() for pdb in pdb_list)

        try:
            # Query pdbq server
            response = urllib2.urlopen(urllib2.Request("%s/entry/%s" % \
                       (self.server, pdb_str))).read()
            # Decode search result
            entry = json.loads(response)

        except urllib2.URLError as pdbq_error:
            if self.tprint:
                self.tprint("  Error connecting to PDBQ server %s" % pdbq_error,
                            level=30,
                            color="red")
            for pdb_code in pdb_list:
                output_dict[pdb_code] = {'description': "Unknown - unable to connect to PDBQ server"}
            return output_dict
        
        for x, pdb_code in enumerate(pdb_list):
            if isinstance(entry["message"], list):
                ret = entry["message"][x]
            else:
                ret = entry["message"]
            # If not in PDBQ
            if ret in [None]:
                output_dict[pdb_code] = {'description': "Unknown - PDB code not found in PDBQ server"}
            else:
                output_dict[pdb_code] = {'description': ret.get("_entity-pdbx_description")[0]}
        return output_dict

    def check_for_pdbs_OLD(self, pdb_list):
        """Check if PDB file in PDB repository and pass back molecular description"""
    
        output_dict = {}
       
        for pdb_code in pdb_list:
    
            # Make sure we are in upper case
            pdb_code = pdb_code.upper()

            try:
                # Query pdbq server
                ## Change to comma separated (https://rapd.nec.aps.anl.gov/pdbq/entry/1Z7E,1QRV)
                response = urllib2.urlopen(urllib2.Request("%s/entry/%s" % \
                           (self.server, pdb_code))).read()
                # Decode search result
                entry = json.loads(response)
    
            except urllib2.URLError as pdbq_error:
                if self.tprint:
                    self.tprint("  Error connecting to PDBQ server %s" % pdbq_error,
                                level=30,
                                color="red")
                entry = {"message": {"_entity-pdbx_description": [
                    "Unknown - unable to connect to PDBQ sever"
                ]}}

            # Grab the description
            description = entry["message"]["_entity-pdbx_description"][0]
    
            # Save the entry
            output_dict[pdb_code] = {'description': description}
    
            # Print info to console
            if self.tprint:
                self.tprint("  %s - %s" % (pdb_code, description),
                            level=10,
                            color="white")

        return output_dict
    
    def download_cif(self, pdb_code, fname):
        """Download the CIF file to fname"""
        
        if os.path.exists(fname):
            return fname
        else:
            try:
                response = urllib2.urlopen(urllib2.Request(\
                            "%s/entry/get_cif/%s" % \
                            (self.server, pdb_code.lower()))\
                            , timeout=60).read()
                # Write the  gzip file
                with open('%s.gz'%fname, "wb") as outfile:
                    outfile.write(response)
                    outfile.close()
                # Unzip the file and pass back path
                local_subprocess(command = ['gunzip', '%s.gz'%fname])
                #subprocess.Popen(["gunzip", '%s.gz'%fname]).wait()
                
                return fname
    
            except urllib2.HTTPError as http_error:
                if self.tprint:
                    self.tprint("      %s when fetching %s" % (http_error, pdb_code),
                                level=50,
                                color="red")
                return False

    def cell_search(self, search_params):
        """search for PDBs within unit cell range."""
        # Query server
        #print "%s/search/" % PDBQ_SERVER
        response = urllib2.urlopen(urllib2.Request("%s/cell_search/" % \
                   self.server, data=json.dumps(search_params))).read()

        # Decode search result
        search_results = json.loads(response)

        # Create handy description key
        for k in search_results.keys():
            search_results[k]["description"] = \
                search_results[k].pop("struct.pdbx_descriptor")

        return search_results

class RCSBRepository():
    """Class for RCSB PDB repository. NOT VERY RELIABLE"""
    # Save results from all the PDB's so we don't have to keeps querying the same ones..
    results = {}

    def __init__(self, server, tprint=False, logger=False):
        self.server = server
        self.tprint = tprint
        self.logger = logger

    def check_conn(self):
        """Check if it is up"""
        try:
            # Query pdbq server
            response = urllib2.urlopen(urllib2.Request("%s/describeHet?chemicalID=NAG" % \
                       self.server,)).read()
            return True

        except urllib2.URLError as pdbq_error:
            if self.tprint:
                self.tprint("  Error connecting to RCSB PDBQ server %s" % pdbq_error,
                            level=30,
                            color="red")
            return False

    def check_for_pdbs(self, pdb_list):
        """Check if PDB file in PDB repository and pass back molecular description"""
        output_dict = {}
        # check if we already ran some of the PDB codes.
        check = self.results.keys()
        for pdb_code in pdb_list:
            # Make sure we are in upper case
            pdb_code = pdb_code.upper()
            # Check if we already ran code
            if check.count(pdb_code):
                 description = self.results[pdb_code].get('description')
            else:
                try:
                    # Query pdbq server
                    response = urllib2.urlopen(urllib2.Request("%s/describeMol?structureId=%s" % \
                               (self.server, pdb_code)),timeout=5).readlines()
                    # save a list with all the mol names
                    name = [ line[line.find('"')+1:line.rfind('"')] for line in response if line.count('<polymerDescription description') ]
                    description = name[0]
                except:
                    if self.tprint:
                        self.tprint("  Error connecting to PDBQ server",
                                    level=30,
                                    color="red")
                    description = "Unknown - unable to connect to PDBQ sever"
            # Save the entry
            output_dict[pdb_code] = {'description': description}
            # Print info to console
            if self.tprint:
                self.tprint("  %s - %s" % (pdb_code, description),
                            level=10,
                            color="white")
        # Update new results
        self.results.update(output_dict)
        # Return results
        return output_dict

    def download_cif(self, pdb_code, fname):
        """Download the CIF file to fname"""
        if os.path.exists(fname):
            return fname
        else:
            try:
                # PDBe is more reliable
                wget = ['wget', 'ftp://ftp.ebi.ac.uk/pub/databases/rcsb/pdb/data/structures/divided/mmCIF/%s/%s.cif.gz'%(pdb_code.lower()[1:-1], pdb_code.lower())]
                local_subprocess(command = wget)
                local_subprocess(command = ['gunzip', '%s.gz'%fname])
                return fname
            except:
                if self.tprint:
                    self.tprint("     Error when fetching %s" % (pdb_code),
                                level=50,
                                color="red")
                return False

    def cell_search(self, search_params):
        """search for PDBs within unit cell range."""
        # Generate input for RCSB
        #l0 = inp
        l1 = ['length_a','length_b','length_c','angle_alpha','angle_beta','angle_gamma']
        
        querycell  = '<?xml version="1.0" encoding="UTF-8"?>'
        querycell += '<orgPdbQuery><queryType>org.pdb.query.simple.XrayCellQuery</queryType>'
        for x in range(len(l1)):
            p = l1[x].split('_')[-1]
            querycell += '<cell.%s.comparator>between</cell.%s.comparator>'%(2*(l1[x],))
            #querycell += '<cell.%s.min>%s</cell.%s.min>'%(l1[x],float(self.cell2[l2[y][x]])-float(self.cell2[l2[y][x]])*self.percent/2,l1[x])
            querycell += '<cell.%s.min>%s</cell.%s.min>'%(l1[x],search_params[p][0],l1[x])
            #querycell += '<cell.%s.max>%s</cell.%s.max>'%(l1[x],float(self.cell2[l2[y][x]])+float(self.cell2[l2[y][x]])*self.percent/2,l1[x])
            querycell += '<cell.%s.max>%s</cell.%s.max>'%(l1[x],search_params[p][1],l1[x])
        querycell += '</orgPdbQuery>'
        self.logger.debug("Checking the PDB...")
        #self.logger.debug(querycell)
        #Sometimes I get an error in urlopen saying it can't resolve the output from the PDB.
        try:
            search_results = urllib2.urlopen(urllib2.Request('%s/search'%self.server, data=querycell)).read().split()
        except urllib2.HTTPError:
            search_results = []

        # Get the molecular descriptions
        return self.check_for_pdbs(search_results)

class PDBERepository():
    """Class for locat RCSB PDB repository"""
    # Save results from all the PDB's so we don't have to keeps querying the same ones..
    results = {}

    def __init__(self, server, tprint=False, logger=False):
        self.server = server
        self.tprint = tprint
        self.logger = logger

    def check_conn(self):
        """Check if it is up"""
        try:
            # Query pdbq server
            query =  {"q" : 'pdb_id:1thw',
                      "rows" : 1, # i.e. all matching documents are required in response
                      "fl"   : "pdb_id, molecule_name", # restrict the returned documents to these fields only
                      }
            self.solr_search(query)
            return True

        except :
            if self.tprint:
                self.tprint("  Error connecting to PDBe server" ,
                            level=30,
                            color="red")
            return False

    def check_for_pdbs(self, pdb_list):
        """Check if PDB file in PDB repository and pass back molecular description"""
        output_dict = {}
        search = []
        query = {"rows" : UNLIMITED_ROWS, # i.e. all matching documents are required in response
                 "fl"   : "pdb_id, molecule_name", # restrict the returned documents to these fields only
                 }
        # Separate out the codes that have to be searched from ones that have already been done.
        for pdb in pdb_list:
            if self.results.get(pdb.upper(), False):
                output_dict[pdb.upper()] = {'description': self.results[pdb_code.upper()].get('description')}
            else:
                search.append(pdb.lower())
        # Update the query
        query.update({'q': 'pdb_id:(%s)'%" OR ".join(search)})
        # update the output_dict with the new results
        output_dict.update(self.solr_search(query))
        return output_dict

    def download_cif(self, pdb_code, fname):
        """Download the CIF file to fname"""
        if os.path.exists(fname):
            return fname
        else:
            try:
                wget = ['wget', 'ftp://ftp.ebi.ac.uk/pub/databases/rcsb/pdb/data/structures/divided/mmCIF/%s/%s.cif.gz'%(pdb_code.lower()[1:-1], pdb_code.lower())]
                local_subprocess(command = wget)
                local_subprocess(command = ['gunzip', '%s.gz'%fname])
                return fname
            except:
                if self.tprint:
                    self.tprint("     Error when fetching %s" % (pdb_code),
                                level=50,
                                color="red")
                return False
    
    def download_pdb(self, pdb_code, fname):
        """Download the PDB file to fname"""
        if os.path.exists(fname):
            return fname
        else:
            try:
                wget = ['wget', 'ftp://ftp.ebi.ac.uk/pub/databases/rcsb/pdb/data/structures/divided/pdb/%s/pdb%s.ent.gz'%(pdb_code.lower()[1:-1], pdb_code.lower())]
                local_subprocess(command = wget)
                shutil.move('pdb%s.ent.gz'%pdb_code.lower(), '%s.gz'%os.path.basename(fname))
                local_subprocess(command = ['gunzip', '%s.gz'%fname])
                return fname
            except:
                if self.tprint:
                    self.tprint("     Error when fetching %s" % (pdb_code),
                                level=50,
                                color="red")
                return False
 
    def cell_search(self, search_params):
        """search for PDBs within unit cell range."""
        #search_params = {'a': [100, 102], 'b': [100, 102], 'c': [100, 102], 'alpha' : [90, 91], 'beta': [90, 91], 'gamma': [90, 91]}
        #UNLIMITED_ROWS = 10000000 # necessary because default in mysolr is mere 10
        
        # Search keys
        l1 = ['cell_a','cell_b','cell_c','cell_alpha','cell_beta','cell_gamma']
       
        query = {#"q" : 'pdb_id:(2qk9 OR 1thw)',
            "rows" : UNLIMITED_ROWS, # i.e. all matching documents are required in response
            "fl"   : "pdb_id, molecule_name", # restrict the returned documents to these fields only
            }
        query["q"] = " AND ".join(["%s:[%s TO %s]" % 
                                     (l, search_params[l.split('_')[-1]][0], search_params[l.split('_')[-1]][1]) for l in l1 ])
        
        output_dict = self.solr_search(query)
        self.results.update(output_dict)
        return output_dict

    def solr_search(self, query):
        """Do the solr search and pass back results"""
        output_dict = {}
        # Setup connections
        solr = Solr(self.server,version=4)
        #UNLIMITED_ROWS = 10000000 # necessary because default in mysolr is mere 10
        # Run the search
        search_results = solr.search(**query)
        # Format results
        for pdb in search_results.documents:
            output_dict[pdb.get('pdb_id').upper()] = {'description': pdb.get('molecule_name')[0]}
        return output_dict

def check_pdbq(tprint=False, logger=False):
    """Check the PDBQ server and return which one is working"""
    if PDBQ_SERVER:
        if isinstance(PDBQ_SERVER, list):
            check = False
            for site in PDBQ_SERVER:
                if site.count('rapd'):
                    instance = NECATRepository(site, tprint, logger)
                    check = instance.check_conn()
                    if check:
                        return instance
                elif site.count('pdbe') and not check:
                    instance = PDBERepository(site, tprint, logger)
                    check = instance.check_conn()
                    if check:
                        return instance
                elif site.count('rcsb') and not check:
                    instance = RCSBRepository(site, tprint, logger)
                    check = instance.check_conn()
                    if check:
                        #instance.download_cif('209d', '/gpfs6/users/necat/Jon/RAPD_test/Output/209d.cif')
                        return instance

def get_commandline():
    """Grabs the commandline"""

    # print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Retrieve CIF or PDB files from PDBQ server"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Reduce output")

    args = my_parser.parse_args()

    # Insert logic to check or modify args here

    return args

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    if args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    if __name__ == "__main__":

        main()

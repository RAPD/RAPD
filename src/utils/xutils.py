"""
rapd_utils has a number of useful dicts and functions used in rapd
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2017, Cornell University
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
from pprint import pprint
import shutil
import subprocess
import sys

from utils.text import json
from bson.objectid import ObjectId

from iotbx import mtz as iotbx_mtz
from iotbx import pdb as iotbx_pdb
import iotbx.pdb.mmcif as iotbx_mmcif

# RAPD imports
#import plugins.subcontractors.parse as Parse
from utils.modules import load_module


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
for key, val in xds_bravais_types.iteritems():
    for sg in val:
        if not sg in intl_to_xds_bravais_type:
            intl_to_xds_bravais_type[sg] = ()
        intl_to_xds_bravais_type[sg] += (key,)



subgroups = {  'None' : [],
               '1'    : [],
               '5'    : [],
               '3'    : ['4'],
               '22'   : [],
               '23'   : ['24'],
               '21'   : ['20'],
               '16'   : ['17','18','19'],
               '79'   : ['80','97','98'],
               '75'   : ['76','77','78','89','90','91','95','94','93','92','96'],
               '143'  : ['144','145','149','151','153','150','152','154','168','169','170','171','172','173','177','178','179','180','181','182'],
               '146'  : ['155'],
               '196'  : ['209','210'],
               '197'  : ['199','211','214'],
               '195'  : ['198','207','208','212','213'] }

intl2std =   { 'None' : 'None',
               '1'   : 'P1',      #* Bravais
               '5'   : 'C2',      #*
               '3'   : 'P2',      #*
               '4'   : 'P21',
               '22'  : 'F222',    #*
               '23'  : 'I222',    #*
               '24'  : 'I212121',
               '21'  : 'C222',    #*
               '20'  : 'C2221',
               '16'  : 'P222',    #*
               '17'  : 'P2221',
               '18'  : 'P21212',
               '19'  : 'P212121',
               '79'  : 'I4',      #*
               '80'  : 'I41',
               '97'  : 'I422',
               '98'  : 'I4122',
               '75'  : 'P4',      #*
               '76'  : 'P41',
               '77'  : 'P42',
               '78'  : 'P43',
               '89'  : 'P422',
               '90'  : 'P4212',
               '91'  : 'P4122',
               '95'  : 'P4322',
               '93'  : 'P4222',
               '94'  : 'P42212',
               '92'  : 'P41212',
               '96'  : 'P43212',
               '143' : 'P3',      #*
               '144' : 'P31',
               '145' : 'P32',
               '149' : 'P312',
               '151' : 'P3112',
               '153' : 'P3212',
               '150' : 'P321',
               '152' : 'P3121',
               '154' : 'P3221',
               '168' : 'P6',
               '169' : 'P61',
               '170' : 'P65',
               '171' : 'P62',
               '172' : 'P64',
               '173' : 'P63',
               '177' : 'P622',
               '178' : 'P6122',
               '179' : 'P6522',
               '180' : 'P6222',
               '181' : 'P6422',
               '182' : 'P6322',
               '146' : 'R3',      #*
               '155' : 'R32',
               '196' : 'F23',     #*
               '209' : 'F432',
               '210' : 'F4132',
               '197' : 'I23',     #*
               '199' : 'I213',
               '211' : 'I432',
               '214' : 'I4132',
               '195' : 'P23',     #*
               '198' : 'P213',
               '207' : 'P432',
               '208' : 'P4232',
               '212' : 'P4332',
               '213' : 'P4132' }

std2intl = dict((value,key) for key, value in intl2std.iteritems())

std_sgs = ['None','P1','C2','P2','P21','F222','I222','I212121','C222','C2221','P222',
           'P2221','P21212','P212121','I4','I41','I422','I4122','P4','P41','P42','P43',
           'P422','P4212','P4122','P4322','P4222','P42212','P41212','P43212','P3','P31',
           'P32', 'P312','P3112','P3212','P321','P3121','P3221','P6','P61','P65','P62',
           'P64','P63','P622','P6122','P6522','P6222','P6422','P6322','R3','R32','F23',
           'F432','F4132','I23','I213','I432','I4132','P23''P213''P432','P4232','P4332',
           'P4132']
#
#  Some utility functions
#
def print_dict(in_dict):
    keys = in_dict.keys()
    keys.sort()
    for key in keys:
        print key,'::',in_dict[key]
    print ''

months = { 'Jan' : '01',
           'Feb' : '02',
           'Mar' : '03',
           'Apr' : '04',
           'May' : '05',
           'Jun' : '06',
           'Jul' : '07',
           'Aug' : '08',
           'Sep' : '09',
           'Oct' : '10',
           'Nov' : '11',
           'Dec' : '12'}

def zerofillday(day_in):
    #print day_in
    intday = int(day_in)
    #print intday
    strday = str(intday)
    #print strday
    if len(strday) == 2:
        return(strday)
    else:
        return('0'+strday)

def date_adsc_to_sql(datetime_in):
    #print datetime_in
    spldate = datetime_in.split()
    #print spldate
    time  = spldate[3]
    #print time
    year  = spldate[4]
    #print year
    month = months[spldate[1]]
    #print month
    day   = zerofillday(spldate[2])
    #print day

    date = '-'.join((year,month,day))
    #print date
    #print ' '.join((date,time))
    return('T'.join((date,time)))

def calcADF(self, inp):
    """
    Calc an ADF from MR phases.
    """

    #try:
    mtz  = self.phaser_results[inp].get("AutoMR results").get("AutoMR mtz")
    pdb  = self.phaser_results[inp].get("AutoMR results").get("AutoMR pdb")
    map1 = self.phaser_results[inp].get("AutoMR results").get("AutoMR adf")
    peak = self.phaser_results[inp].get("AutoMR results").get("AutoMR peak")
    file_type = self.datafile[-3:]
    if file_type == "mtz":
        command  = "cad hklin1 %s hklin2 %s hklout adf_input.mtz<<eof3\n"%(mtz, self.datafile)
    else:
        command  = "scalepack2mtz hklin %s hklout junk.mtz<<eof1\n"%self.datafile
        command += "symm %s\nanomalous yes\nend\neof1\n" % self.phaser_results[inp].get("AutoMR results").get("AutoMR sg")
        command += "truncate hklin junk.mtz hklout junk2.mtz<<eof2\n"
        command += "truncate yes\nanomalous yes\nend\neof2\n"
        command += "cad hklin1 %s hklin2 junk2.mtz hklout adf_input.mtz<<eof3\n" % mtz
    command += "labin file 1 E1=FC  E2=PHIC E3=FOM\n"
    command += "labin file 2 all\nend\neof3\n"
    command += "fft hklin adf_input.mtz mapout map.tmp<<eof4\n"
    command += "scale F1 1.0\n"
    command += "labin DANO=DANO SIG1=SIGDANO PHI=PHIC W=FOM\n"
    command += "end\neof4\n"
    command += "mapmask mapin map.tmp xyzin %s mapout %s<<eof5\n" % (pdb, map1)
    command += "border 5\nend\neof5\n"
    command += "peakmax mapin %s xyzout %s<<eof6\n" % (map1, peak)
    command += "numpeaks 50\nend\neof6\n\n"
    adf = open("adf.com", "w")
    adf.writelines(command)
    adf.close()

    if self.test == False:
        processLocal(("sh adf.com", "adf.log"), self.logger)
    else:
        os.system("touch adf.com")
    """
    except:
        # self.logger.exception('**Error in Utils.calcADF**')
        pass
    """
def calcResNumber(self,sg,se=False,vol=False):
  """
  Calculates total number of residues or number of Se in AU.
  """
  if self.verbose:
    self.logger.debug('Utilities::calcResNumber')
  #try:
  if vol:
    num_residues = calcTotResNumber(self,vol)
  else:
    num_residues = calcTotResNumber(self,calcVolume(self))
  den = int(symopsSG(self,sg))
  if sg == 'R3':
    if self.cell2[-1].startswith('120'):
      den = int(symopsSG(self,'H3'))
  elif sg == 'R32':
    if self.cell2[-1].startswith('120'):
      den = int(symopsSG(self,'H32'))
  #Figure about 1 SeMet every 75 residues.
  if se:
    num_se = int(round((num_residues/75)/den))
    if num_se == 0:
      num_se = 1
    return (num_se)
  else:
    return (int(num_residues/den))
  """
  except:
    self.logger.exception('**Error in Utils.calcResNumber**')
    if se:
      return(5)
    else:
      return(200)
  """
def calc_res_number(sg, se=False, volume=0.0, sample_type="protein", solvent_content=0.55):
    """
    Calculates total number of residues or number of Se in AU.
    """

    # try:
    if volume:
        num_residues = calc_tot_res_number(volume, sample_type, solvent_content)
    else:
        num_residues = calcTotResNumber(self, calcVolume(self))

    den = sg_to_nsymops(sg)

    if sg == "R3":
        if self.cell2[-1].startswith("120"):
            den = sg_to_nsymops("H3")
    elif sg == "R32":
        if self.cell2[-1].startswith("120"):
            den = sg_to_nsymops("H32")

    # Figure about 1 SeMet every 75 residues.
    if se:
        num_se = int(round((num_residues/75)/den))
        if num_se == 0:
            num_se = 1
        return num_se
    else:
        return int(num_residues/den)
    # except:
    #   self.logger.exception('**Error in Utils.calcResNumber**')
    #   if se:
    #     return(5)
    #   else:
    #     return(200)

def calcTotResNumber_OLD(self, volume):
  """
  Calculates number of residues in the unit cell for Raddose calculation. If cell volume bigger than 50000000, then
  turns on Ribosome which makes changes so meaning strategy is presented.
  """
  if self.verbose:
    self.logger.debug('Utilities::calcTotResNumber')
  #try:
  checkVolume(self,volume)
  content = 1 - float(self.solvent_content)
  #Calculate number of residues based on solvent content in volume of cell.
  if self.sample_type == 'protein':
    #based on average MW of residue = 110 DA
    return(int((float(volume)*float(content))/135.3))
  elif self.sample_type == 'dna':
    #based on average MW of residue = 330 DA
    return(int((float(volume)*float(content))/273.9))
  else:
    #if RNA or Ribosome
    #RNA based on average MW of residue = 340 DA
    return(int((float(volume)*float(content))/282.2))
  """
  except:
    self.logger.exception('**Error in Utils.calcTotResNumber**')
    return (None)
  """
def calc_tot_res_number(volume, sample_type='protein', solvent_content=False):
    """
    Calculates number of residues in the unit cell for Raddose calculation. If cell volume bigger than 50000000, then
    turns on Ribosome which makes changes so meaning strategy is presented.
    """
    # try:
    if not sample_type:
        if volume > 25000000.0: #For 30S
            sample_type = "ribosome"

    if not solvent_content:
        if sample_type == "protein":
            solvent_content = 0.55
        elif sample_type == "ribosome":
            solvent_content = 0.64
        elif sample_type == "dna":
            solvent_content = 0.64

    content = 1 - solvent_content

    # Calculate number of residues based on solvent content in volume of cell.
    if sample_type == "protein":
        # Based on average MW of residue = 110 DA
        return int((float(volume)*float(content))/135.3)
    elif sample_type == "dna":
        # Based on average MW of residue = 330 DA
        return int((float(volume)*float(content))/273.9)
    else:
        # RNA or Ribosome
        # RNA based on average MW of residue = 340 DA
        return int((float(volume)*float(content))/282.2)

def calcTransmission(self,attenuation=1):
    """
    NOT run for Best strategy. Calculate appropriate setting for % transmission for Mosflm strategy.
    """
    if self.verbose:
        self.logger.debug('Utilities::calcTransmission')
    #try:
    if self.distl_results:
        if self.distl_results["distl_results"] != 'FAILED':
            mean_int_sig = float(max(self.distl_results.get("distl_results").get('mean int signal')))
            if mean_int_sig < 1:
                mean_int_sig = -1
    else:
        mean_int_sig = -1

    #TESTING: Adjusting the '4000' number to give reasonable results for expected transmission setting.
    #if self.best_failed == False:
    if mean_int_sig != -1:
        trans = int((4000/(mean_int_sig))*self.transmission*attenuation)
        if trans > 100:
            trans = int(100)
            if trans < 1:
                trans = int(1)
    else:
        trans = int(attenuation*self.transmission)
    return (trans)
    """
    except:
        self.logger.exception('**Error in Utils.calcTransmission**')
        return (1)
    """
def calcVolume(self):
    """
    Calculate and return volume of unit cell.
    """
    if self.verbose:
        self.logger.debug('Utilities::calcVolume')
    #try:
    log = []
    volume = False
    #put together the command script for Raddose
    if isinstance(self.cell, list):
        cell = ' '.join(self.cell)
    else:
        cell = self.cell
    #Run Raddose to get the volume of the cell.
    command = 'raddose << EOF\nCELL %s\nEND\nEOF\n'%cell
    output = subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    for line in output.stdout:
        log.append(line)
        #self.logger.debug(line.rstrip())
        if line.startswith('Unit Cell Volume'):
            volume = float((line.split())[4])
    return(volume)
    """
    except:
        self.logger.exception('**Error in Utils.calcVolume**')
        return(None)
    """
def changeIns(self):
  """
  Change the ins file for ShelxD to account for nproc in multiShelxD mode.
  """
  if self.verbose:
    self.logger.debug('Utilities::changeIns')
  #try:
  ntry = int(round(self.shelxd_try/self.njobs))
  if ntry == 0:
    ntry = 1
  os.system('cp junk_fa.ins junk_fa_orig.ins')
  junk = []
  for x,line in enumerate(open('junk_fa.ins','r').readlines()):
    junk.append(line)
    if line.startswith('SEED'):
      new_line = line.replace(line.split()[1],'0')
      junk.remove(line)
      junk.insert(x,new_line)
    if line.startswith('NTRY'):
      new_line2 = line.replace(line.split()[1],str(ntry))
      junk.remove(line)
      junk.insert(x,new_line2)
    if line.startswith('PATS'):
      #if self.many_sites:
      if self.many_sites or self.cubic:
        new = 'PATS 200\nWEED 0.3'
        new_line3 = line.replace(line.split()[0],new)
        junk.remove(line)
        junk.insert(x,new_line3)
  f2 = open('junk_fa.ins','w')
  f2.writelines(junk)
  f2.close()
  """
  except:
    self.logger.exception('**Error in Utils.ChangeIns**')
  """
"""
def checkAnom(self):

  #Check to see if anomalous signal is present in data. Should modify to just
  #read the SHELXC results instead of running it before.

  #try:
  signal = False
  #cc_anom   = self.data.get('original').get('cc_anom')
  log = open(self.data.get('original').get('scala_log'),'r').readlines()
  for line in log:
    if line.startswith('  Completeness'):
      comp = line.split()[1]
    if line.startswith('  Mid-Slope of'):
      slope = line.split()[5]
    if line.startswith('  DelAnom correlation'):
      cc_anom = line.split()[4]
    #if line.startswith('  Multiplicity'):
    #  mult = line.split()[1]
    #if line.startswith('  Anomalous completeness'):
    #  comp_anom = line.split()[2]
    #if line.startswith('  Anomalous multiplicity'):
    #  mult_anom = line.split()[2]
    #if line.startswith('  Rmerge    '):
    #  r = line.split()[1]
    #if line.startswith('  Rpim (within'):
    #  rpim_anom = line.split()[3]
    #if line.startswith('  Rpim (all'):
    #  rpim = line.split()[5]
  if float(comp) > 70:
    if float(slope) > 1:
      if float(cc_anom) > 0.1:
        #copy sca file to local directory so path isn't too long for SHELX
        sca = os.path.basename(self.datafile)
        shutil.copy(self.datafile,sca)
        command  = 'shelxc junk <<EOF\nCELL %s\nSPAG %s\nSAD %s\nFIND 1\nSFAC Se\nEOF\n'%(self.cell,self.input_sg,sca)
        output = subprocess.Popen(command,
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        temp = []
        for line in output.stdout:
          temp.append(line)
        #shelx = self.ParseOutputShelxC(temp)
        shelx = Parse.ParseOutputShelxC(self,temp)
        dsig = shelx.get('shelxc_dsig')
        max_dsig = max(dsig)
        if max_dsig > 1:
          signal = True
        else:
          signal = False
  if signal:
    return (True)
  else:
    Parse.setShelxResults(self)
    return (False)

  except:
    self.logger.exception('**ERROR in Utils.checkAnom**')
    Parse.setShelxResults(self)
    return(False)
"""
def checkInverse(self, inp):
    """
    Check if inverse SG is possible.
    """
    if self.verbose:
        self.logger.debug('Utilities::checkInverse')

    subgroups = {  '76' : ['78'],
                   '91' : ['95'],
                   '92' : ['96'],
                   '144': ['145'],
                   '151': ['153'],
                   '152': ['154'],
                   '169': ['170'],
                   '171': ['172'],
                   '178': ['179'],
                   '180': ['181'],
                   '212': ['213']
                   }
    if subgroups.has_key(inp):
        sg = subgroups[inp]
        return(sg)
    else:
        return([inp])

def checkSG(self, inp):
  """
  Check SG subgroups.
  """

  if self.verbose:
    self.logger.debug('Utilities::checkSG')

  subgroups = {  '1'  : [None],
                 '5'  : [None],
                 '3'  : ['4'],
                 '22' : [None],
                 '23' : ['24'],
                 '21' : ['20'],
                 '16' : ['17','18','19'],
                 '79' : ['80','97','98'],
                 '75' : ['76','77','78','89','90','91','95','94','93','92','96'],
                 '143': ['144','145','149','151','153','150','152','154','168','169','170','171','172','173','177','178','179','180','181','182'],
                 '146': ['155'],
                 '196': [None],
                 '209': ['210'],
                 '197': ['199'],
                 '211': ['214'],
                 '195': ['198'],
                 '207': ['208','212','213'] }
  return(subgroups[inp])

def checkVolume(self,volume):
  """
  Check to see if unit cell is really big.
  """
  if self.verbose:
    self.logger.debug('Utilities::checkVolume')
  #try:
  #if float(volume) > 50000000.0: #For 70S
  if float(volume) > 25000000.0: #For 30S
    self.sample_type = 'ribosome'
    self.solvent_content = 0.64
  """
  except:
    self.logger.exception('**Error in Utils.checkVolume**')
  """
def check_volume_OLD(volume):
    """Check to see if unit cell is really big"""


    if float(volume) > 25000000.0: #For 30S
        sample_type = "ribosome"
        solvent_content = 0.64
    # WONT WORK if less than 25000000
    return (sample_type, solvent_content)
"""
def checkXparm(self):

  #Check if XPARM.XDS has the same SG and similar cell to GXPARM.XDS. For multiruns.py.

  if self.verbose:
    self.logger.debug('Utilities::checkXparm')

  if os.path.exists('XPARM.XDS'):
    gxparm = int(Parse.ParseOutputGxparm(self,open(self.gxparm,'r').readlines(),True))
    xparm = int(Parse.ParseOutputGxparm(self,open('XPARM.XDS','r').readlines(),True))
    if gxparm != xparm:
      if os.path.exists('GXPARM.XDS'):
        os.rename('GXPARM.XDS','GXPARM1.XDS')
      os.rename('XPARM.XDS','XPARM_orig.XDS')
      shutil.copy(self.gxparm,os.path.join(os.getcwd(),'XPARM.XDS'))
"""
def cleanPDB(self,inp):
  """
  Get rid of HETATM, ANISOU, and water lines in pdb file.
  """
  if self.verbose:
    self.logger.debug('Utilities::cleanPDB')
  #try:
  temp = []
  old = '%s_orig.pdb'%inp[:-4]
  shutil.copy(inp,old)
  f = open(inp,'r').readlines()
  for line in f:
    temp.append(line)
    if line.startswith('HETATM'):
      temp.remove(line)
    if line.startswith('ANISOU'):
      temp.remove(line)
  f2 = open(inp,'w')
  f2.writelines(temp)
  f2.close()
  """
  except:
    self.logger.exception('**Error in Utils.cleanPDB**')
  """
def convert_hdf5_cbf(inp,
                     odir=False,
                     prefix=False,
                     imgn=False,
                     zfill=5,
                     logger=False):
    """
    Run eiger2cbf on HDF5 dataset. Returns path of new CBF files.
    Not sure I need multiprocessing.Pool, but used as saftety.
    odir is output directory
    prefix is new image prefix
    imgn is the image number for the output frame.
    zfill is the number digits for snap image numbers
    returns header
    """
    import multiprocessing, time, sys
    from rapd_pilatus import pilatus_read_header as readHeader

    if logger:
        logger.debug('Utilities::convert_hdf5_cbf')

    #try:
    #command0 = '/gpfs6/users/necat/Jon/Programs/CCTBX_x64/base_tmp/eiger2cbf/trunk/eiger2cbf %s'%inp
    command0 = "eiger2cbf %s" % inp

    if odir:
        out = odir
    else:
        out = '/gpfs6/users/necat/Jon/RAPD_test/Output/Temp'
    if prefix == False:
        prefix = 'conv_1_'

    # check if folder exists, if not make it and change to it.
    #folders2(self,out)
    if os.path.exists(out) == False:
        os.makedirs(out)
    os.chdir(out)

    if inp.count("master"):

        # Not really needed, unless someone collected a huge dataset.
        ncpu = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=ncpu)

        # Check how many frames are in dataset
        nimages = pool.apply_async(processLocal, ((command0, os.path.join(out, "test.log")),))
        nimages.wait()
        total = int(open('test.log','r').readlines()[-1])
        if BLspec.checkCluster():
            # Half the number of nodes in the queue.
            split = int(round(total/8))
            cluster = True
        else:
            # Least amount of splitting without running out of memory.
            split = 360
            cluster = False
        st = 1
        end = split
        stop = False
        # For Autoindexing. Differentiate pairs from separate runs.
        if total == 1:
            # Set the image number defaut to 1.
            if imgn == False: imgn = 1
            img = '%s%s.cbf'%(os.path.join(out,prefix),str(imgn).zfill(zfill))
            command = '%s 1 %s'%(command0, img)
        else:
            command = '%s %s:%s %s'%(command0,st, end, os.path.join(out,prefix))
        while 1:
            if cluster:
                # No self required
                pool.apply_async(BLspec.processCluster_NEW, ((command,os.path.join(out,'eiger2cbf.log')),))
            else:
                pool.apply_async(processLocal, ((command,os.path.join(out,'eiger2cbf.log')),))
            time.sleep(0.1)
            if stop:
                break
            st += split
            end += split
            # Check to see if next round will be out of range
            if st >= total:
                break
            if st + split >= total:
                end = total
                stop = True
            if end > total:
                end = total
        pool.close()
        pool.join()

        # Get the detector description from the h5 file
        with open('eiger2cbf.log','r') as f:
            for line in f:
                if line.count('description'):
                    det = line[line.find('=')+2:].strip()
                    break

        # Read header from first image and pass it back.
        header = readHeader(img)

        # change the detector
        header['detector'] = det
        return(header)
    else:
        return('Not master file!!!')
    """
    except:
        if logger:
            logger.exception('**ERROR in Utils.convert_hdf5_cbf**')
        return("FAILED")
    """
def convertImage(self, inp, output):
  """
  Convert image to new type.
  """
  if self.verbose:
    self.logger.debug('Utilities::convertImage')
  #try:
  processLocal('convert %s %s'%(inp,output),self.logger)
  """
  except:
    self.logger.exception('**ERROR in Utils.convertImage**')
  """
def convertSG(self, inp, reverse=False):
    """
    Convert SG to SG#.
    """
    # print "convertSG %s %s" % (inp, reverse)
    if self.verbose:
        self.logger.debug('Utilities::convertSG')

    #CCP4 conversion file /programs/i386-linux/ccp4/6.2.0/ccp4-6.2.0/lib/data/syminfo.lib
    # try:
    std2intl =   {'P1'       : '1'  ,
                  'C121'     : '5'  ,
                  'C2'       : '5'  ,
                  'I121'     : '5.1',
                  'A121'     : '5.2',#2005
                  'A112'     : '5.3',
                  'B112'     : '5.4',#1005
                  'I112'     : '5.5',#4005
                  'P2'       : '3'  ,
                  'P121'     : '3'  ,
                  'P21'      : '4'  ,
                  'P1211'    : '4'  ,
                  'F222'     : '22' ,
                  'I222'     : '23' ,
                  'I212121'  : '24' ,
                  'C222'     : '21' ,
                  'C2221'    : '20' ,
                  'P222'     : '16' ,
                  'P2221'    : '17' ,
                  'P2212'    : '17.1',#2017
                  'P2122'    : '17.2',#1017
                  'P21212'   : '18' ,
                  'P21221'   : '18.1',#2018
                  'P22121'   : '18.2',#3018
                  'P212121'  : '19' ,
                  'I4'       : '79' ,
                  'I41'      : '80' ,
                  'I422'     : '97' ,
                  'I4122'    : '98' ,
                  'P4'       : '75' ,
                  'P41'      : '76' ,
                  'P42'      : '77' ,
                  'P43'      : '78' ,
                  'P422'     : '89' ,
                  'P4212'    : '90' ,
                  'P4122'    : '91' ,
                  'P4322'    : '95' ,
                  'P4222'    : '93' ,
                  'P42212'   : '94' ,
                  'P41212'   : '92' ,
                  'P43212'   : '96' ,
                  'P3'       : '143',
                  'P31'      : '144',
                  'P32'      : '145',
                  'P312'     : '149',
                  'P3112'    : '151',
                  'P3212'    : '153',
                  'P321'     : '150',
                  'P3121'    : '152',
                  'P3221'    : '154',
                  'P6'       : '168',
                  'P61'      : '169',
                  'P65'      : '170',
                  'P62'      : '171',
                  'P64'      : '172',
                  'P63'      : '173',
                  'P622'     : '177',
                  'P6122'    : '178',
                  'P6522'    : '179',
                  'P6222'    : '180',
                  'P6422'    : '181',
                  'P6322'    : '182',
                  'R3'       : '146.1',#1146
                  'H3'       : '146.2',#146
                  'R32'      : '155.1',#1155
                  'H32'      : '155.2',#155
                  'F23'      : '196',
                  'F432'     : '209',
                  'F4132'    : '210',
                  'I23'      : '197',
                  'I213'     : '199',
                  'I432'     : '211',
                  'I4132'    : '214',
                  'P23'      : '195',
                  'P213'     : '198',
                  'P432'     : '207',
                  'P4232'    : '208',
                  'P4332'    : '212',
                  'P4132'    : '213'    }

    mono =       {'C121'     : 'C2',
                  'P121'     : 'P2',
                  'P1211'    : 'P21'}

    if reverse:
        for letters, number in std2intl.items():
            if number == inp:
                if mono.has_key(letters):
                    sg = mono[letters]
                else:
                    sg = letters
    else:
        sg = std2intl[inp]

    return sg

    # except:
    #     self.logger.exception('**ERROR in Utils.convertSG**')

def convert_spacegroup(inp, reverse=False):
    """Convert SG to SG#"""

    # CCP4 conversion file /programs/i386-linux/ccp4/6.2.0/ccp4-6.2.0/lib/data/syminfo.lib
    std2intl = { "P1": "1",
                 "C121": "5",
                 "C2": "5",
                 "I121": "5.1",
                 "A121": "5.2",  # 2005
                 "A112": "5.3",
                 "B112": "5.4",  # 1005
                 "I112": "5.5",  # 4005
                 "P2": "3",
                 "P121": "3",
                 "P21": "4",
                 "P1211": "4",
                 "F222": "22",
                 "I222": "23",
                 "I212121": "24",
                 "C222": "21",
                 "C2221": "20",
                 "P222": "16",
                 "P2221": "17",
                 "P2212": "17.1",  # 2017
                 "P2122": "17.2",  # 1017
                 "P21212": "18",
                 "P21221": "18.1",  # 2018
                 "P22121": "18.2",  # 3018
                 "P212121": "19",
                 "I4": "79",
                 "I41": "80",
                 "I422": "97",
                 "I4122": "98",
                 "P4": "75",
                 "P41": "76",
                 "P42": "77",
                 "P43": "78",
                 "P422": "89",
                 "P4212": "90",
                 "P4122": "91",
                 "P4322": "95",
                 "P4222": "93",
                 "P42212": "94",
                 "P41212": "92",
                 "P43212": "96",
                 "P3": "143",
                 "P31": "144",
                 "P32": "145",
                 "P312": "149",
                 "P3112": "151",
                 "P3212": "153",
                 "P321": "150",
                 "P3121": "152",
                 "P3221": "154",
                 "P6": "168",
                 "P61": "169",
                 "P65": "170",
                 "P62": "171",
                 "P64": "172",
                 "P63": "173",
                 "P622": "177",
                 "P6122": "178",
                 "P6522": "179",
                 "P6222": "180",
                 "P6422": "181",
                 "P6322": "182",
                 "R3": "146.1",  # 1146
                 "H3": "146.2",  # 146
                 "R32": "155.1",  # 1155
                 "H32": "155.2",  # 155
                 "F23": "196",
                 "F432": "209",
                 "F4132": "210",
                 "I23": "197",
                 "I213": "199",
                 "I432": "211",
                 "I4132": "214",
                 "P23": "195",
                 "P213": "198",
                 "P432": "207",
                 "P4232": "208",
                 "P4332": "212",
                 "P4132": "213",
                 }

    mono = {"C121": "C2",
            "P121": "P2",
            "P1211": "P21"}

    if reverse:
        for letters, number in std2intl.items():
            if number == inp:
                if mono.has_key(letters):
                    sg = mono[letters]
                else:
                    sg = letters
    else:
        sg = std2intl[inp]

    return sg

def convertShelxFiles(self,inp):
  """
  Rename phs, hat, and convert phs to mtz for building.
  """
  if self.verbose:
    self.logger.debug('Utilities::convertShelxFiles')
  #try:
  inv = self.shelx_results0[inp].get('Shelx results').get('shelxe_inv_sites')
  if inv == 'True':
    sg = convertSG(self,checkInverse(self,convertSG(self,inp))[0],True)
    h = 'junk_i'
  else:
    sg = inp
    h = 'junk'
  for i in range(2):
    fl = 'phs'
    if i == 1:
      fl = 'hat'
    if os.path.exists('%s.%s'%(h,fl)):
      shutil.copy('%s.%s'%(h,fl),'%s.%s'%(sg,fl))
  """
  except:
    self.logger.exception('**ERROR in Utils.convertShelxFiles**')
  """
def convertUnicode(self,inp=False):
  """
  Convert unicode to Python string for Phenix.
  """
  if self.verbose:
    self.logger.debug('Utilities::convertUnicode')
  if inp == False:
    inp0 = self.datafile
  else:
    inp0 = inp
  if type(inp0) == unicode:
    #out = str(inp0)
    out = inp0.encode('utf8')
  else:
    out = inp0
  return(out)

def convert_unicode(inp):
  """
  Convert unicode to Python string for Phenix.
  """

  if isinstance(inp, unicode):
    out = inp.encode('utf8')
  else:
    out = inp

  return out

def copyShelxFiles(self,inp):
  """
  Symlink the files needed for SHELXE to run in separate folder.
  """
  if self.verbose:
    self.logger.debug('Utilities::copyShelxFiles')

  home = os.getcwd()
  folders2(self,str(inp))
  l = ['junk.hkl','junk_fa.hkl','junk_fa.res']
  for x in range(len(l)):
    if os.path.exists(l[x]) == False:
      os.symlink(os.path.join(home,l[x]),l[x])

def denzo2mosflm(self):
  """
  Convert Denzo A matrix to Mosflm format.
  """
  if self.verbose:
    self.logger.debug('Utilities::denzo2mosflm')
  if self.test:
    os.chdir('/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0')
    align_omega = ['65.641']
  else:
    align_omega = self.stacalign_results.get('STAC align results').get('omega')

  try:
    #temp  = []
    temp2 = []
    #temp3 = []
    #ub = []
    inp = open('name1.x','r')
    a1 = inp[1].split()[0]
    a2 = inp[1].split()[1]
    a3 = inp[1].split()[2]
    b1 = inp[2].split()[0]
    b2 = inp[2].split()[1]
    b3 = inp[2].split()[2]
    c1 = inp[3].split()[0]
    c2 = inp[3].split()[1]
    c3 = inp[3].split()[2]
    line1 = 'UB             ' + c1 + ' ' + c2 + ' ' + c3 + '\n'
    line2 = '               ' + a1 + ' ' + a2 + ' ' + a3 + '\n'
    line3 = '               ' + b1 + ' ' + b2 + ' ' + b3 + '\n'

    omega = 'PHISTART         ' + align_omega[0] + '\n'
    cp = 'cp bestfile.par bestfile_old.par'
    if self.verbose:
      self.logger.debug(cp)
    cp = shutil.copy()
    os.system(cp)
    bestfile = open('bestfile_old.par','r')

    for line in bestfile:
      temp2.append(line)
      if line.startswith('PHISTART'):
        junk1 = temp2.index(line)
        temp2.remove(line)
      if line.startswith('UB'):
        junk = temp2.index(line)
        temp2.remove(line)
      if line.startswith('      '):
        temp2.remove(line)
    bestfile.close()
    temp2.insert(junk1,omega)
    temp2.insert(junk,line1)
    temp2.insert(junk+1,line2)
    temp2.insert(junk+2,line3)
    inp.close()
    out = open('bestfile.par','w')
    out.writelines(temp2)
    out.close()

  except:
    self.logger.exception('**Error in Utils.denzo2mosflm**')

# def distlComb(self):
#   """
#   Combine distl results into 1 inp.
#   """
#   try:
#     if len(self.distl_results.keys()) == 1:
#       self.distl_results = self.distl_results['0']
#     else:
#       d = {}
#       for key in self.distl_results.get('0').get("distl_results").keys():
#         temp = self.distl_results.get('0').get("distl_results")[key]
#         temp.extend(self.distl_results.get('1').get("distl_results")[key])
#         d[key] = temp
#       self.distl_results = {"distl_results" : d}
#       # pprint.pprint(self.distl_results)
#
#   except:
#     self.logger.exception('**Error in Utils.distlComb**')

#Moved Labelit stuff here because it is used by rapd_agent_strategy.py and rapd_agent_beamcenter.py
def errorLabelitPost_OLD(self, iteration, error, run_before=False):
  """
  Do the logging for the error correction in Labelit.
  """

  # pprint(self.labelit_log)

  if self.verbose:
    self.logger.debug('Utilities::errorLabelitPost')
  try:
    if self.multiproc:
      if run_before:
        if self.verbose:
          self.logger.debug(error)
        self.labelit_log[str(iteration)].extend('\n%s\n'%error)
        self.labelit_results[str(iteration)] = { "labelit_results"  : 'FAILED'}
      else:
        self.labelit_log[str(iteration)].extend('\n%s Retrying Labelit\n'%error)
    else:
      if iteration >= self.iterations:
        if self.verbose:
          self.logger.debug("After 3 tries, %s" % error)
        self.labelit_log[str(iteration)].extend("\nAfter 3 tries, %s\n" % error)
      else:
        back_counter = self.iterations-iteration
        if self.verbose:
          self.logger.debug('%s Retrying Labelit %s more time(s)'%(error, back_counter))
        self.labelit_log[str(iteration)].extend('\n%s Retrying Labelit %s more time(s)\n'%(error,back_counter))

  except:
    self.logger.exception('**ERROR in Utils.errorLabelitPost**')

#def errorLabelit(self, iteration=0):
def get_labelit_settings_OLD(self, iteration=0):
    """
    Labelit error correction. Set/reset setting in dataset_preferences.py according to error iteration.
    Commented out things were tried before.
    """

    self.logger.debug('Utilities::errorLabelit')

    # If iteration is string, return the total number of iterations in the funnction.
    if isinstance(iteration, str):
        return 6

    # Create separate folders for Labelit runs.
    if self.multiproc == False:
        iteration += 1
    # Change to the correct folder (create it if necessary).
    foldersLabelit(self, iteration)

    preferences = open('dataset_preferences.py','a')

    preferences.write('\n#iteration %s\n' % iteration)

    if self.twotheta == False:
        preferences.write('beam_search_scope=0.3\n')

    if iteration == 0:
        preferences.close()
        self.labelit_log[iteration] = ['\nUsing default parameters.\n']
        self.tprint("\n  Using default parameters", level=30, color="white", newline=False)
        self.logger.debug('Using default parameters.')

    if iteration == 1:
        # Seemed to pick stronger spots on Pilatis
        if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
            preferences.write('distl.minimum_spot_area=3\n')
            preferences.write('distl.minimum_signal_height=4\n')
        elif "Eiger" in self.vendortype:
            preferences.write('distl.minimum_spot_area=3\n')
            preferences.write('distl.minimum_signal_height=5.5\n')
        else:
            preferences.write('distl.minimum_spot_area=6\n')
            preferences.write('distl.minimum_signal_height=4.3\n')
        preferences.close()
        self.labelit_log[iteration] = ['\nLooking for long unit cell.\n']
        self.tprint("\n  Looking for long unit cell", level=30, color="white", newline=False)
        self.logger.debug('Looking for long unit cell.')

    elif iteration == 2:
        # Change it up and go for larger peaks like small molecule.
        preferences.write('distl.minimum_spot_height=6\n')
        preferences.close()
        self.labelit_log[iteration] = ['\nChanging settings to look for stronger peaks (ie. small molecule).\n']
        self.tprint("\n  Looking for stronger peaks (ie. small molecule)", level=30, color="white", newline=False)
        self.logger.debug("Changing settings to look for stronger peaks (ie. small molecule).")

    elif iteration == 3:
        if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
            preferences.write('distl.minimum_spot_area=2\n')
            preferences.write('distl.minimum_signal_height=2.3\n')
        elif "Eiger" in self.vendortype:
            preferences.write('distl.minimum_spot_area=3\n')
            preferences.write('distl.minimum_signal_height=2.6\n')
        else:
            preferences.write('distl.minimum_spot_area=7\n')
            preferences.write('distl.minimum_signal_height=1.2\n')
        preferences.close()
        self.labelit_log[iteration] = ['\nLooking for weak diffraction.\n']
        self.tprint("\n  Looking for weak diffraction", level=30, color="white", newline=False)
        self.logger.debug('Looking for weak diffraction.')

    elif iteration == 4:
        if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
            preferences.write('distl.minimum_spot_area=3\n')
            self.labelit_log[iteration] = ['\nSetting spot picking level to 3.\n']
            area = 3
        elif "Eiger" in self.vendortype:
            preferences.write('distl.minimum_spot_area=3\n')
            self.labelit_log[iteration] = ['\nSetting spot picking level to 3.\n']
            area = 3
        else:
            preferences.write('distl.minimum_spot_area=8\n')
            self.labelit_log[iteration] = ['\nSetting spot picking level to 8.\n']
            area = 8
        preferences.close()
        self.tprint("\n  Setting spot picking level to %d" % area, level=30, color="white", newline=False)
        self.logger.debug('Setting spot picking level to 3 or 8.')

    elif iteration == 5:
        if "Pilatus" in self.vendortype or "HF4M" in self.vendortype:
            preferences.write('distl.minimum_spot_area=2\n')
            preferences.write('distl_highres_limit=5\n')
            self.labelit_log[iteration] = ['\nSetting spot picking level to 2 and resolution to 5.\n']
            setting = (2, 5)
        elif "Eiger" in self.vendortype:
            preferences.write('distl.minimum_spot_area=2\n')
            preferences.write('distl_highres_limit=4\n')
            self.labelit_log[iteration] = ['\nSetting spot picking level to 2 and resolution to 4.\n']
            setting = (2, 4)
        else:
            preferences.write('distl.minimum_spot_area=6\n')
            preferences.write('distl_highres_limit=5\n')
            self.labelit_log[iteration] = ['\nSetting spot picking level to 6 and resolution to 5.\n']
            setting = (6, 5)
        preferences.close()
        self.tprint("\n  Setting spot picking level to %d and hires limit to %d" % setting, level=30, color="white", newline=False)
        self.logger.debug('Setting spot picking level to 2 or 6.')

    return self.process_labelit(iteration)

def errorLabelitMin_OLD(self, iteration, line):
  """
  Labelit error correction. Reset min spots allowed. Set/reset setting in dataset_preferences.py according
  to error iteration. Only run in multiproc mode.
  """

  self.logger.debug('Utilities::errorLabelitMin')

  try:
    spots = int(line[line.find('=')+1:])
    # Minimum number of spots to define a blank image.
    if spots < 25:
      if self.verbose:
        self.logger.debug('Not enough spots to autoindex!')
      self.labelit_log[str(iteration)].extend('\nNot enough spots to autoindex!\n')
      self.postprocess_labelit(iteration, True, True)
      return None
    else:
      preferences = open('dataset_preferences.py', 'a')
      preferences.write('%s\n' % line)
      preferences.close()
      return(self.process_labelit(iteration))

  except:
    self.logger.exception('**ERROR in Utils.errorLabelitMin**')
    self.labelit_log[str(iteration)].extend('\nCould not change spot finding settings in dataset_preferences.py file.\n')
    return(None)

def errorLabelitFixCell_OLD(self,iteration,lg,labelit_sol):
  """
  Pick correct cell (lowest rmsd) if multiple cell choices are possible in user selected SG and rerun Labelit.
  """
  if self.verbose:
    self.logger.debug('Utilities::errorLabelitFixCell')
  try:
    rmsd = []
    m = False
    for i in range(2):
      if i == 1:
        m = min(rmsd)
      for line in labelit_sol:
        if line[7] == lg:
          if i == 0:
            rmsd.append(float(line[4]))
          else:
            if line[4] == str(m):
              cell = 'known_cell=%s,%s,%s,%s,%s,%s'%(line[8],line[9],line[10],line[11],line[12],line[13])
    return(self.process_labelit(iteration,inp=cell))

  except:
    self.logger.exception('**Error in Utils.errorLabelitFixCell**')
    return(None)

def errorLabelitCellSG_OLD(self,iteration):
  """
  #Retrying Labelit without using user specified unit cell params.
  """
  if self.verbose:
    self.logger.debug('Utilities::errorLabelitCellSG')
  try:
    self.ignore_user_cell = True
    self.ignore_user_SG = True
    self.labelit_log[str(iteration)].extend('\nIgnoring user cell and SG command and rerunning.\n')
    return (self.process_labelit(iteration))

  except:
    self.logger.exception('**ERROR in Utils.errorLabelitCellSG**')
    return(None)

def errorLabelitBump_OLD(self,iteration):
  """
  Get rid of distl_profile_bumpiness line in dataset_preferences.py. Don't think I use much anyway.
  """
  if self.verbose:
    self.logger.debug('Utilities::errorLabelitBump')
  try:
    temp1 = []
    for line in open('dataset_preferences.py','r').readlines():
      temp1.append(line)
      if line.startswith('distl_profile_bumpiness'):
        temp1.remove(line)
    preferences = open('dataset_preferences.py','w')
    preferences.writelines(temp1)
    preferences.close()
    return (self.process_labelit(iteration))

  except:
    self.logger.exception('**ERROR in Utils.errorLabelitBump**')
    self.labelit_log[str(iteration)].extend('\nCould not remove distl_profile_bumpiness line in dataset_preferences.py file.\n')
    return(None)

def errorLabelitGoodSpots_OLD(self,iteration):
  """
  Sometimes Labelit gives an eror saying that there aren't enough 'good spots' for Mosflm. Not a Labelit
  failure error. Forces Labelit/Mosflm to give result regardless. Sometimes causes failed index.
  """
  if self.verbose:
    self.logger.debug('Utilities::errorLabelitGoodSpots')
  try:
    foldersLabelit(self,iteration)
    preferences    = open('dataset_preferences.py','a')
    if self.verbose:
      self.logger.debug('Changing preferences to allow less spots for autoindexing')
    if self.min_good_spots:
      preferences.write('\n#iteration %s\n'%iteration)
      preferences.write('model_refinement_minimum_N=%s'%self.min_good_spots)
      preferences.close()
      self.labelit_log[str(iteration)].extend('\nSetting min number of good bragg spots to %s.\n'%self.min_good_spots)
      if self.verbose:
        self.logger.debug('Setting min number of good bragg spots to %s'%self.min_good_spots)
      return (self.process_labelit(iteration))
    else:
      return(None)

  except:
    self.logger.exception('**ERROR in Utils.errorLabelitGoodSpots**')
    self.labelit_log[str(iteration)].extend('\nCould not change min number of good bragg spots settings in dataset_preferences.py file.\n')
    return(None)

def errorLabelitMosflm_OLD(self,iteration):
    """
    Set Mosflm integration resolution lower. Seems to fix this error.
    """
    if self.verbose:
        self.logger.debug('Utilities::errorLabelitMosflm')
    try:
        foldersLabelit(self,iteration)
        #'index01' will always be present since it is P1
        preferences = open('dataset_preferences.py','a')
        for line in open('index01','r').readlines():
            if line.startswith('RESOLUTION'):
                new_res = float(line.split()[1])+1.00
                preferences.write('\n#iteration %s\nmosflm_integration_reslimit_override = %s\n'%(iteration,new_res))
                self.labelit_log[str(iteration)].extend('\nDecreasing integration resolution to %s and rerunning.\n'%new_res)
        preferences.close()
        return (self.process_labelit(iteration))

    except:
        self.logger.exception('**ERROR in Utils.errorLabelitMosflm**')
        self.labelit_log[str(iteration)].extend('\nCould not reset Mosflm resolution.\n')
        return None

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

def errorBest_OLD(self, iteration=0, best_version="3.2.0"):
    """
    Run all the Best runs at the same time.
    Reduce resolution limit and rerun Mosflm to calculate new files.
    """

    if self.verbose:
        self.logger.debug("Utilities::errorBest")

    try:
        if iteration != 0:
            if self.test == False:
                temp = []
                f = "%s_res%s"%(self.index_number, iteration)
                shutil.copy(self.index_number, f)
                for line in open(f, "r").readlines():
                    temp.append(line)
                    if line.startswith("RESOLUTION"):
                        temp.remove(line)
                        temp.append("RESOLUTION %s\n" % str(float(line.split()[1]) + iteration))
                new = open(f, "w")
                new.writelines(temp)
                new.close()
                subprocess.Popen("sh %s" % f, shell=True).wait()
        self.process_best(iteration, best_version)

    except:
        self.logger.exception("**ERROR in Utils.errorBest**")
        self.best_log.append("\nCould not reset Mosflm resolution for Best.\n")

def errorBestPost_OLD(self,iteration,error,anom=False):
  """
  Post error to proper log in postprocessBest.
  """
  if self.verbose:
    self.logger.debug('Utilities::errorBestPost')
  try:
    if anom:
      j = ['ANOM','_anom']
    else:
      j = ['','']
    if self.verbose:
      self.logger.debug(error)
    if iteration >= 3:
      line = 'After 3 tries, Best %s failed. Will run Mosflm %s strategy'%(j[0],j[0])
      if self.verbose:
        self.logger.debug(line)
    else:
      iteration += 1
      back_counter = 4 - iteration
      line = 'Error in Best %s strategy. Retrying Best %s more time(s)'%(j[0],back_counter)
      if self.verbose:
        self.logger.debug(line)
    eval('self.best%s_log'%j[1]).append('\n%s'%line)

  except:
    self.logger.exception('**Error in Utils.errorBestPost**')

def failedHTML_OLD(self, inp):
  """
  Generates failed html to output for GUI. FOR RAPD1!!
  """
  if self.verbose:
    self.logger.debug('Utilities::failedHTML')
  #try:
  if type(inp) == tuple:
    name,error = inp
  else:
    name = inp
    error = False
  f = getHTMLHeader(self)
  f +='%6s$(document).ready(function() {\n'%''
  f +='%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',))
  f +='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
  if error:
    f +='%7s<h3 class="results">%s</h3>\n'%('',error)
  elif self.failed:
    f +='%7s<h3 class="results">Input data could not be analysed.</h3>\n'%''
  else:
    f +='%7s<h3 class="results">There was an error during data analysis or it timed out</h3>\n'%''
  f +='%6s</div>\n%5s</div>\n%4s</div>\n%2s</body>\n</html>\n'%(4*('',))
  if self.gui:
    sp = '%s.php'%name
  else:
    sp = '%s.html'%name
  junk = open(sp,'w')
  junk.writelines(f)
  junk.close()
  if os.path.exists(os.path.join(self.working_dir,sp)) == False:
    shutil.copy(sp,self.working_dir)
  """
  except:
    self.logger.exception('**ERROR in Utils.failedHTML**.')
  """
def fixBestSG(self):
    """
    Make user selected SG correct for BEST.
    """
    if self.verbose:
        self.logger.debug("Utilities::fixBestSG")
    #try:
    temp = []
    shutil.copy("bestfile.par", "bestfile_orig.par")
    if self.verbose:
        self.logger.debug("Since user selected the space group, BEST files will be edited to match.")
    for x,line in enumerate(open("bestfile_orig.par", "r").readlines()):
        temp.append(line)
        if line.startswith("SYMMETRY"):
            if line.split()[1] != self.spacegroup:
                temp.remove(line)
                temp.insert(x, line.replace(line.split()[1], self.spacegroup))
    new = open("bestfile.par", "w")
    new.writelines(temp)
    new.close()
    """
    except:
        self.logger.exception("**ERROR in Utils.fixBestSG**")
    """
def fixBestSGBack_OLD(self):
  """
  Best will fail if user selected SG is not found in autoindexing. This brings back the autoindexed SG.
  """
  if self.verbose:
    self.logger.debug('Utilities::fixBestSGBack')
  try:
    if self.verbose:
      self.logger.debug('The user selected SG was not found in autoindexing.')
    shutil.copy('bestfile_orig.par','bestfile.par')

  except:
    self.logger.exception('**ERROR in Utils.fixBestSGBack**')

def fix_bestfile():
    """
    Fix the 'BEAM SWUNG_OUT' line in case of 2 theta usage.
    """
    #self.logger.debug('Utilities::fixBestfile')

    temp = []
    tt = False
    for i,line in enumerate(open('bestfile.par','r').readlines()):
        temp.append(line)
        if line.startswith('BEAM'):
            if line.split()[1] == 'SWUNG_OUT':
                tt = True
                temp.remove(line)
                temp.insert(i,'BEAM           %s %s\n'%(line.split()[2],line.split()[3]))
    if tt:
        shutil.copy('bestfile.par', 'bestfile_orig.par')
        with open('bestfile.par', 'w') as new:
            new.writelines(temp)
            new.close()

def fixBestfile_OLD(self):
    """
    Fix the 'BEAM SWUNG_OUT' line in case of 2 theta usage.
    """
    self.logger.debug('Utilities::fixBestfile')
    # try:
    temp = []
    tt = False
    #r3 = False
    for i,line in enumerate(open('bestfile.par','r').readlines()):
        temp.append(line)
        if line.startswith('BEAM'):
            if line.split()[1] == 'SWUNG_OUT':
                tt = True
                temp.remove(line)
                temp.insert(i,'BEAM           $s %s\n'%(line.split()[2],line.split()[3]))
    if tt:
        shutil.copy('bestfile.par', 'bestfile_orig.par')
        new = open('bestfile.par', 'w')
        new.writelines(temp)
        new.close()

    # except:
    #   self.logger.exception('**ERROR in Utils.fixBestfile**')

def fixMosflmSG(self):
  """
  Make user selected SG correct for Mosflm.
  """
  if self.verbose:
    self.logger.debug('Utilities::fixMosflmSG')
  #try:
  temp = []
  mfile = os.path.join(self.labelit._dir,self.index_number)
  shutil.copy(mfile,'%s_orig'%mfile)
  if self.verbose:
    self.logger.debug('Since user selected the space group, Mosflm files will be edited to match.')
  for x,line in enumerate(open(mfile,'r').readlines()):
    temp.append(line)
    if line.startswith('SYMMETRY'):
      if line.split()[1] != self.spacegroup:
        temp.remove(line)
        temp.insert(x,'SYMMETRY %s\n'%self.spacegroup)
  new = open('%s'%os.path.join(self.labelit._dir, self.index_number),'w')
  new.writelines(temp)
  new.close()
  """
  except:
    self.logger.exception('**ERROR in Utils.fixMosflmSG**')
  """
def fixMosflmSGBack_OLD(self):
  """
  Best will fail if user selected SG is not found in autoindexing. This brings back the autoindexed SG.
  """
  if self.verbose:
    self.logger.debug('Utilities::fixMosflmSGBack')
  try:
    shutil.copy('%s_orig'%self.index_number,'%s'%self.index_number)
    if self.verbose:
      self.logger.debug('The user selected SG was not found in autoindexing.')

  except:
    self.logger.exception('**ERROR in Utils.fixMosflmSGBack**')

def fixSCA(self,inp=False):
  """
  #Fix spaces in SG and * in sca file.
  """
  #if self.verbose:
    #self.logger.debug('Utilities::fixSCA')
  #try:
  if inp:
    sca = inp
  else:
    sca = self.datafile
  temp = []
  lines_fixed = 0
  old_sca = sca.replace('.sca','_orig.sca')
  shutil.copy(sca,old_sca)
  junk = open(old_sca, 'r').readlines()[2]
  if inp == False:
    if self.input_sg:
      junk2 = junk.replace(junk[61:-1],self.input_sg)
  for line in open(old_sca,'r').readlines():
    temp.append(line)
    if inp == False:
      if line.startswith(junk):
        if self.input_sg:
          temp.remove(line)
          temp.insert(2,junk2)
    #Fix *'s in sca file
    if line.count('*'):
      temp.remove(line)
      lines_fixed += 1
  out = open(sca,'w')
  out.writelines(temp)
  out.close()
  self.logger.debug('Number of lines fixed in the SCA file: %s'%lines_fixed)
  """
  except:
    self.logger.exception('**ERROR in Utils.fixSCA**')
  """
def fix_mtz_to_sca(input_file):
    """Fix spaces in SG and * in sca file"""

    new_lines = []

    # Read in the input sca file symmetry line and correct
    symmetry_line = open(input_file, "r").readlines()[2]
    corrected_symmetry_line = (
        symmetry_line[:symmetry_line.index(symmetry_line.split()[6])]
        + ''.join(symmetry_line.split()[6:]) + "\n")

    for line in open(input_file, "r").readlines():

        # Broken line
        if line.startswith(symmetry_line):
            line = corrected_symmetry_line

        # Throw out lines with * in them
        if "*" in line:
            continue

        # This line is a keeper
        new_lines.append(line)

    # Write out the file
    with open(input_file, "w") as output_file:
        output_file.writelines(new_lines)

def fix_spacegroup(spacegroup):
    """Fix input SG if R3/R32"""

    # print "fix_spacegroup", spacegroup

    if spacegroup == "H3":
        return "R3"
    elif spacegroup == 'H32':
        return "R32"
    elif spacegroup == "R3:H":
        return "R3"
    elif spacegroup == "R32:H":
        return "R32"
    else:
        return spacegroup

def fix_R3_sg(inp):
    """
    Fix input SG if R3/R32.
    """

    # try:
    if inp == "R3":
        return "H3"
    elif inp == "R32":
        return "H32"
    else:
        return inp

    # except:
    #   self.logger.exception('**ERROR in Utils.fixR3SG**')

def foldersLabelit(self, iteration=0):
  """
  Sets up new directory and changes to it for each error iteration in multiproc_labelit.
  """
  if self.verbose:
    self.logger.debug('Utilities::foldersLabelit')
  #try:
  if os.path.exists(os.path.join(self.working_dir, str(iteration))):
    copy = False
  else:
    copy = True
  folders(self, iteration)
  if copy:
    pref = 'dataset_preferences.py'
    pref_path = os.path.join(self.working_dir, pref)
    shutil.copy(pref_path, pref)
  """
  except:
    self.logger.exception('**Error in Utils.foldersLabelit**')
  """
def create_folders_labelit(working_dir, iteration=0):
    """
    Sets up new directory and changes to it for each error iteration in multiproc_labelit.
    """

    target_directory = os.path.join(working_dir, str(iteration))

    if os.path.exists(target_directory):
        copy = False
    else:
        copy = True

    # Create and move to the target_directory
    create_folder(target_directory)

    if copy:
        pref = 'dataset_preferences.py'
        pref_path = os.path.join(working_dir, pref)
        shutil.copy(pref_path, pref)

def foldersStrategy_OLD2(self, iteration=0):
  """
  Sets up new directory for programs.
  """
  if self.verbose:
    self.logger.debug('Utilities::foldersStrategy')
  #try:
  if os.path.exists(os.path.join(self.working_dir,str(iteration))):
    copy = False
  else:
    copy = True
  folders(self,iteration)
  if copy:
    if iteration[-1] == '0':
      # Does this even work? there is bestfile.dat and .par?
      os.system('cp %s/bestfile* %s/%s*.hkl .'%(self.labelit_dir,self.labelit_dir,self.index_number))
    shutil.copy(os.path.join(self.labelit_dir,self.index_number),os.getcwd())
    shutil.copy(os.path.join(self.labelit_dir,'%s.mat'%self.index_number),os.getcwd())
    if self.header2:
      shutil.copy(os.path.join(self.labelit_dir,'%s_S.mat'%self.index_number),os.getcwd())
    #For Pilatis background calc.
    if self.vendortype in ('Pilatus-6M','ADSC-HF4M'):
    #if self.pilatus:
      if os.path.exists(os.path.join(self.working_dir,'BKGINIT.cbf')):
        shutil.copy(os.path.join(self.working_dir,'BKGINIT.cbf'),os.getcwd())
  """
  except:
    self.logger.exception('**Error in Utils.foldersStrategy**')
  """
def foldersStrategy_OLD(self, iteration=0):
  """
  Sets up new directory for programs.
  """
  if self.verbose:
    self.logger.debug('Utilities::foldersStrategy')
  #try:
  #if os.path.exists(os.path.join(self.working_dir,str(iteration))):
  new_folder = os.path.join(self.labelit_dir,str(iteration))
  if os.path.exists(new_folder):
    copy = False
  else:
    copy = True
  #folders(self,iteration)
  folders2(self, new_folder)
  if copy:
    if iteration == 0:
      os.system('cp %s/bestfile* %s/%s*.hkl .'%(self.labelit_dir,self.labelit_dir,self.index_number))
    #shutil.copy(os.path.join(self.labelit_dir,self.index_number),new_folder)
    shutil.copy(os.path.join(self.labelit_dir,'%s.mat'%self.index_number),new_folder)
    if self.header2:
      shutil.copy(os.path.join(self.labelit_dir,'%s_S.mat'%self.index_number),new_folder)
    #For Pilatis background calc.
    if self.vendortype in ('Pilatus-6M','ADSC-HF4M'):
    #if self.pilatus:
      if os.path.exists(os.path.join(self.working_dir,'BKGINIT.cbf')):
        shutil.copy(os.path.join(self.working_dir,'BKGINIT.cbf'),new_folder)
  """
  except:
    self.logger.exception('**Error in Utils.foldersStrategy**')
  """
def folders(self,inp=None):
  """
  Sets up new directory for programs.

  if self.verbose:
    self.logger.debug('Utilities::folders')
  """
  #try:
  if inp != None:
    dir1 = os.path.join(self.working_dir,str(inp))
  else:
    dir1 = self.working_dir
  if os.path.exists(dir1) == False:
    os.mkdir(dir1)
    #os.makedirs(dir1)
  os.chdir(dir1)
  """
  except:
    self.logger.exception('**Error in Utils.folders**')
  """
def create_folders(working_dir=None, new_dir=None):
    """Creates and moves to a new directory"""

    if working_dir == None:
        working_dir = os.getcwd()

    if new_dir != None:
        target_dir = os.path.join(working_dir, new_dir)
    else:
        target_dir = working_dir

    if os.path.exists(target_dir) == False:
        os.mkdir(target_dir)

    os.chdir(target_dir)

def create_folder(target_directory, move_to=True):
    """
    Sets up new directory and move to it.
    """

    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    # Move to the directory
    if move_to:
        os.chdir(target_directory)

def folders2(self,inp=None):
  """
  Sets up new directory for programs.
  """
  if self.verbose:
    self.logger.debug('Utilities::folders2')
  #try:
  if inp != None:
    if inp.startswith('/'):
      dir1 = inp
    else:
      dir1 = os.path.join(os.getcwd(),str(inp))
  else:
    dir1 = self.working_dir
  if os.path.exists(dir1) == False:
    #os.mkdir(dir1)
    os.makedirs(dir1)
  os.chdir(dir1)
  """
  except:
    self.logger.exception('**Error in Utils.folders2**')
  """
def getmmCIF(self,inp):
  """
  Symlink the path of the mmCIF to local folder.
  """
  if self.verbose:
    self.logger.debug('Utilities::getmmCIF')
  import os
  #try:
  path = '/gpfs5/users/necat/rapd/pdbq/pdb/%s/%s.cif'%(inp[1:3].lower(),inp.lower())
  new_path = os.path.join(os.getcwd(),os.path.basename(path))
  #If symlink is already there, pass it back, otherwise create it.
  if os.path.exists(new_path) == False:
    os.symlink(path,new_path)
  return(new_path)
  #except:
  #  self.logger.exception('**Error in Utils.getmmCIF**')

def getHTMLHeader_OLD(self,inp=False):
  """
  Return PHP header for output HTML files.
  """
  if self.verbose:
    self.logger.debug('Utilities::getHTMLHeader')
  s = ''
  if self.gui:
    s +="<?php\n//prevents caching\n"
    s +='header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n'
    s +='header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n'
    s +='header("Cache-Control: post-check=0, pre-check=0",false);\n'
    s +="session_cache_limiter();\nsession_start();\n"
    s +="require('/var/www/html/rapd/login/config.php');\n"
    s +="require('/var/www/html/rapd/login/functions.php');\n"
    s +="//prevents unauthorized access\n"
    s +='if(allow_user() != "yes")\n{\n'
    s +='%2sif(allow_local_data($_SESSION[data]) != "yes")\n%2s{\n'%('','')
    s +="%4sinclude ('./login/no_access.html');\n%4sexit();\n%2s}\n}\n?>\n\n"%(3*('',))
    s +='<html>\n%2s<head>\n%4s<style type="text/css" media="screen">\n'%('','')
  else:
    #s +='<html>\n%2s<head>\n%4s<style type="text/css" media="screen">\n'%('','')
    s +='<html>\n%2s<head>\n%4s<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'%('','')
    s +='%4s<style type="text/css" media="screen">\n'%''
  if self.gui == False:
    s +='%6s@import "../css/rapd.css";\n'%''
    s +='%6s@import "../css/ndemo_page.css";\n'%''
    s +='%6s@import "../css/ndemo_table.css";\n'%''
    s +='%6s@import "../css/thickbox.css";\n'%''
    s +='%6s@import "../css/south-street/jquery-ui-1.7.2.custom.css";\n'%''
  s +='%6sbody { background-image: none; }\n'%''
  if inp == 'plots':
    s +="%6s.y-label {width:7px; position:absolute; text-align:center; top:300px; left:15px; }\n"%''
    s +="%6s.x-label {position:relative; text-align:center; top:10px; }\n"%''
    s +="%6s.title {font-size:30px; text-align:center;} \n"%''
  else:
    s +='%6s.dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both; }\n'%''
    s +='%6stable.display td {padding: 1px 7px;}\n'%''
    if inp == 'pdbquery':
      s +='%6std.Small {font-size: 8pt;}\n'%''
    if inp == 'xtriage':
      #Reset text to normal position in summary.
      s += '%6sP.t {margin-top: 0;}\n'%''
    if inp in ('phaser','pdbquery'):
      s +='%6str.GradeAA {font-style: italic; color: gray;}\n'%''
      #For line separators
      s +='%6str.GradeE {background-color:gray;}\n'%''
      #For best solution
      s +='%6str.GradeF {background-color:#fbb117;font-weight: bold;}\n'%''
      #For still running jobs
      s +='%6str.GradeH {background-color:#98ff98;}\n'%''
    if inp in ('anom','pdbquery'):
      s +='%6str.GradeDD {font-weight: bold;}\n'%''
    if inp in ('anom','phaser'):
      #For SG listing (phaser) and SHELXC (anom)
      s +='%6std.Name0 {background-color:#d1ffd1;font-weight:bold;font-style:normal;color:black;}\n'%''
      s +='%6std.Name1 {background-color:#e2ffe2;font-weight:bold;font-style:normal;color:black;}\n'%''
  s +='%4s</style>\n'%''
  if self.gui == False:
    if inp == 'plots':
      s +='%4s<script src="../js/jquery-1.6.3.min.js" type="text/javascript"></script>\n'%''
      s +='%4s<script src="../js/jquery-ui-1.8.11.min.js" type="text/javascript"></script>\n'%''
      s +='%4s<script src="../js/jquery.flot.0.6.min.js" type="text/javascript"></script>\n'%''
    else:
      s +='%4s<script type="text/javascript" language="javascript" src="../js/jquery-1.6.3.min.js"></script>\n'%''
      s +='%4s<script type="text/javascript" language="javascript" src="../js/jquery-ui-1.8.11.min.js"></script>\n'%''
      s +='%4s<script type="text/javascript" language="javascript" src="../js/jquery.dataTables.1.7.1.min.js"></script>\n'%''
      #s +='%4s<script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n'%''
  s +='%4s<script type="text/javascript" charset="utf-8">\n'%''
  return(s)

def getMTZInfo(self, inp=False, convert=True, volume=False):
  """
  Get unit cell and SG from input data regardless of file type.
  """
  if self.verbose:
      self.logger.debug('Utilities::getMTZInfo')
  from iotbx import mtz
  sg = False
  cell = False
  cell2 = False
  vol = False
  try:
    if inp == False:
      inp = self.datafile
    if type(inp) == unicode:
      inp = convertUnicode(self,inp)
    if os.path.basename(inp).upper()[-3:] == 'SCA':
      fixSCA(self,inp)
      inp = sca2mtz(self)
      if convert:
        #For rapd_agent_phaser.py
        self.datafile = inp
      else:
        #For rapd_agent_anom.py so original SCA file used in SHELX.
        self.autosol_datafile = inp
    data = mtz.object(inp)
    sg = fix_R3_sg(self,data.space_group_name().replace(' ',''))
    cell2 = [str(round(x,3)) for x in data.crystals()[0].unit_cell_parameters() ]
    cell = ' '.join(cell2)
    if volume:
      vol = data.crystals()[0].unit_cell().volume()

  except:
    # Should have converted file to MTZ...
    self.logger.debug('Input file is not mtz')

    # Run in SAD since input is converted to SCA for SHELX
    junk = open(inp,'r').readlines()[2]

    # Save unit cell info
    cell2 = junk.split()[:6]
    cell = ' '.join(cell2)

    # Save correct SG info and fix sca file
    sg = junk[61:-1].upper().replace(' ','')

  if volume:
      return(sg, cell, cell2, vol)
  else:
      return(sg, cell, cell2, 0)

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

def getPDBInfo_OLD(self,inp,matthews=True,cell_analysis=False):
  """
  Get info from PDB of mmCIF file.
  """
  from iotbx import pdb
  if self.verbose:
    self.logger.debug('Utilities::PDBInfo')
  #try:
  #get resolution limit for Matthews Calc. Only called once.
  if self.dres:
    res0 = self.dres
  else:
    res0 = getRes(self)
  #Get rid of ligands and water so Phenix won't error.
  #cleanPDB(self,inp)
  np = 0
  na = 0
  nmol = 1
  sc = 0.55
  nchains = 0
  res1 = 0.0
  d = {}
  l = []
  inp = convertUnicode(self,inp)
  if inp[-3:].lower() == 'cif':
    import iotbx.pdb.mmcif
    root = pdb.mmcif.cif_input(file_name=inp).construct_hierarchy()
  else:
    root = pdb.input(inp).construct_hierarchy()
  #print rsam.structure_weight(root,mmt.PROTEIN)
  for chain in root.models()[0].chains():
    np1 = 0
    na1 = 0
    #Sometimes Hetatoms are AA with same segid.
    if l.count(chain.id) == 0:
      l.append(chain.id)
      repeat = False
      nchains += 1
    else:
      repeat = True
    #Count the number of AA and NA in pdb file.
    for rg in chain.residue_groups():
      if rg.atoms()[0].parent().resname in pdb.common_residue_names_amino_acid:
        np1 += 1
      if rg.atoms()[0].parent().resname in pdb.common_residue_names_rna_dna:
        na1 += 1
      #not sure if I get duplicates?
      if rg.atoms()[0].parent().resname in pdb.common_residue_names_ccp4_mon_lib_rna_dna:
        na1 += 1
    #Limit to 10 chains?!?
    if nchains < 10:
      #Do not split up PDB if run from cell analysis
      if cell_analysis == False and repeat == False:
        #Save info for each chain.
        if np1 or na1:
          #Write new pdb files for each chain.
          temp = pdb.hierarchy.new_hierarchy_from_chain(chain)
          #Long was of making sure that user does not have directory named '.pdb' or '.cif'
          n = os.path.join(os.path.dirname(inp),'%s_%s.pdb'%(os.path.basename(inp)[:os.path.basename(inp).find('.')],chain.id))
          if self.test == False:
            temp.write_pdb_file(file_name=n)
          if matthews:
            # Run Matthews Calc. on chain
            nmol, sc, res1 = runPhaserModule(self, (np1, na1, res0, n))
          else:
            res1 = runPhaserModule(self, n)
          d[chain.id] = {'file':n,
                         'NRes':np1+na1,
                         'MWna':na1*330,
                         'MWaa':np1*110,
                         'MW':na1*330+np1*110,
                         'NMol':nmol,
                         'SC':sc,
                         'res':res1,}
    np += np1
    na += na1

  #Run on entire PDB
  if matthews:
    nmol,sc,res1 = runPhaserModule(self,(np,na,res0,inp))
  else:
    res1 = runPhaserModule(self,inp)
  d['all'] = {'file':inp,
              'NRes':np+na,
              'MWna':na*330,
              'MWaa':np*110,
              'MW':na*330+np*110,
              'NMol':nmol,
              'SC':sc,
              'res':res1}
  return(d)
  """
  except:
    self.logger.exception('**ERROR in Utils.getPDBInfo')
    return(False)
  """
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
            if cell_analysis == False and repeat == False:

                # Save info for each chain.
                if np1 or na1:

                    # Write new pdb files for each chain.
                    temp = iotbx_pdb.hierarchy.new_hierarchy_from_chain(chain)

                    # Long was of making sure that user does not have directory named '.pdb' or
                    # '.cif'
                    n = os.path.join(os.path.dirname(cif_file), "%s_%s.pdb" % \
                        (os.path.basename(cif_file)[:os.path.basename(cif_file).find('.')], \
                        chain.id))
                    temp.write_pdb_file(file_name=n)
                    if matthews:
                        # Run Matthews Calc. on chain
                        phaser_return = run_phaser_module((np1, na1, dres, n, data_file))
                    else:
                        res1 = run_phaser_module(n)

                    d[chain.id] = {'file': n,
                                   'NRes': np1+na1,
                                   'MWna': na1*330,
                                   'MWaa': np1*110,
                                   'MW': na1*330+np1*110,
                                   'NMol': phaser_return["z"],
                                   'SC': phaser_return["solvent_content"],
                                   'res': phaser_return["target_resolution"]}
        np += np1
        na += na1

    # Run on entire PDB
    if matthews:
        phaser_return = run_phaser_module((np, na, dres, cif_file, data_file))
        d['all'] = {'file': cif_file,
                    'NRes': np+na,
                    'MWna': na*330,
                    'MWaa': np*110,
                    'MW': na*330+np*110,
                    'NMol': phaser_return["z"],
                    'SC': phaser_return["solvent_content"],
                    'res': phaser_return["target_resolution"]}
    else:
        phaser_return = run_phaser_module((np, na, dres, cif_file, data_file))
        d['all'] = {'file': cif_file,
                    'NRes': np+na,
                    'MWna': na*330,
                    'MWaa': np*110,
                    'MW': na*330+np*110,
                    'NMol': phaser_return["z"],
                    'SC': phaser_return["solvent_content"],
                    'res': phaser_return["target_resolution"]}
    return d

def getSGInfo_OLD(self,inp):
  """
  Get info from PDB of mmCIF file.
  """
  from iotbx import pdb
  if self.verbose:
    self.logger.debug('Utilities::getSGInfo')
  try:
    inp = convertUnicode(self,inp)
    if inp[-3:].lower() == 'cif':
      fail = False
      sg = False
      try:
        f = open(inp,'r').read(20480)
      except IOError:
        #File does not exist
        return(False)
      for line in f.split('\n'):
        if line.count('_symmetry.space_group_name_H-M'):
          sg = line[32:].strip()[1:-1].upper().replace(' ','')
          #sg = line[line.find('"')+1:line.rfind('"')].upper().replace(' ','')
        if line.count('_pdbx_database_status.pdb_format_compatible'):
          if line.split()[1] == 'N':
            fail = True
      if fail:
        return(False)
      else:
        if sg == False:
          self.logger.debug(inp)
        return(sg)
      """
      #Hangs on large files
      import iotbx.pdb.mmcif
      f = iotbx.pdb.mmcif.cif_input(inp)
      print dir(f)

      print str(f.crystal_symmetry())
      print str(f.crystal_symmetry().space_group_info())

      sg = str(f.crystal_symmetry().space_group_info()).upper().replace(' ','')
      print 'got hre2'
      return(str(iotbx.pdb.mmcif.cif_input(inp).crystal_symmetry().space_group_info()).upper().replace(' ',''))
      """
    else:
      return(str(pdb.input(inp).crystal_symmetry().space_group_info()).upper().replace(' ',''))
  except:
    self.logger.exception('**ERROR in Utils.getSGInfo')
    return(False)

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

def getLabelitCell_OLD(self,inp=False):
  """
  Get unit cell from Labelit results.
  """
  if self.verbose:
    self.logger.debug('Utilities::getLabelitCell')
  #try:
  run2 = False
  run3 = False
  cell = False
  sym = False
  for line in open(os.path.join(self.labelit_dir,'bestfile.par'),'r').readlines():
    if line.startswith('CELL'):
      if len(line.split()) == 7:
        cell = line.split()[1:]
      else:
        run2 = True
    if line.startswith('SYMMETRY'):
      if len(line.split()) == 2:
        sym = line.split()[1]
      else:
        run3 = True
  #Sometimes bestfile.par is corrupt so I have backups to get cell and sym.
  if run2:
    for line in open('%s.mat'%os.path.join(self.labelit_dir,self.index_number),'r').readlines():
      if len(line.split()) == 6:
        cell = line.split()
  if run3:
    for line in open(os.path.join(self.labelit_dir, self.index_number),'r').readlines():
      if line.startswith('SYMMETRY'):
        sym = line.split()[1]
  if inp == 'all':
    return((cell,sym))
  elif inp == 'sym':
    return(sym)
  else:
    return(cell)
  """
  except:
    self.logger.exception('**Error in Utils.getLabelitCell**')
    return (None)
  """
def getLabelitStats(self,inp=False,simple=False):
  """
  Returns stats from Labelit for determining beam center. (Extra parsing from self.labelit_results)
  """
  if self.verbose:
    self.logger.debug('Utilities::getLabelitStats')
  output = {}
  #try:
  if inp:
    j1 = '[inp]'
  else:
    j1 = ''
  if simple:
    x = 1
  else:
    x = 2
  if type(eval('self.labelit_results%s'%j1).get("labelit_results")) == dict:
    for i in range(0,x):
      if i == 0:
        ind = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_face').index(':)')
        sg   = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_sg')[ind]
        sol  = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_solution')[ind]
      else:
        #P1 stats
        ind = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_solution').index('1')
        sol = '1'
      mos_rms = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_rms')[ind]
      mos_x = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_beam_x')[ind]
      mos_y = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_beam_y')[ind]
      ind1  = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_solution').index(sol)
      met  = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_metric')[ind1]
      rmsd = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_rmsd')[ind1]
      vol = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_volume')[ind1]
      if i == 0:
        output['best'] = {'SG':sg, 'mos_rms':mos_rms, 'mos_x':mos_x, 'mos_y':mos_y, 'metric':met, 'rmsd':rmsd, 'sol':sol}
      else:
        output['P1']   = {'mos_rms':mos_rms, 'mos_x':mos_x, 'mos_y':mos_y, 'rmsd':rmsd}
    if simple:
      return(sg,mos_rms,met,vol)
    else:
      eval('self.labelit_results%s'%j1).update({'labelit_stats': output})
  """
  except:
    self.logger.exception('**Error in Utils.getLabelitStats**')
  """
def getLabelitStatsNoMosflm(self,inp=False,simple=False):
  """
  Returns stats from Labelit for determining beam center. (Extra parsing from self.labelit_results)
  """
  if self.verbose:
    self.logger.debug('Utilities::getLabelitStatsNoMosflm')
  from labelit.steps import primaries
  output = {}
  try:
    if inp:
      j1 = '[inp]'
    else:
      j1 = ''
    if simple:
      x = 1
    else:
      x = 2
    l = [':)',':(','xx']
    if type(eval('self.labelit_results%s'%j1).get("labelit_results")) == dict:
      for i in range(0,x):
        if i == 0:
          for z in range(len(l)):
            try:
              ind = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_face').index(l[z])
              break
            except(ValueError):
              continue
          sg   = primaries[eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_system')[ind][1]]
          sol  = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_solution')[ind]
        else:
          #P1 stats
          ind = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_solution').index('1')
          sol = '1'
        #mos_rms = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_rms')[ind]
        #mos_x = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_beam_x')[ind]
        #mos_y = eval('self.labelit_results%s'%j1).get("labelit_results").get('mosflm_beam_y')[ind]
        ind1  = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_solution').index(sol)
        met  = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_metric')[ind1]
        rmsd = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_rmsd')[ind1]
        cell = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_cell')[ind1]
        vol = eval('self.labelit_results%s'%j1).get("labelit_results").get('labelit_volume')[ind1]
        if i == 0:
          #output['best'] = {'SG':sg, 'mos_rms':mos_rms, 'mos_x':mos_x, 'mos_y':mos_y, 'metric':met, 'rmsd':rmsd, 'sol':sol}
          output['best'] = {'SG':sg, 'metric':met, 'rmsd':rmsd, 'sol':sol, 'cell':cell}
        else:
          #output['P1']   = {'mos_rms':mos_rms, 'mos_x':mos_x, 'mos_y':mos_y, 'rmsd':rmsd}
          output['P1']   = {'rmsd':rmsd}
      if simple:
        return(sg,rmsd,met,vol)
      else:
        eval('self.labelit_results%s'%j1).update({'labelit_stats': output})
  except:
    self.logger.exception('**Error in Utils.getLabelitStatsNoMosflm**')

def getRes_OLD(self,inp=False):
  """
  Return resolution limit of dataset.
  """
  if self.verbose:
    self.logger.debug('Utilities::getRes')
  from iotbx import mtz
  try:
    if inp == False:
      inp = self.datafile
    if type(inp) == unicode:
      inp = convertUnicode(self,inp)
    data = mtz.object(inp)
    return(float(data.max_min_resolution()[-1]))
  except:
    self.logger.exception('**ERROR in Utils.getRes**')
    return (0.0)

def get_res(datafile):
    """Return resolution limit of dataset"""

    datafile = convert_unicode(datafile)
    data = iotbx_mtz.object(datafile)

    return float(data.max_min_resolution()[-1])

def get_detector(image, load=False):
    """
    Returns the best detector file for a given an image. If the detector is
    unknown to RAPD, a generic file will be suggested
    """
    from iotbx.detectors import ImageFactory

    # If this detector corresponds to a site

    # Try a generic detector

    # No idea
    return False

def get_site(image, load=False):
    """
    Figures out the correct site file by reading in an image.
    """
    from utils.modules import load_module
    from iotbx.detectors import ImageFactory

    d = {('MARCCD', 7) : ('sercat', 'SERCAT_BM'),
         ('MARCCD', 101) : ('sercat', 'SERCAT_ID'),
         #('Eiger-16M', 'Dectris Eiger 16M S/N E-32-0108') : ('necat', 'NECAT_E'),
         ('Eiger-16M', 'Dectris Eiger 16M S/N E-32-0108') : ('necat', 'NECAT_T'),
         }

    i = ImageFactory(image)
    if load:
        return (load_module(seek_module=d[(i.vendortype, i.parameters['DETECTOR_SN'])],
                            directories='sites'))
    else:
        return (d[(i.vendortype, i.parameters['DETECTOR_SN'])])


def getWavelength(self,inp=False):
  """
  Returns wavelength of dataset.
  """
  if self.verbose:
    self.logger.debug('Utilities::getWavelength')
  from iotbx import mtz

  wave = 0.979
  try:
    if inp == False:
      inp = self.datafile
    if type(inp) == unicode:
      inp = convertUnicode(self,inp)
    data = mtz.object(inp)
    for i in range(len(data.crystals())):
      if data.crystals()[i].project_name() == 'XDSproject':
        for x in range(len(data.crystals()[i].datasets())):
          wave = data.crystals()[i].datasets()[x].wavelength()
  except:
    self.logger.exception('**ERROR in Utils.getWavelength**')
  finally:
    return(wave)

def get_vendortype(inp):
  """
  Returns which detector vendortype the image is from by passing in the header.
  If it is not in the header, use ImageFactory to get it.
  """
  vendortype = inp.get('detector',False)
  #If not in header, use ImageFactory
  if vendortype == False:
    from iotbx.detectors import ImageFactory
    vendortype = ImageFactory(inp.get('fullname')).vendortype
  return (vendortype)

def load_cluster_adapter(self):
    """Load the appropriate cluster adapter.
       Need self.site set so it knows which cluster to import.
    """
    try:
        if self.site.CLUSTER_ADAPTER:
            return (load_module(self.site.CLUSTER_ADAPTER))
        else:
            return (False)
    except:
        # If self.site is not set.
        return (False)

def kill_children(pid, logger=False):
  """
  Kills the parent process, the children, and the children's children.
  """
  if logger:
    logger.debug('Utilities::killChildren')
  pids = []
  #try:
  output = subprocess.Popen('ps -F -A | grep %s'%pid,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  for line in output.stdout:
    if line.split()[1] == str(pid):
      pids.append(pid)
    if line.split()[2] == str(pid):
      pid1 = line.split()[:][1]
      pids.append(pid1)
      #Grab all the child processes as well.
      output2 = subprocess.Popen('ps -F -A | grep %s'%pid1,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
      for line in output2.stdout:
        if line.split()[2] == str(pid1):
          pids.append(line.split()[:][1])
  for p in pids:
    if logger:
        logger.debug('kill -9 %s'%p)
    os.system('kill -9 %s'%p)
  """
  except:
    if logger:
        logger.exception('**Could not kill the children?!?**')
  """
def kill_job(inp, logger=False):
  """
  Kills all the input jobs.
  """
  if logger:
    logger.debug('Utilities::killJobs')
  #try:
  output = subprocess.Popen('ps -F -A | grep %s'%inp,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  for line in output.stdout:
    kill = 'kill -9 %s'%line
    if logger:
        logger.debug(kill)
    os.system(kill)
  """
  except:
    if logger:
        logger.exception('**Could not kill the children?!?**')
  """
def makeHAfiles(self):
  """
  make the input HA files for phenix.autosol.
  """
  if self.verbose:
    self.logger.debug('Utilities::makeHAfiles')
  #try:
  counter = 0
  l = ['','_i']
  while counter <= 1:
    temp = []
    ha1 = []
    for line in open('junk%s.hat'%l[counter],'r').readlines():
      temp.append(line)
      if line.startswith('UNIT'):
        index1 = temp.index(line)
    for line in temp[index1:]:
      if len(line.split()) == 7:
        if line.split()[5].startswith('-') == False:
          ha1.append('%s %s %s'%(line.split()[2],line.split()[3],line.split()[4]))
    if counter == 0:
      self.ha_num1 = str(len(ha1))
    else:
      self.ha_num2 = str(len(ha1))
    new_ha = open('junk%s.ha'%l[counter],'w')
    for line in ha1:
      new_ha.write('%s\n'%line)
    new_ha.close()
    counter += 1
  """
  except:
    self.logger.exception('**ERROR in Utils.makeHAfiles**')
  """
def makeSeqFile(self):
  """
  Convert seq to file of generate poly-ala file. Required to fix bug in AutoSol.
  """
  if self.verbose:
    self.logger.debug('Utilities::makeSeqFile')
  #try:
  seq = self.preferences.get('request').get('sequence')
  f = open('seq.pir','w')
  if seq == '':
    print >>f, "> dummy sequence\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA*\n"
  else:
    print >>f, "> sequence\n%s*\n"%seq
  f.close()
  """
  except:
    self.logger.exception('**Error in Utils.makeSeqFile**')
  """
def mtz2sca(self,inp=False,output=False):
  """
  Convert mtz file to SCA for Shelx using mtz2sca. Scales correctly.
  """
  if self.verbose:
    self.logger.debug('Utilities::mtz2sca')
  #try:
  if inp:
    if len(inp) == 2:
      outfile = '%s.sca'%inp[0]
      command  = 'mtz2sca %s %s'%(inp[1],outfile)
      out = os.path.join(os.getcwd(),outfile)
    else:
      command = 'mtz2sca %s'%inp
      out = os.path.join(os.getcwd(),os.path.basename(inp.replace('.mtz','.sca')))
  else:
    command  = 'mtz2sca %s temp.sca'%self.datafile
    out = os.path.join(os.getcwd(),'temp.sca')
  if self.test == False:
    processLocal(command,self.logger)
  fixSCA(self,out)
  if output:
    output.put(out)
  else:
    self.datafile = out

  #except:
  #  self.logger.exception('**ERROR in Utils.mtz2sca2**')

def mtz2scaUM(self,inp,output=False):
  """
  Convert unmerged mtz file to unmerged SCA for Shelx.
  """
  if self.verbose:
    self.logger.debug('Utilities::mtz2scaUM')
  #try:
  if len(inp) == 2:
    name = inp[0]
    inp = inp[1]
  else:
    name = False
    inp = inp
  if os.path.basename(inp).startswith('smerge'):
    if name:
      file2 = '%s_unmerged.sca'%name
    else:
      file2 = os.path.basename(inp).replace('_sortedMergable.mtz','_unmerged.sca')
  else:
    file2 = os.path.basename(inp).replace('_mergable.mtz','_unmerged.sca')
  command  = 'aimless hklin %s scalepackunmerged %s hklout temp.mtz << eof > aimless.log\n'%(inp,file2)
  command += 'anomalous on\nscales constant\n'
  command += 'sdcorrection norefine full 1 0 0 partial 1 0 0\n'
  command += 'bins resolution 10\n'
  command += 'cycles 0\n'
  command += 'output scalepack unmerged\neof\n'
  if self.test == False:
    processLocal(command,self.logger)
    fixSCA(self,file2)
  if output:
    output.put(os.path.join(os.getcwd(),file2))
  else:
    self.datafile = os.path.join(os.getcwd(),file2)
  #except:
  #  self.logger.exception('**ERROR in Utils.mtz2scaUM**')

def phs2mtz(self,inp):
  """
  Convert Shelx phs to mtz.
  """
  if self.verbose:
    self.logger.debug('Utilities::phs2mtz')
  #try:
  command  = 'f2mtz hklin %s hklout %s<<eof\n'%(inp,inp.replace('.phs','.mtz'))
  command += 'CELL %s\n'%self.cell
  command += 'SYMM %s\n'%self.shelx_sg
  #Make labels the same as Resolve.
  command += 'LABOUT  H K L FP FOMM PHIM SIGFP\n'
  command += 'CTYPOUT H H H F W P Q\n'
  command += 'END\neof\n'
  if self.test == False:
    processLocal(command,self.logger)
  #except:
  #  self.logger.exception('**ERROR in Utils.phs2mtz**')

def pp(inp):
  """
  Print out the list of dict pretty.
  """
  import pprint
  junk = pprint.PrettyPrinter(indent=4)
  junk.pprint(inp)

def pp2(inp):
  """
  saves pretty version of list or dict.
  """
  inp1,f = inp
  f1 = open(f,'w')
  import pprint
  junk = pprint.PrettyPrinter(indent=4,stream=f1)
  #junk.pprint(inp1,stream=f1)
  junk.pprint(inp1)
  f1.close()

def processLocal(inp, logger=False, output=False):
    """
    Run job as subprocess on local machine.
    """

    # Logfile might be passed in
    if type(inp) == tuple:
        command, logfile = inp
    else:
        command = inp
        logfile = False

    # Run the process
    proc = subprocess.Popen(command,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    # Send back PID if have outlet
    if output:
        output.put(proc.pid)

    # Get the stdout and stderr from process
    stdout, stderr = proc.communicate()
    # print stdout
    # print stderr

    # Write out a log file, if name passed in
    if logfile:
        with open(logfile, "w") as out_file:
            out_file.write(stdout)
            out_file.write(stderr)

def rocksCommand(inp, logger=False):
  """
  Run Rocks command on all cluster nodes. Mainly used by rapd_agent_beamcenter.py to copy
  specific images to /dev/shm on each node for processing in RAM.
  """
  if logger:
    logger.debug('Utilities::rocksCommand')
  #try:
  command = '/opt/rocks/bin/rocks run host compute "%s"'%inp
  if logger:
    processLocal("ssh necat@gadolinium '%s'"%command,logger)
  else:
    processLocal("ssh necat@gadolinium '%s'"%command)
  #except:
  #    self.logger.exception('**ERROR in Utils.rocksCommand**')

def readHeader_TESTING(self,image):
  """
  Read image header as RAPD.
  """
  if self.verbose:
      self.logger.debug('MultiRuns::readHeader')

  tail = image[-3:]
  d = {}
  if tail== 'cbf':
    from rapd_pilatus import PilatusReadHeader
    from rapd_site import settings_C as C
    d['header'] = PilatusReadHeader(os.path.join(os.getcwd(),image),logger=self.logger)
    distance = float(d['header'].get('distance'))
    x_beam = C['beam_center_x_m6'] * distance**6 + \
             C['beam_center_x_m5'] * distance**5 + \
             C['beam_center_x_m4'] * distance**4 + \
             C['beam_center_x_m3'] * distance**3 + \
             C['beam_center_x_m2'] * distance**2 + \
             C['beam_center_x_m1'] * distance + C['beam_center_x_b']
             #header['vertical_offset']
    y_beam = C['beam_center_y_m6'] * distance**6 + \
             C['beam_center_y_m5'] * distance**5 + \
             C['beam_center_y_m4'] * distance**4 + \
             C['beam_center_y_m3'] * distance**3 + \
             C['beam_center_y_m2'] * distance**2 + \
             C['beam_center_y_m1'] * distance + C['beam_center_y_b']
    d['header'].update({'x_beam':x_beam})
    d['header'].update({'y_beam':y_beam})
  else:
    from rapd_adsc import AdscReadHeader
    d['header'] = AdscReadHeader(os.path.join(os.getcwd(),image),logger=self.logger)
  return(d)

def junk():
  return('got here')

def readMarHeader(inp):
  import re,struct
  print 'got here'
  format = '<'
  f = open(inp,'rb')
  parameters = {}
  offset = 1024
  #f.seek(offset+80)
  f.seek(2464)
  print f.read(512)

  f.seek(offset+640)
  rawdata = f.read(4)
  print struct.unpack(format+'i',rawdata)[0]/1000.

  f.seek(offset+696)
  rawdata = f.read(4)
  start_xtal_to_detector = struct.unpack(format+'i',rawdata)[0]/1000.
  print start_xtal_to_detector

  f.seek(1676)
  rawdata = f.read(8)
  integration, exposure = struct.unpack(format+'ii',rawdata)
  print integration* 0.001
  print exposure* 0.001




  """
  f.seek(offset+772)
  rawdata = f.read(8)
  pixelsize_x,pixelsize_y = struct.unpack(format+'ii',rawdata)
  parameters['PIXEL_SIZE'] = pixelsize_x*1.0e-6
  print parameters['PIXEL_SIZE']

  f.seek(offset+664)
  rawdata = f.read(8)
  beam_center_x,beam_center_y = struct.unpack(format+'ii',rawdata)
  parameters['BEAM_CENTER_X'] = beam_center_x/1000.*parameters['PIXEL_SIZE']
  parameters['BEAM_CENTER_Y'] = beam_center_y/1000.*parameters['PIXEL_SIZE']
  print parameters['BEAM_CENTER_X'], parameters['BEAM_CENTER_Y']

  f.seek(offset+908)
  rawdata = f.read(4)
  parameters['WAVELENGTH'] = struct.unpack(format+'i',rawdata)[0]*1.0e-5 # convert from femto to angstrom
  print parameters['WAVELENGTH']
  """




  f.close()


def runPhaserModule(self, inp=False):
  """
  Run separate module of Phaser to get results before running full job.
  Setup so that I can read the data in once and run multiple modules.
  """
  if self.verbose:
    self.logger.debug('Utilities::runPhaserModule')

  import phaser

  res = 0.0
  z = 0
  sc = 0.0

  try:
    def run_ellg():
      res0 = 0.0
      i0 = phaser.InputMR_ELLG()
      i0.setSPAC_HALL(r.getSpaceGroupHall())
      i0.setCELL6(r.getUnitCell())
      i0.setMUTE(True)
      i0.setREFL_DATA(r.getDATA())
      i0.addENSE_PDB_ID("junk",f,0.7)
      #i.addSEAR_ENSE_NUM("junk",5)
      r1 = phaser.runMR_ELLG(i0)
      #print r1.logfile()
      if r1.Success():
        res0 = r1.get_target_resolution('junk')
      del(r1)
      return(res0)

    def run_cca():
      z0 = 0
      sc0 = 0.0
      i0 = phaser.InputCCA()
      i0.setSPAC_HALL(r.getSpaceGroupHall())
      i0.setCELL6(r.getUnitCell())
      i0.setMUTE(True)
      #Have to set high res limit!!
      i0.setRESO_HIGH(res0)
      if np > 0:
        i0.addCOMP_PROT_NRES_NUM(np,1)
      if na > 0:
        i0.addCOMP_NUCL_NRES_NUM(na,1)
      r1 = phaser.runCCA(i0)
      #print r1.logfile()
      if r1.Success():
        z0 = r1.getBestZ()
        sc0 = 1-(1.23/r1.getBestVM())
      del(r1)
      return((z0,sc0))

    def run_ncs():
      i0 = phaser.InputNCS()
      i0.setSPAC_HALL(r.getSpaceGroupHall())
      i0.setCELL6(r.getUnitCell())
      i0.setREFL_DATA(r.getDATA())
      #i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
      #i0.setLABI_F_SIGF(f,sigf)
      i0.setMUTE(True)
      #i0.setVERB(True)
      r1 = phaser.runNCS(i0)
      print r1.logfile()
      print r1.loggraph().size()
      print r1.loggraph().__dict__.keys()
      #print r1.getCentricE4()
      if r1.Success():
        return(r1)

    def run_ano():
      #from cStringIO import StringIO
      i0 = phaser.InputANO()
      i0.setSPAC_HALL(r.getSpaceGroupHall())
      i0.setCELL6(r.getUnitCell())
      #i0.setREFL(p.getMiller(),p.getF(),p.getSIGF())
      #i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
      #i0.setREFL_F_SIGF(p.getMiller(),p.getIobs(),p.getSigIobs())
      i0.setREFL_DATA(r.getDATA())
      i0.setMUTE(True)
      r1 = phaser.runANO(i0)
      print r1.loggraph().__dict__.keys()
      print r1.loggraph().size()
      print r1.logfile()
      """
      o = phaser.Output()
      redirect_str = StringIO()
      o.setPackagePhenix(file_object=redirect_str)
      r1 = phaser.runANO(i0,o)
      """

      if r1.Success():
        print 'SUCCESS'
        return(r1)

    #Setup which modules are run
    matthews = False
    if inp:
      ellg = True
      ncs = False
      if type(inp) == str:
        f = inp
      else:
        np,na,res0,f = inp
        matthews = True
    else:
      ellg = False
      ncs = True

    #Read the dataset
    i = phaser.InputMR_DAT()
    i.setHKLI(self.datafile)
    #f = 'F'
    #sigf = 'SIGF'
    i.setLABI_F_SIGF('F','SIGF')
    i.setMUTE(True)
    r = phaser.runMR_DAT(i)
    if r.Success():
      if ellg:
        res = run_ellg()
      if matthews:
        z,sc = run_cca()
      if ncs:
        n = run_ncs()
    if matthews:
      #Assumes ellg is run as well.
      return((z,sc,res))
    elif ellg:
      #ellg run by itself
      return(res)
    else:
      #NCS
      return(n)

  except:
    self.logger.exception('**ERROR in Utils.runPhaserModule')
    if matthews:
      return((0,0.0,0.0))
    else:
      return(0.0)

def run_phaser_module(inp=False):
    """
    Run separate module of Phaser to get results before running full job.
    Setup so that I can read the data in once and run multiple modules.
    """

    # print "run_phaser_module"

    # import phaser
    #
    # res = 0.0
    # z = 0
    # sc = 0.0
    #
    # try:
    #   def run_ellg():
    #     res0 = 0.0
    #     i0 = phaser.InputMR_ELLG()
    #     i0.setSPAC_HALL(r.getSpaceGroupHall())
    #     i0.setCELL6(r.getUnitCell())
    #     i0.setMUTE(True)
    #     i0.setREFL_DATA(r.getDATA())
    #     i0.addENSE_PDB_ID("junk",f,0.7)
    #     #i.addSEAR_ENSE_NUM("junk",5)
    #     r1 = phaser.runMR_ELLG(i0)
    #     #print r1.logfile()
    #     if r1.Success():
    #       res0 = r1.get_target_resolution('junk')
    #     del(r1)
    #     return(res0)
    #
    #   def run_cca():
    #     z0 = 0
    #     sc0 = 0.0
    #     i0 = phaser.InputCCA()
    #     i0.setSPAC_HALL(r.getSpaceGroupHall())
    #     i0.setCELL6(r.getUnitCell())
    #     i0.setMUTE(True)
    #     #Have to set high res limit!!
    #     i0.setRESO_HIGH(res0)
    #     if np > 0:
    #       i0.addCOMP_PROT_NRES_NUM(np,1)
    #     if na > 0:
    #       i0.addCOMP_NUCL_NRES_NUM(na,1)
    #     r1 = phaser.runCCA(i0)
    #     #print r1.logfile()
    #     if r1.Success():
    #       z0 = r1.getBestZ()
    #       sc0 = 1-(1.23/r1.getBestVM())
    #     del(r1)
    #     return((z0,sc0))
    #
    #   def run_ncs():
    #     i0 = phaser.InputNCS()
    #     i0.setSPAC_HALL(r.getSpaceGroupHall())
    #     i0.setCELL6(r.getUnitCell())
    #     i0.setREFL_DATA(r.getDATA())
    #     #i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
    #     #i0.setLABI_F_SIGF(f,sigf)
    #     i0.setMUTE(True)
    #     #i0.setVERB(True)
    #     r1 = phaser.runNCS(i0)
    #     print r1.logfile()
    #     print r1.loggraph().size()
    #     print r1.loggraph().__dict__.keys()
    #     #print r1.getCentricE4()
    #     if r1.Success():
    #       return(r1)
    #
    #   def run_ano():
    #     #from cStringIO import StringIO
    #     i0 = phaser.InputANO()
    #     i0.setSPAC_HALL(r.getSpaceGroupHall())
    #     i0.setCELL6(r.getUnitCell())
    #     #i0.setREFL(p.getMiller(),p.getF(),p.getSIGF())
    #     #i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
    #     #i0.setREFL_F_SIGF(p.getMiller(),p.getIobs(),p.getSigIobs())
    #     i0.setREFL_DATA(r.getDATA())
    #     i0.setMUTE(True)
    #     r1 = phaser.runANO(i0)
    #     print r1.loggraph().__dict__.keys()
    #     print r1.loggraph().size()
    #     print r1.logfile()
    #     """
    #     o = phaser.Output()
    #     redirect_str = StringIO()
    #     o.setPackagePhenix(file_object=redirect_str)
    #     r1 = phaser.runANO(i0,o)
    #     """
    #
    #     if r1.Success():
    #       print 'SUCCESS'
    #       return(r1)
    #
    # Setup which modules are run
    matthews = False
    if inp:
        ellg = True
        ncs = False
        if type(inp) == str:
            f = inp
        else:
            np, na, res0, pdb_file , data_file = inp
            matthews = True
            # print np, na, res0, pdb_file, data_file, matthews
            command = ["phenix.python",
                       "/Users/fmurphy/workspace/rapd_github/src/plugins/analysis/subcontractors/phaser_preflight.py",
                       "--json",
                       "--np",
                       str(np),
                       "--na",
                       str(na),
                       "--resolution",
                       str(res0),
                       "--pdb_file",
                       pdb_file,
                       "--data_file",
                       data_file
                      ]
            if matthews:
                command.append("--matthews")
            phaser_preflight = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            phaser_preflight.wait()
            stdout, _ = phaser_preflight.communicate()
            preflight_return = json.loads(stdout.rstrip())

            return preflight_return

    else:
        ellg = False
        ncs = True
    #
    #   #Read the dataset
    #   i = phaser.InputMR_DAT()
    #   i.setHKLI(self.datafile)
    #   #f = 'F'
    #   #sigf = 'SIGF'
    #   i.setLABI_F_SIGF('F','SIGF')
    #   i.setMUTE(True)
    #   r = phaser.runMR_DAT(i)
    #   if r.Success():
    #     if ellg:
    #       res = run_ellg()
    #     if matthews:
    #       z,sc = run_cca()
    #     if ncs:
    #       n = run_ncs()
    #   if matthews:
    #     #Assumes ellg is run as well.
    #     return((z,sc,res))
    #   elif ellg:
    #     #ellg run by itself
    #     return(res)
    #   else:
    #     #NCS
    #     return(n)
    #
    # except:
    #   self.logger.exception('**ERROR in Utils.runPhaserModule')
    #   if matthews:
    #     return((0,0.0,0.0))
    #   else:
    #     return(0.0)

def sca2mtz(self,res=False,run_before=False):
  """
  Convert sca file to mtz for Phaser.
  """
  if self.verbose:
    self.logger.debug('Utilities::sca2mtz')
  #try:
  failed = False
  os.chdir(self.working_dir)
  path = os.path.join(self.working_dir,'temp.mtz')
  command  = 'scalepack2mtz hklin %s hklout junk.mtz<<eof1\n'%self.datafile
  if res:
    command += 'resolution 50 %s\n'%res
  command += 'end\neof1\n'
  command += 'truncate hklin junk.mtz hklout temp.mtz<<eof2\n'
  command += 'truncate yes\nend\neof2\n'
  temp = []
  if self.test == False:
    myoutput = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in myoutput.stdout:
      temp.append(line)
      if line.startswith(' TRUNCATE:  LSQ: sigma is zero'):
        failed = True
        for line in temp:
          if line.startswith(' finishing resolution'):
            hi_res = line.split()[3]
  if failed:
    if run_before:
      return(None)
    else:
      run_before = True
      sca2mtz(self,hi_res,run_before)
  else:
    if self.test == False:
      os.system('rm -f junk.mtz')
    #self.datafile = path
    return(path)
  """
  except:
    self.logger.exception('**ERROR in Utils.sca2mtz**')
    return(None)
  """
def setPhaserRes(self,res):
  """
  Determine the best resolution to run Phaser at.
  """
  if self.verbose:
    self.logger.debug('Utilities::setPhaserRes')
  try:
    #If recommended res is greater than 6 use it, or limit to 6 if less than.
    if self.large_cell:
      if res < 6.0:
        res = 6.0
    else:
      #If recommended res is higher than dataset res.
      #Use recommend res if lower than 4.5.
      if res > self.dres:
        #If easy solution
        if res > 6.0:
          res = 6.0
        #If recommended res is 6 to 4.5, use 4.5.
        elif 4.5 < res < 6.0:
          res = 4.5
    return(res)
  except:
    self.logger.exception('**ERROR in Utils.setPhaserRes**')
    return(res)

def set_phaser_res(res, large_cell, dres):
    """Determine the best resolution to run Phaser at"""

    # If recommended res is greater than 6 use it, or limit to 6 if less than.
    if large_cell:
        if res < 6.0:
            res = 6.0
    else:
        # If recommended res is higher than dataset res.
        # Use recommend res if lower than 4.5.
        if res > dres:
            # If easy solution
            if res > 6.0:
              res = 6.0
            # If recommended res is 6 to 4.5, use 4.5.
            elif 4.5 < res < 6.0:
              res = 4.5
    return res
"""
def setCellSymXDS(self):

  #Set the cell and sym from the GXPARM file to the XDS.INP.

  if self.verbose:
    self.logger.debug('Utilities::setCellSymXDS')
  try:
    run = True
    #Check if GXPARM and XPARM have same SG. If not copy GXPARM over.
    gxparm = Parse.ParseOutputGxparm(self,open(self.gxparm,'r').readlines(),True)
    #if os.path.exists('XPARM.XDS'):
    #  #local_gxparm = Parse.ParseOutputGxparm(self,open('GXPARM.XDS','r').readlines(),True)
    #  xparm = Parse.ParseOutputGxparm(self,open('XPARM.XDS','r').readlines(),True)
    #  #if int(gxparm[0]) != int(xparm[0]):

    #  #Should not happen since cell and SG are input as below.
    #  if int(gxparm[0]) != int(local_gxparm[0]):
    #    print os.getcwd()
    #    if os.path.exists('GXPARM.XDS'):
    #      os.rename('GXPARM.XDS','GXPARM1.XDS')
    #    os.rename('XPARM.XDS','XPARM_orig.XDS')
    #    shutil.copy(self.gxparm,os.path.join(os.getcwd(),'XPARM.XDS'))
    inp = open('XDS.INP','r').readlines()
    for line in inp:
      if line.count('UNIT_CELL_CONSTANTS='):
        run = False
    if run:
      #cell = Parse.ParseOutputGxparm(self,open(self.gxparm,'r').readlines(),True)
      inp.append('     SPACE_GROUP_NUMBER=%s\n'%gxparm[0])
      inp.append('     UNIT_CELL_CONSTANTS=%s %s %s %s %s %s\n'%(gxparm[1],gxparm[2],gxparm[3],gxparm[4],gxparm[5],gxparm[6]))
      f = open('XDS.INP','w')
      f.writelines(inp)
      f.close()

  except:
    self.logger.exception('**ERROR in Utils.setCellSymXDS**')
"""
def setRes(self,input,res):
  """
  Set the high res limit of mtz file to new limit.
  """
  if self.verbose:
    self.logger.debug('Utilities::setRes')
  #try:
  inp  = 'pointless -copy hklin %s hklout newres_mergable.mtz <<eof\n'%input
  #inp += 'SETTING C2\nResolution 50 %s\neof\n'%res
  #Keep low res data
  inp += 'SETTING C2\nResolution high %s\neof\n'%res
  processLocal(inp,self.logger)
  return(os.path.join(os.getcwd(),'newres_mergable.mtz'))

  #except:
  #  self.logger.exception('**ERROR in Utils.setRes**')

def setScalingXDS_OLD(self):
  """
  Turn off the scaling in XDS.
  """
  if self.verbose:
    self.logger.debug('Utilities::setScalingXDS')
  #try:
  run = True
  inp = open('XDS.INP','r').readlines()
  for line in inp:
    if line.count('MINIMUM_I/SIGMA='):
      run = False
  if run:
    #inp.append('     MINIMUM_I/SIGMA=50\n     CORRECTIONS=\n     NBATCH=1\nJOB=CORRECT\n')
    inp.append('     MINIMUM_I/SIGMA=50\n     CORRECTIONS=MODULATION\n     NBATCH=1\nJOB=CORRECT\n')
    f = open('XDS.INP','w')
    f.writelines(inp)
    f.close()
  """
  except:
    self.logger.exception('**ERROR in Utils.setScalingXDS**')
  """
def stillRunning(pid):
  """
  Check to see if process and/or its children and/or children's children are still running.
  """
  #try:
  running = False
  output = subprocess.Popen('ps -F -A | grep %s'%pid,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  for line in output.stdout:
    if line.split()[1] == str(pid):
      running = True
    """
    if line.split()[2] == str(pid):
      running = True
      pid1 = line.split()[:][1]
      output2 = subprocess.Popen('ps -F -A | grep %s'%pid1,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
      for line in output2.stdout:
  	if line.split()[2] == str(pid1):
  	  running = True
  """
  return(running)
  """
  except:
    self.logger.exception('**Error in Utils.stillRunning**')
  """

def subGroups(self,inp1,inp2='shelx'):
  """
  Determine which SG's to run.
  """
  if self.verbose:
    self.logger.debug('Utilities::subGroups')
  try:
    subgroups = {  '1'  : [None],
                   '5'  : [None],
                   '5.1': [None],
                   '5.2': [None],
                   '5.3': [None],
                   '5.4': [None],
                   '5.5': [None],
                   #'5'  : ['5.1','5.2','5.3','5.4','5.5'],
                   '3'  : ['4'],
                   '16' : ['17','17.1','17.2','18','18.1','18.2','19'],
                   '20' : ['21'],
                   '22' : [None],
                   '23' : ['24'],
                   '75' : ['76','77','78'],
                   '79' : ['80'],
                   '89' : ['90','91','95','94','93','92','96'],
                   '97' : ['98'],
                   '143': ['144','145'],
                   '149': ['151','153'],
                   '150': ['152','154'],
                   '146.1': [None],
                   '146.2': [None],
                   '155.1': [None],
                   '155.2': [None],
                   '168': ['169','170','171','172','173'],
                   '177': ['178','179','180','181','182'],
                   '196': [None],
                   '195': ['198'],
                   '197': ['199'],
                   '207': ['208','212','213'],
                   '209': ['210'],
                   '211': ['214']  }

    subgroups2 = { '3'  : ['3','4'],
                   '16' : ['16','17','17.1','17.2','18','18.1','18.2','19'],
                   '20' : ['20','21'],
                   '23' : ['23','24'],
                   '75' : ['75','76','77'],
                   '79' : ['79','80'],
                   '89' : ['89','90','91','94','93','92'],
                   '97' : ['97','98'],
                   '143': ['143','144'],
                   '149': ['149','151'],
                   '150': ['150','152'],
                   '168': ['168','169','171','173'],
                   '177': ['177','178','180','182'],
                   '195': ['195','198'],
                   '197': ['197','199'],
                   '207': ['207','208','212'],
                   '209': ['209','210'],
                   '211': ['211','214'] }

    subgroups3 = { '3'  : ['3','4'],
                   '16' : ['16','17','17.1','17.2','18','18.1','18.2','19'],
                   '20' : ['20','21'],
                   '23' : ['23','24'],
                   '75' : ['75','76','77','78'],#
                   '79' : ['79','80'],
                   '89' : ['89','90','91','94','93','92','95','96'],#
                   '97' : ['97','98'],
                   '143': ['143','144','145'],#
                   '149': ['149','151','153'],#
                   '150': ['150','152','154'],#
                   '168': ['168','169','171','173','170','172'],#
                   '177': ['177','178','180','182','179','181'],#
                   '195': ['195','198'],
                   '197': ['197','199'],
                   '207': ['207','208','212','213'],#
                   '209': ['209','210'],
                   '211': ['211','214'] }
    sg2 = False
    if subgroups.has_key(inp1):
      sg = inp1
    else:
      for line in subgroups.items():
        if line[1].count(inp1):
          sg = line[0]
    #Returns Laue group number
    if inp2 == 'simple':
      return(sg)
    else:
      if inp2 == 'shelx':
        if subgroups2.has_key(sg):
          sg2 = subgroups2[sg]
      else:
        if subgroups3.has_key(sg):
          sg2 = subgroups3[sg]
      if sg2:
        return(sg2)
      else:
        return([sg])
  except:
    self.logger.exception('**ERROR in Utils.subGroups**')

def get_sub_groups(input_sg, mode="simple"):
    """Return sub subgroups releated to input spacegroup"""

    subgroups1 = {"1": [None],
                  "5": [None],
                  "5.1": [None],
                  "5.2": [None],
                  "5.3": [None],
                  "5.4": [None],
                  "5.5": [None],
                  "3": ["4"],
                  "16": ["17", "17.1", "17.2", "18", "18.1", "18.2", "19"],
                  "20": ["21"],
                  "22": [None],
                  "23": ["24"],
                  "75": ["76", "77", "78"],
                  "79": ["80"],
                  "89": ["90", "91", "95", "94", "93", "92", "96"],
                  "97": ["98"],
                  "143": ["144", "145"],
                  "149": ["151", "153"],
                  "150": ["152", "154"],
                  "146.1": [None],
                  "146.2": [None],
                  "155.1": [None],
                  "155.2": [None],
                  "168": ["169", "170", "171", "172", "173"],
                  "177": ["178", "179", "180", "181", "182"],
                  "196": [None],
                  "195": ["198"],
                  "197": ["199"],
                  "207": ["208", "212", "213"],
                  "209": ["210"],
                  "211": ["214"]}

    subgroups2 = {"3": ["3", "4"],
                  "16": ["16", "17", "17.1", "17.2", "18", "18.1", "18.2", "19"],
                  "20": ["20", "21"],
                  "23": ["23", "24"],
                  "75": ["75", "76", "77"],
                  "79": ["79", "80"],
                  "89": ["89", "90", "91", "94", "93", "92"],
                  "97": ["97", "98"],
                  "143": ["143", "144"],
                  "149": ["149", "151"],
                  "150": ["150", "152"],
                  "168": ["168", "169", "171", "173"],
                  "177": ["177", "178", "180", "182"],
                  "195": ["195", "198"],
                  "197": ["197", "199"],
                  "207": ["207", "208", "212"],
                  "209": ["209", "210"],
                  "211": ["211", "214"]}

    subgroups3 = {"3": ["3", "4"],
                  "16": ["16", "17", "17.1", "17.2", "18", "18.1", "18.2", "19"],
                  "20": ["20", "21"],
                  "23": ["23", "24"],
                  "75": ["75", "76", "77", "78"],
                  "79": ["79", "80"],
                  "89": ["89", "90", "91", "94", "93", "92", "95", "96"],
                  "97": ["97", "98"],
                  "143": ["143", "144", "145"],
                  "149": ["149", "151", "153"],
                  "150": ["150", "152", "154"],
                  "168": ["168", "169", "171", "173", "170", "172"],
                  "177": ["177", "178", "180", "182", "179", "181"],
                  "195": ["195", "198"],
                  "197": ["197", "199"],
                  "207": ["207", "208", "212", "213"],
                  "209": ["209", "210"],
                  "211": ["211", "214"]}

    shelx_sg = False

    if isinstance(input_sg, int):
        input_sg = str(input_sg)

    # Look for subgroups
    if subgroups1.has_key(input_sg):
        simple_sg = input_sg
    else:
        for line in subgroups1.items():
            if line[1].count(input_sg):
                simple_sg = line[0]

    # Returns Laue group number
    if mode == "simple":
        return simple_sg
    else:
        if mode == "shelx":
            if subgroups2.has_key(simple_sg):
                shelx_sg = subgroups2[simple_sg]
        else:
            if subgroups3.has_key(simple_sg):
                shelx_sg = subgroups3[simple_sg]
        if shelx_sg:
            return shelx_sg
        else:
            return [simple_sg]

def symopsSG(self, inp):
  """
  Convert SG to SG#.
  """
  if self.verbose:
    self.logger.debug('Utilities::symopsSG')
  try:
    symops =     {'P1'       : '1'  ,
                  'C2'       : '4'  ,
                  'C121'     : '4'  ,
                  'I121'     : '4'  ,
                  'A121'     : '4'  ,
                  'A112'     : '4'  ,
                  'B112'     : '4'  ,
                  'I112'     : '4'  ,
                  'P2'       : '2'  ,
                  'P121'     : '2'  ,
                  'P21'      : '2'  ,
                  'P1211'    : '2'  ,
                  'F222'     : '16' ,
                  'I222'     : '8' ,
                  'I212121'  : '8' ,
                  'C222'     : '8' ,
                  'C2221'    : '8' ,
                  'P222'     : '4' ,
                  'P2221'    : '4' ,
                  'P2212'    : '4' ,
                  'P2122'    : '4' ,
                  'P21212'   : '4' ,
                  'P21221'   : '4' ,
                  'P22121'   : '4' ,
                  'P212121'  : '4' ,
                  'I4'       : '8' ,
                  'I41'      : '8' ,
                  'I422'     : '16' ,
                  'I4122'    : '16' ,
                  'P4'       : '4' ,
                  'P41'      : '4' ,
                  'P42'      : '4' ,
                  'P43'      : '4' ,
                  'P422'     : '8' ,
                  'P4212'    : '8' ,
                  'P4122'    : '8' ,
                  'P4322'    : '8' ,
                  'P4222'    : '8' ,
                  'P42212'   : '8' ,
                  'P41212'   : '8' ,
                  'P43212'   : '8' ,
                  'P3'       : '3',
                  'P31'      : '3',
                  'P32'      : '3',
                  'P312'     : '6',
                  'P3112'    : '6',
                  'P3212'    : '6',
                  'P321'     : '6',
                  'P3121'    : '6',
                  'P3221'    : '6',
                  'P6'       : '6',
                  'P61'      : '6',
                  'P65'      : '6',
                  'P62'      : '6',
                  'P64'      : '6',
                  'P63'      : '6',
                  'P622'     : '12',
                  'P6122'    : '12',
                  'P6522'    : '12',
                  'P6222'    : '12',
                  'P6422'    : '12',
                  'P6322'    : '12',
                  'R3'       : '3',
                  'H3'       : '9',
                  'R32'      : '6',
                  'H32'      : '18',
                  'F23'      : '48',
                  'F432'     : '96',
                  'F4132'    : '96',
                  'I23'      : '24',
                  'I213'     : '24',
                  'I432'     : '48',
                  'I4132'    : '48',
                  'P23'      : '12',
                  'P213'     : '12',
                  'P432'     : '24',
                  'P4232'    : '24',
                  'P4332'    : '24',
                  'P4132'    : '24'    }

    sg = symops[inp]
    return(sg)
  except:
    self.logger.exception('**ERROR in Utils.symopsSG**')

def sg_to_nsymops(inp):
    """
    return number of symmetry operations for given space group.
    """
    symops = {'P1': 1,
              'C2': 4,
              'C121': 4,
              'I121': 4,
              'A121': 4,
              'A112': 4,
              'B112': 4,
              'I112': 4,
              'P2': 2,
              'P121': 2,
              'P21': 2,
              'P1211': 2,
              'F222': 16,
              'I222': 8,
              'I212121': 8,
              'C222': 8,
              'C2221': 8,
              'P222': 4,
              'P2221': 4,
              'P2212': 4,
              'P2122': 4,
              'P21212': 4,
              'P21221': 4,
              'P22121': 4,
              'P212121': 4,
              'I4': 8,
              'I41': 8,
              'I422': 16,
              'I4122': 16,
              'P4': 4,
              'P41': 4,
              'P42': 4,
              'P43': 4,
              'P422': 8,
              'P4212': 8,
              'P4122': 8,
              'P4322': 8,
              'P4222': 8,
              'P42212': 8,
              'P41212': 8,
              'P43212': 8,
              'P3': 3,
              'P31': 3,
              'P32': 3,
              'P312': 6,
              'P3112': 6,
              'P3212': 6,
              'P321': 6,
              'P3121': 6,
              'P3221': 6,
              'P6': 6,
              'P61': 6,
              'P65': 6,
              'P62': 6,
              'P64': 6,
              'P63': 6,
              'P622': 12,
              'P6122': 12,
              'P6522': 12,
              'P6222': 12,
              'P6422': 12,
              'P6322': 12,
              'R3': 3,
              'H3': 9,
              'R32': 6,
              'H32': 18,
              'F23': 48,
              'F432': 96,
              'F4132': 96,
              'I23': 24,
              'I213': 24,
              'I432': 48,
              'I4132': 48,
              'P23': 12,
              'P213': 12,
              'P432': 24,
              'P4232': 24,
              'P4332': 24,
              'P4132': 24}

    return symops[inp]

def XDS2Shelx(self,inp,output=False):
  """
  Run xdsconv to create SHELX input file. SHELXD complains about not having any reflexions about threshold?
  REASON: File is not an SCA file...
  """
  if self.verbose:
    self.logger.debug('Utilities::XDS2Shelx')
  #try:
  if len(inp) == 2:
    #name = inp[0]
    inp = inp[1]
  else:
    #name = False
    inp = inp
  if os.path.exists(os.path.basename(inp)) == False:
    os.symlink(inp,os.path.basename(inp))
  #print os.path.basename(inp).replace('.HKL','.sca')
  inp1 = "INPUT_FILE=%s\nOUTPUT_FILE=%s SHELX\nFRIEDEL'S_LAW=FALSE\n"%(os.path.basename(inp),os.path.basename(inp).replace('.HKL','.sca'))
  f = open('XDSCONV.INP','w')
  #print >>f,inp
  f.writelines(inp1)
  f.close()
  #if self.test == False:
  subprocess.Popen('xdsconv',shell=True).wait()
  fixSCA(self,os.path.basename(inp).replace('.HKL','.sca'))
  if output:
    output.put(os.path.join(os.getcwd(),os.path.basename(inp).replace('.HKL','.sca')))
  else:
    self.datafile = os.path.join(os.getcwd(),os.path.basename(inp).replace('.HKL','.sca'))

  #except:
  #  self.logger.exception('**ERROR in Utils.XDS2Shelx**')

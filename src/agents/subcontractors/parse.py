"""
Parsing methods for multiple core functions
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2011, Cornell University
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
__created__ = "2011-02-02"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

# Standard imports
import os

def setShelxResults(self, inp=False):
  """
  Output dict for SHelx results.
  """
  if self.verbose:
    self.logger.debug('Parse::setShelxResults')
  if inp:
    tag = inp
  else:
    tag = 'no anom signal'

  data  = { 'shelxc_res'      : tag,
            'shelxc_data'     : tag,
            'shelxc_isig'     : tag,
            'shelxc_comp'     : tag,
            'shelxc_dsig'     : tag,
            'shelxc_chi-sq'   : tag,
            'shelxc_cchalf'   : tag,
            'shelxd_try'      : tag,
            'shelxd_cca'      : tag,
            'shelxd_ccw'      : tag,
            'shelxd_fom'      : tag,
            'shelxd_cfom'     : tag,
            'shelxd_best_occ' : tag,
            'shelxd_best_try' : tag,
            'shelxd_best_cc'  : tag,
            'shelxd_best_ccw' : tag,
            'shelxd_best_cfom': tag,
            'shelxe_cc'       : tag,
            'shelxe_mapcc'    : tag,
            'shelxe_res'      : tag,
            'shelxe_contrast' : tag,
            'shelxe_con'      : tag,
            'shelxe_sites'    : tag,
            'shelxe_inv_sites': tag,
            'shelxe_nosol'    : tag,
            'shelx_data'      : tag,
            'MAD_CC'          : tag,
            'shelx_ha'        : 'None',
            'shelx_phs'       : 'None',
            'shelx_tar'       : 'None'}
  #self.shelx_results = {'Shelx results' : data}
  return(data)

def setXtriageFailed(self):
  """
  Set output dict if Xtraige fails.
  """
  if self.verbose:
    self.logger.debug('Parse::setXtriageFailed')
  xtriage = {'Xtriage anom'         : 'None',
             'Xtriage anom plot'    : 'None',
             'Xtriage int plot'     : 'None',
             'Xtriage i plot'       : 'None',
             'Xtriage z plot'       : 'None',
             'Xtriage nz plot'      : 'None',
             'Xtriage l-test plot'  : 'None',
             'Xtriage z-score'      : 'None',
             'Xtriage pat'          : 'None',
             #'Xtriage pat coor'     : 'None',
             #'Xtriage pat dist'     : 'None',
             #'Xtriage pat height'   : 'None',
             'Xtriage pat p-value'  : 'None',
             'Xtriage summary'      : 'None',
             'Xtriage log'          : 'None',
             'Xtriage PTS'          : 'None',
             'Xtriage PTS info'     : 'None',
             'Xtriage twin'         : 'None',
             'Xtriage twin info'    : 'None'}
  return(xtriage)

def setMolrepFailed(self):
  """
  Set output dict if Molrep fails.
  """
  if self.verbose:
    self.logger.debug('Parse::setMolrepFailed')
  molrep  =  {#'Molrep log'    : 'None',
              #'Molrep jpg'    : 'None',
              'Molrep PTS'    : False,
              'Molrep PTS_pk' : False}
  return(molrep)
  #self.molrep_results = {'Molrep results': molrep}

def setAutoSolFalse(inp=False):
  """
  set output dict for Autosol when it is disabled.
  """
  if inp:
    tag = inp
  else:
    tag = 'NA'
  phenix = { 'directory'       : tag,
             'sg'              : tag,
             'wavelength'      : tag,
             'ha_type'         : tag,
             "f'"              : tag,
             'f"'              : tag,
             'bayes-cc'        : tag,
             'fom'             : tag,
             'sites_start'     : tag,
             'sites_refined'   : tag,
             'res_built'       : tag,
             'side_built'      : tag,
             'num_chains'      : tag,
             'model-map_cc'    : tag,
             'r/rfree'         : tag,
             #'den_mod_r'       : tag
                                      }
  return(phenix)

def setPhaserFailed(inp=False):
  """
  Return dict with all the params set to NA.
  """
  if inp:
    tag = inp
  else:
    tag = 'Timed out'
  phaser = {      'AutoMR nosol': 'True',
                  'AutoMR tar'  : 'None',
                  'AutoMR pdb'  : tag,
                  'AutoMR mtz'  : tag,
                  'AutoMR gain' : tag,
                  'AutoMR rfz'  : tag,
                  'AutoMR tfz'  : tag,
                  'AutoMR clash': tag,
                  'AutoMR dir'  : tag,
                  'AutoMR sg'   : tag,
                  'AutoMR nmol' : 0,
                  'AutoMR adf'  : 'None',
                  'AutoMR peak' : 'None'}
  return(phaser)

def setRaddoseFailed(inp=False):
  if inp:
    tag = inp
  else:
    tag = 'Timed out'
  raddose = { 'dose per image'       : tag,
              'exp dose limit'       : tag,
              'henderson limit'      : tag }
  return(raddose)

def setBestFailed(inp=False):
  data = {         'strategy'+inp+'run number'                       : 'skip',
                   'strategy'+inp+'phi start'                        : 'skip',
                   'strategy'+inp+'num of images'                    : 'skip',
                   'strategy'+inp+'delta phi'                        : 'skip',
                   'strategy'+inp+'image exp time'                   : 'skip',
                   'strategy'+inp+'distance'                         : 'skip',
                   'strategy'+inp+'overlap'                          : 'skip',
                   'strategy'+inp+'res limit'                        : 'skip',
                   'strategy'+inp+'anom flag'                        : 'skip',
                   'strategy'+inp+'phi end'                          : 'skip',
                   'strategy'+inp+'rot range'                        : 'skip',
                   'strategy'+inp+'completeness'                     : 'skip',
                   'strategy'+inp+'redundancy'                       : 'skip',
                   'strategy'+inp+'R-factor'                         : 'skip',
                   'strategy'+inp+'I/sig'                            : 'skip',
                   'strategy'+inp+'total exposure time'              : 'skip',
                   'strategy'+inp+'data collection time'             : 'skip',
                   'strategy'+inp+'frac of unique in blind region'   : 'skip',
                   'strategy'+inp+'attenuation'                      : 'skip',
                   'strategy'+inp+'new transmission'                 : 'skip'    }
  return(data)

def setMosflmFailed(inp):
  data = {    'strategy'+inp+'run number'            : 'skip',
              'strategy'+inp+'phi start'             : 'skip',
              'strategy'+inp+'phi end'               : 'skip',
              'strategy'+inp+'num of images'         : 'skip',
              'strategy'+inp+'resolution'            : 'skip',
              'strategy'+inp+'completeness'          : 'skip',
              'strategy'+inp+'redundancy'            : 'skip',
              'strategy'+inp+'distance'              : 'skip',
              'strategy'+inp+'image exp time'        : 'skip',
              'strategy'+inp+'delta phi'             : 'skip'}
  return(data)

def ParseOutputLabelit(self,inp,iteration=0):
  """
  Parses Labelit results and filters for specific errors. Cleans up the output AND looks for best solution
  then passes info back to caller.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputLabelit')
  tmp                = []
  junk               = []
  labelit_sol        = []
  pseudotrans        = False
  multi_sg           = False
  few_spots          = False
  min_spots          = False
  spot_problem       = False
  labelit_face       = []
  labelit_solution   = []
  labelit_metric     = []
  labelit_fit        = []
  labelit_rmsd       = []
  labelit_spots_fit  = []
  labelit_system     = []
  labelit_cell       = []
  labelit_volume     = []
  labelit_bc         = {}
  #mosflm_sol         = []
  mosflm_face        = []
  mosflm_solution    = []
  mosflm_sg          = []
  mosflm_beam_x      = []
  mosflm_beam_y      = []
  mosflm_distance    = []
  mosflm_res         = []
  mosflm_mos         = []
  mosflm_rms         = []

  try:
    #If results empty, then fail
    if len(inp) == 0:
      return ('failed')
    #Check for errors
    for x,line in enumerate(inp):
      tmp.append(line)
      if len(line) > 1:
        if line.startswith('distl_minimum_number_spots'):
          min_spots = line
          #return (('min spots', line))
        if line.startswith('RuntimeError:'):
          return ('failed')
        if line.startswith('ValueError:'):
          return ('failed')
        if line.startswith('Labelit finds no reasonable solution'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('No_Indexing_Solution: Unreliable model'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith("No_Indexing_Solution: (couldn't find 3 good basis vectors)"):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('MOSFLM_Warning: MOSFLM logfile declares FATAL ERROR'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('ValueError: min()'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('Spotfinder Problem:'):
          spot_problem = True
        if line.startswith('InputFileError: Input error: File header must contain the sample-to-detector distance in mm; value is 0.'):
          return ('fix labelit')
        if line.startswith('InputFileError: Input error:'):
          return ('no pair')
        if line.startswith('Have '):
          self.min_good_spots = line.split()[1].rstrip(';')
          few_spots = True
        if line.startswith('UnboundLocalError'):
          return ('bad input')
        if line.startswith('divide by zero'):
          return ('bumpiness')
        #Could give error is too many choices with close cell dimensions, but...
        if line.startswith('No_Lattice_Selection: In this case'):
          multi_sg = True
          error_lg = line.split()[11]
        if line.startswith('No_Lattice_Selection: The known_symmetry'):
          return ('bad input')
        if line.startswith('MOSFLM_Warning: MOSFLM does not give expected results on r_'):
          return ('mosflm error')
        #Save the beam center
        if line.startswith('Beam center'):
          labelit_bc['labelit_x_beam'] = line.split()[3][:-3]
          labelit_bc['labelit_y_beam'] = line.split()[5][:-3]
        #Now save line numbers for parsing Labelit and Mosflm results
        if line.startswith('Solution'):
          junk.append(x)
        #Find lines for Labelit's pseudotrans
        if line.startswith('Analysis'):
          pseudotrans = True
          junk.append(x)
        if line.startswith('Transforming the lattice'):
          pseudotrans = True

    if len(junk) == 0:
      if spot_problem:
        if min_spots:
          return (('min spots', line))
        else:
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
      else:
        if self.multiproc:
          return ('failed')
        else:
          return ('no index')

    #Parse Labelit results
    for line in tmp[junk[0]:]:
      if len(line.split()) == 15:
        labelit_sol.append(line.split())
        labelit_face.append(line.split()[0])
        labelit_solution.append(line.split()[1])
        labelit_metric.append(line.split()[2])
        labelit_fit.append(line.split()[3])
        labelit_rmsd.append(line.split()[4])
        labelit_spots_fit.append(line.split()[5])
        labelit_system.append(line.split()[6:8])
        labelit_cell.append(line.split()[8:14])
        labelit_volume.append(line.split()[14])
    #If multiple indexing choice for same SG... taking care of it.
    if multi_sg:
      return(('fix_cell',error_lg,labelit_sol))
    #Getting Mosflm results with Labelit pseudotrans present
    if len(junk) == 3:
      tmp2 = tmp[junk[1]+1:junk[2]-1]
    #If no pseudotrans...
    else:
      tmp2 = tmp[junk[1]+1:]
    #Parse Mosflm results
    for line in tmp2:
      run = True
      if len(line.split()) == 9:
        x = 1
        mosflm_face.append(line.split()[0])
        if line.split()[0].startswith(':)'):
          mosflm_index = 'index'+line.split()[1].zfill(2)
      elif len(line.split()) == 8:
        x = 0
        mosflm_face.append(' ')
      else:
        run = False
      if run:
        mosflm_solution.append(line.split()[0+x])
        mosflm_sg.append(line.split()[1+x])
        mosflm_beam_x.append(line.split()[2+x])
        mosflm_beam_y.append(line.split()[3+x])
        mosflm_distance.append(line.split()[4+x])
        mosflm_res.append(line.split()[5+x])
        mosflm_mos.append(line.split()[6+x])
        mosflm_rms.append(line.split()[7+x])
    #Sometimes Labelit works with few spots, sometimes it doesn't...
    if few_spots:
      if os.path.exists(mosflm_index) == False:
        return ('min good spots')

    data = { 'labelit_face'     : labelit_face,
             'labelit_solution' : labelit_solution,
             'labelit_metric'   : labelit_metric,
             'labelit_fit'      : labelit_fit,
             'labelit_rmsd'     : labelit_rmsd,
             'labelit_spots_fit': labelit_spots_fit,
             'labelit_system'   : labelit_system,
             'labelit_cell'     : labelit_cell,
             'labelit_volume'   : labelit_volume,
             'labelit_iteration': str(iteration),
             'labelit_bc'       : labelit_bc,
             'pseudotrans'      : pseudotrans,
             'mosflm_face'      : mosflm_face,
             'mosflm_solution'  : mosflm_solution,
             'mosflm_sg'        : mosflm_sg,
             'mosflm_beam_x'    : mosflm_beam_x,
             'mosflm_beam_y'    : mosflm_beam_y,
             'mosflm_distance'  : mosflm_distance,
             'mosflm_res'       : mosflm_res,
             'mosflm_mos'       : mosflm_mos,
             'mosflm_rms'       : mosflm_rms,
             'mosflm_index'     : mosflm_index,
             'output'           : tmp}
    #Utils.pp(self,data)
    return(data)

  except:
    self.logger.exception('**Error in Parse.ParseOutputLabelit**')
    return(None)

def ParseOutputLabelitNoMosflm(self,inp,iteration=0):
  """
  Parses Labelit results and filters for specific errors. Cleans up the output AND looks for best solution
  then passes info back to caller.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputLabelitNoMosflm')
  tmp                = []
  junk               = []
  labelit_sol        = []
  pseudotrans        = False
  multi_sg           = False
  few_spots          = False
  min_spots          = False
  spot_problem       = False
  labelit_face       = []
  labelit_solution   = []
  labelit_metric     = []
  labelit_fit        = []
  labelit_rmsd       = []
  labelit_spots_fit  = []
  labelit_system     = []
  labelit_cell       = []
  labelit_volume     = []
  labelit_bc         = {}
  #mosflm_sol         = []
  mosflm_index       = False
  mosflm_face        = []
  mosflm_solution    = []
  mosflm_sg          = []
  mosflm_beam_x      = []
  mosflm_beam_y      = []
  mosflm_distance    = []
  mosflm_res         = []
  mosflm_mos         = []
  mosflm_rms         = []

  try:
    #If results empty, then fail
    if len(inp) == 0:
        return ('failed')
    #Check for errors
    for x,line in enumerate(inp):
      tmp.append(line)
      if len(line) > 1:
        if line.startswith('distl_minimum_number_spots'):
          min_spots = line
          #return (('min spots', line))
        if line.startswith('RuntimeError:'):
          return ('failed')
        if line.startswith('ValueError:'):
          return ('failed')
        if line.startswith('Labelit finds no reasonable solution'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('No_Indexing_Solution: Unreliable model'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith("No_Indexing_Solution: (couldn't find 3 good basis vectors)"):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('MOSFLM_Warning: MOSFLM logfile declares FATAL ERROR'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('ValueError: min()'):
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
        if line.startswith('Spotfinder Problem:'):
          spot_problem = True
        if line.startswith('InputFileError: Input error: File header must contain the sample-to-detector distance in mm; value is 0.'):
          return ('fix labelit')
        if line.startswith('InputFileError: Input error:'):
          return ('no pair')
        if line.startswith('Have '):
          self.min_good_spots = line.split()[1].rstrip(';')
          few_spots = True
        if line.startswith('UnboundLocalError'):
          return ('bad input')
        if line.startswith('divide by zero'):
          return ('bumpiness')
        #Could give error is too many choices with close cell dimensions, but...
        if line.startswith('No_Lattice_Selection: In this case'):
          multi_sg = True
          error_lg = line.split()[11]
        if line.startswith('No_Lattice_Selection: The known_symmetry'):
          return ('bad input')
        #if line.startswith('MOSFLM_Warning: MOSFLM does not give expected results on r_'):
        #    return ('mosflm error')
        #Save the beam center
        if line.startswith('Beam center'):
          labelit_bc['labelit_x_beam'] = line.split()[3][:-3]
          labelit_bc['labelit_y_beam'] = line.split()[5][:-3]
        #Now save line numbers for parsing Labelit and Mosflm results
        if line.startswith('Solution'):
          junk.append(x)
        #Find lines for Labelit's pseudotrans
        if line.startswith('Analysis'):
          pseudotrans = True
          junk.append(x)
        if line.startswith('Transforming the lattice'):
          pseudotrans = True

    if len(junk) == 0:
      if spot_problem:
        if min_spots:
          return (('min spots', line))
        else:
          if self.multiproc:
            return ('failed')
          else:
            return ('no index')
      else:
        if self.multiproc:
          return ('failed')
        else:
          return ('no index')

    #Parse Labelit results
    for line in tmp[junk[0]:]:
      if len(line.split()) == 15:
        labelit_sol.append(line.split())
        labelit_face.append(line.split()[0])
        labelit_solution.append(line.split()[1])
        labelit_metric.append(line.split()[2])
        labelit_fit.append(line.split()[3])
        labelit_rmsd.append(line.split()[4])
        labelit_spots_fit.append(line.split()[5])
        labelit_system.append(line.split()[6:8])
        labelit_cell.append(line.split()[8:14])
        labelit_volume.append(line.split()[14])
    #If multiple indexing choice for same SG... taking care of it.
    if multi_sg:
      return(('fix_cell',error_lg,labelit_sol))
    #Getting Mosflm results with Labelit pseudotrans present
    if len(junk) == 3:
      tmp2 = tmp[junk[1]+1:junk[2]-1]
    #If Mosflm isn't run
    elif len(junk) == 1:
      tmp2 = False
    #If no pseudotrans...
    else:
      tmp2 = tmp[junk[1]+1:]
    #Parse Mosflm results
    if tmp2:
      for line in tmp2:
        run = True
        if len(line.split()) == 9:
          x = 1
          mosflm_face.append(line.split()[0])
          if line.split()[0].startswith(':)'):
            mosflm_index = 'index'+line.split()[1].zfill(2)
        elif len(line.split()) == 8:
          x = 0
          mosflm_face.append(' ')
        else:
          run = False
        if run:
          mosflm_solution.append(line.split()[0+x])
          mosflm_sg.append(line.split()[1+x])
          mosflm_beam_x.append(line.split()[2+x])
          mosflm_beam_y.append(line.split()[3+x])
          mosflm_distance.append(line.split()[4+x])
          mosflm_res.append(line.split()[5+x])
          mosflm_mos.append(line.split()[6+x])
          mosflm_rms.append(line.split()[7+x])
      #Sometimes Labelit works with few spots, sometimes it doesn't...
      if few_spots:
        if os.path.exists(mosflm_index) == False:
          return ('min good spots')

    data = { 'labelit_face'     : labelit_face,
             'labelit_solution' : labelit_solution,
             'labelit_metric'   : labelit_metric,
             'labelit_fit'      : labelit_fit,
             'labelit_rmsd'     : labelit_rmsd,
             'labelit_spots_fit': labelit_spots_fit,
             'labelit_system'   : labelit_system,
             'labelit_cell'     : labelit_cell,
             'labelit_volume'   : labelit_volume,
             'labelit_iteration': str(iteration),
             'labelit_bc'       : labelit_bc,
             'pseudotrans'      : pseudotrans,
             'mosflm_face'      : mosflm_face,
             'mosflm_solution'  : mosflm_solution,
             'mosflm_sg'        : mosflm_sg,
             'mosflm_beam_x'    : mosflm_beam_x,
             'mosflm_beam_y'    : mosflm_beam_y,
             'mosflm_distance'  : mosflm_distance,
             'mosflm_res'       : mosflm_res,
             'mosflm_mos'       : mosflm_mos,
             'mosflm_rms'       : mosflm_rms,
             'mosflm_index'     : mosflm_index,
             'output'           : tmp}
    #Utils.pp(self,data)
    return(data)

  except:
    self.logger.exception('**Error in Parse.ParseOutputLabelitNoMosflm**')
    return(None)

def ParseOutputLabelitPP(self,inp):
  """
  Parse Labelit.precession_photo.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputLabelitPP')
  try:
    temp = []
    image = False
    for line in inp:
      temp.append(line)
      if line.startswith('Exception: File not found:'):
        #path = line.split()[-1]
        s = line.rindex('_')+1
        e = line.rindex('.')
        image = int(line[s:e])-1
    if image:
      return(image)

  except:
    self.logger.exception('**Error in Parse.ParseOutputLabelitPP**')
    #return((None))

def ParseOutputDistl(self, inp):
  """
  parse distl.signal_strength
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputDistl')
  try:
    spot_total   = []
    spot_inres   = []
    good_spots   = []
    labelit_res  = []
    distl_res    = []
    max_cell     = []
    ice_rings    = []
    overloads    = []
    min1         = []
    max1         = []
    mean1        = []
    signal_strength = False
    for line in inp:
      if line.count('Spot Total'):
        spot_total.append(line.split()[3])
      if line.count('In-Resolution Total'):
        spot_inres.append(line.split()[3])
      if line.count('Good Bragg'):
        good_spots.append(line.split()[4])
      if line.count('Method 1'):
        labelit_res.append(line.split()[4])
      if line.count('Method 2'):
        distl_res.append(line.split()[4])
      if line.count('Maximum unit cell'):
        max_cell.append(line.split()[4])
      if line.count('Ice Rings'):
        ice_rings.append(line.split()[3])
      if line.count('In-Resolution Ovrld Spots'):
        overloads.append(line.split()[4])
      if line.count('Signals range'):
        signal_strength = True
        min1.append(str(int(float(line.split()[3]))))
        max1.append(str(int(float(line.split()[5]))))
        mean1.append(str(int(float(line.split()[10]))))
    if signal_strength == False:
      min1.append('0')
      max1.append('0')
      mean1.append('0')
    distl = { 'total spots'             : spot_total,
              'spots in res'            : spot_inres,
              'good Bragg spots'        : good_spots,
              'distl res'               : distl_res,
              'labelit res'             : labelit_res,
              'max cell'                : max_cell,
              'ice rings'               : ice_rings,
              'overloads'               : overloads,
              'min signal strength'     : min1,
              'max signal strength'     : max1,
              'mean int signal'         : mean1      }
    return(distl)

  except:
    self.logger.exception('**Error in Parse.ParseOutputDistl**')
    return(None)

def ParseOutputRaddose(self, inp):
    """
    Looks for dose and cell volume. Passes info back to caller
    """

    if self.verbose:
        self.logger.debug('Parse::ParseOutputRaddose')

    print inp

    try:
        for line in inp:
            if line.startswith('Total absorbed dose'):
                dose_per_image = float(line.split()[4])
            if line.startswith('** Time in sec'):
                exp_dose_lim = line.split()[11]
            if line.startswith('   Time in sec'):
                hen_lim = line.split()[13]
        raddose = {"dose per image": dose_per_image,
                   "exp dose limit": exp_dose_lim,
                   "henderson limit": hen_lim  }
        return(raddose)

    except:
        self.logger.exception('**Error in Parse.ParseOutputRaddose**')
        return(None)


def ParseOutputBestNone(self, inp):
    """
    Parse the output of a Best run to ascertain the version running
    """

    print "ParseOutputBestNone"
    print inp


def ParseOutputBest(self, inp, anom=False):
    """
    cleans up the output and looks for errors to pass back for fixing and rerunning.
    passes info back to caller
    """

    if self.verbose:
        self.logger.debug('Parse::ParseOutputBest')

    temp = []
    run_num = []
    phi_start = []
    num_images = []
    delta_phi = []
    time = []
    orig_time = []
    distance = []
    overlap = []
    new_trans = []
    h_isig = []
    r_fac = []
    red = []
    # pos = []
    com = []
    # iso_B = False
    # nbr = False
    dis = False
    # frac_unique_blind = '0.0'

    try:
        log, xml = inp

        # Check for errors in the log
        for line in log:
            """
            if line.count('ERROR: scaling error > 100%'):
              nbr = True
            """
            if line.count('***any data cannot be measured for the given time!'):
                return ('dosage too high')
            if line.count('no data can be measured with requested'):
                return ('dosage too high')
            if line.count('ERROR: radiation damage exceeds 99.9%'):
                return ('dosage too high')
            """
            if line.count('Anisotropic B-factor can not be determined'):
              iso_B = True
            """
            if line.count('ERROR: negative B-factors'):
                return('neg B')
            if line.count('Determination of B-factor failed'):
                return('neg B')
            if line.count('ERROR: the deretmination of'):
                return('neg B')
            if line.count('ERROR: unknown spacegroup'):
                return('sg')
            if line.count('ERROR: Detector pixel'):
                return('bin')

        if xml == 'None':
            return 'None'
        else:
            # Parse the xml
            for i, line in enumerate(xml):
                temp.append(line)
                if line.count("program=") and line.count("version="):
                    version = line.split("'")[3].split(" ")[0]
                    print ">>>>", line, version
                if line.count('"resolution"'):
                    res = line[line.find('>')+1:line.rfind('<')]
                if line.count('"distance"'):
                    dis = round(float(line[line.find('>')+1:line.rfind('<')]),-1)
                    if dis > 1200:
                        dis = '1200.0'
                if line.count('"i_sigma"'):
                    h_isig.append(line[line.find('>')+1:line.rfind('<')])
                if line.count('"average_i_over_sigma"'):
                    isig = line[line.find('>')+1:line.rfind('<')]
                if line.count('"completeness"'):
                    com.append(line[line.find('>')+1:line.rfind('<')])
                if line.count('"redundancy"'):
                    red.append(line[line.find('>')+1:line.rfind('<')])
                # Version 3.4.4 Linux
                if line.count('"transmission"'):
                    trans = float(line[line.find('>')+1:line.rfind('<')])
                    attenuation = str(100 - trans).zfill(3)
                # Version 3.2.0.z Mac OS X
                if line.count('"attenuation"'):
                    attenuation = float(line[line.find('>')+1:line.rfind('<')])
                    trans = attenuation # str(100 - trans).zfill(3)
                # NOT correct when I modify time and flux for efficency
                if line.count('"total_exposure_time"'):
                    tot_exp_time = line[line.find('>')+1:line.rfind('<')]
                if line.count('"total_data_collection_time"'):
                    tot_data_col_time = line[line.find('>')+1:line.rfind('<')]
                if line.count('"R_factor"'):
                    r_fac.append(line[line.find('>')+1:line.rfind('<')])
                if line.count('"fraction_achievable_%"'):
                    blind = str(100.0-float(line[line.find('>')+1:line.rfind('<')]))
                if line.count('"phi_start"'):
                    phi_start.append(line[line.find('>')+1:line.rfind('<')])
                if line.count('"phi_end">'):
                    phi_end = line[line.find('>')+1:line.rfind('<')]
                if line.count('"number_of_images"'):
                    num_images.append(line[line.find('>')+1:line.rfind('<')])
                    #For every range, save a distance for the html summary.
                    distance.append(str(dis))
                if line.count('"phi_width"'):
                    delta_phi.append(line[line.find('>')+1:line.rfind('<')])
                if line.count('"overlaps"'):
                    overlap.append(line[line.find('>')+1:line.rfind('<')])
                if line.count('"collection_run"'):
                    run_num.append(line[line.rfind('=')+2:line.rfind('"')])
                if line.count('"exposure_time"'):
                    t = float(line[line.find('>')+1:line.rfind('<')])
                    orig_time.append(t)
                    # if self.pilatus:
                    if self.vendortype in ('Pilatus-6M','ADSC-HF4M'):
                        new_trans.append(str(round(trans)))
                        time.append(str(round(t, 1)))
                    else:
                        # Set time and transmission to minimize data collection time
                        nt = t * trans
                        if trans == 100.0:
                            if t > 1:
                                new_trans.append(str(trans))
                                time.append(str(round(t,1)))
                            else:
                                new_trans.append(str(round(nt)))
                                time.append('1.0')
                        else:
                            if nt > 100:
                                new_trans.append('100.0')
                                time.append(str(round(nt/100)))
                            elif nt < 1:
                                new_trans.append(str(trans))
                                #time.append(str(t))
                                time.append(str(round(t,1)))
                            else:
                                new_trans.append(str(round(nt)))
                                time.append('1.0')

        # If best did not give strat...
        # if nbr:
        if dis == False:
            return "neg B"

        # Remove the last line in starting phi
        phi_start = phi_start[:-1]
        rot_range = str(float(phi_end) - float(phi_start[0]))

        # Removes thin sliced erroronious strategy when B-factor calc tanks.
        # if iso_B:
        #   if float(min(delta_phi)) < 0.3:
        #     return ('isotropic B')

        # Check for Best strategy giving multiple continuous runs (Bug in Best)
        if len(phi_start)> 1:
            if all(i==delta_phi[0] for i in delta_phi):
                if all(i==orig_time[0] for i in orig_time):
                    phi = float(phi_start[0])
                    i = 0
                    for x in range(len(num_images)):
                        phi += float(num_images[x])*float(delta_phi[x])
                        i += int(num_images[x])
                    if phi == float(phi_end):
                        phi_start = [phi_start[0]]
                        num_images = [str(i)]
                        time = [time[0]]
                        delta_phi = [delta_phi[0]]
                        distance = [distance[0]]
                        new_trans = [new_trans[0]]
                        overlap = [overlap[0]]
                        run_num = [run_num[0]]
        if anom:
            j1 = " anom "
        else:
            j1 = " "
        data = {
            'strategy'+j1+'best_version': version,
            'strategy'+j1+'run number': run_num,
            'strategy'+j1+'phi start': phi_start,
            'strategy'+j1+'num of images': num_images,
            'strategy'+j1+'delta phi': delta_phi,
            'strategy'+j1+'image exp time': time,
            'strategy'+j1+'distance': distance,
            'strategy'+j1+'overlap': overlap,
            'strategy'+j1+'res limit': res,
            'strategy'+j1+'anom flag': str(anom),
            'strategy'+j1+'phi end': phi_end,
            'strategy'+j1+'rot range': rot_range,
            'strategy'+j1+'completeness': com[0],
            'strategy'+j1+'redundancy': red[0],
            'strategy'+j1+'R-factor': r_fac[-1]+' ('+r_fac[-2]+')',
            'strategy'+j1+'I/sig': isig+' ('+h_isig[0]+')',
            'strategy'+j1+'total exposure time': tot_exp_time,
            'strategy'+j1+'data collection time': tot_data_col_time,
            'strategy'+j1+'frac of unique in blind region': blind,
            'strategy'+j1+'attenuation': attenuation,
            'strategy'+j1+'new transmission': new_trans
            }

        return data

    except:
        self.logger.exception('**Error in Parse.ParseOutputBest**')
        return 'None'

def ParseOutputBestPlots(self, inp):
    """
    Parse Best plots file for plots.
    """

    if self.verbose:
        self.logger.debug("Parse::ParseOutputBestPlots")

    res = []
    com = []
    ws = []
    we = []
    wilson = []
    max_delta_omega = []
    rad_damage_int_decr = []
    rad_damage_rfactor_incr = []
    osc_range = []

    # Definitions for the expected values
    cast_vals = {
        "Relative Error and Intensity Plot": {
            "Rel.Error": {"x": float, "y": float}
        }
    }

    # Run through the plot file lines and separate raw plots
    parsed_plots = {}
    in_data = False
    plot = False
    for x, line in enumerate(inp):
        # New plot
        if line.startswith("$"):
            if plot:
                self.logger.debug(plot)
                parsed_plots[plot["parameters"]["toplabel"]] = plot
            self.logger.debug("New plot")
            in_data = False
            plot = {"parameters": {}, "data": []}
            line_plot = {"parameters": {}, "data": {"series": []}}
        # Curve defs
        elif line.startswith("%"):
            # New line
            if in_data:
                self.logger.debug(line_plot)
                plot["data"].append(line_plot)
                in_data = False
                line_plot = {"parameters": {}, "data": {"series": []}}
            self.logger.debug(line)
            strip_line = line[1:].strip()
            self.logger.debug(strip_line)
            key = strip_line[:strip_line.index("=")].strip()
            self.logger.debug(key)
            val = strip_line[strip_line.index("=")+1:].replace("'", "").strip()
            self.logger.debug(val)
            line_plot["parameters"][key] = val
            self.logger.debug(line_plot)
        # Data point
        else:
            in_data = True
            self.logger.debug(plot["parameters"]["toplabel"])
            x = cast_vals[plot["parameters"]["toplabel"]][line_plot["parameters"]["linelabel"]["x"]](line.split()[0].strip())
            y = cast_vals[plot["parameters"]["toplabel"]][line_plot["parameters"]["linelabel"]["y"]](line.split()[1].strip())
            line_plot["data"]["series"].append({"name": x, "value": y})



    for x, line in enumerate(inp):
        if line.startswith("% linelabel  = 'Theory'"):
            ws.append(x)
        if line.startswith("% linelabel  = 'Pred.low errors'"):
            we.append(x-4)
            ws.append(x)
        if line.startswith("% linelabel  = 'Pred.high errors'"):
            we.append(x-4)
            ws.append(x)
        if line.startswith("% linelabel  = 'Experiment'"):
            we.append(x-1)
            #ws.append(x+5)
            ws.append(x)
        if line.startswith("% toplabel  = 'Maximal oscillation width'"):
            we.append(x-1)
        if line.startswith("% linelabel  = 'resol. "):
            res.append(x)
        if line.startswith("% linelabel  = 'compl"):
            com.append(x)

    # Assembling wilson
    for i in range(len(ws)):
        d = {}

        temp = []
        k = inp[ws[i]][inp[ws[i]].find("=")+2:].strip().replace("'", "")
        d = {"name":k, "series":[]}

        for line in inp[ws[i]+1:we[i]]:
            if len(line.split()) == 2:
                # temp.append(line.split())
                sline = line.split()
                d["series"].append({"name":float(sline[0]), "value":float(sline[1])})
        # d[k] = temp
        wilson.append(d)

    # Assembling the max_delta_omega, rad_damage_int_decr, and rad_damage_rfactor_incr
    self.logger.debug(res)
    for i in range(len(res)):
        temp = []
        d = {}
        k = inp[res[i]][inp[res[i]].find("=")+2:].strip().replace("resol. ", "").strip() + "A"
        d = {"name":k, "series":[]}
        print ">>>", k, "<<<"
        if i == 4:
            t = inp[res[i]+1:res[i]+182]
        elif i == 14:
            t = inp[res[i]+1:res[i]+102]
        elif i == len(res)-1:
            t = inp[res[i]+1:res[i]+502]
        else:
            t = inp[res[i]+1:res[i+1]-5]
        for line in t:
            sline = line.split()
            if len(sline) == 2:
                temp.append(line.split())
                d["series"].append({"name":int(sline[0]), "value":float(sline[1])})
        # d[k] = temp
        if i < 5:
            self.logger.debug("max_delta_omega")
            max_delta_omega.append(d)
        elif i > 14:
            self.logger.debug("rad_damage_rfactor_incr")
            rad_damage_rfactor_incr.append(d)
        else:
            self.logger.debug("rad_damage_int_decr")
            rad_damage_int_decr.append(d)

    # Assembling the osc_range
    for i in range(5):
        temp = []
        k = inp[com[i]][inp[com[i]].find("=")+2:].strip().replace("compl -", "").replace(".%", "%")
        d = {"name":k, "series":[]}
        if i == 0:
            t = inp[com[i]+4:com[i+1]-4]
        else:
            t = inp[com[i]+1:com[i+1]-4]
        for line in t:
            if len(line.split()) == 2:
                # temp.append(line.split())
                sline = line.split()
                d["series"].append({"name":int(sline[0]), "value":int(sline[1])})
        osc_range.append(d)

    output = {"wilson": wilson,
              "max_delta_omega": max_delta_omega,
              "rad_damage_int_decr": rad_damage_int_decr,
              "rad_damage_rfactor_incr": rad_damage_rfactor_incr,
              "osc_range": osc_range}
    return output

def ParseOutputMosflm_strat(self, inp, anom=False):
    """
    Parsing Mosflm strategy.
    """
    if self.verbose:
        self.logger.debug('Parse::ParseOutputMosflm_strat')

    try:
        temp  = []
        strat = []
        res   = []
        start = []
        end   = []
        ni    = []
        rn    = []
        seg = False
        #osc_range  = str(self.header.get('osc_range'))
        if self.vendortype in ('Pilatus-6M','ADSC-HF4M'):
            osc_range = '0.2'
        else:
            if float(self.header.get('osc_range')) < 0.5:
                osc_range = '0.5'
            else:
                osc_range  = str(self.header.get('osc_range'))
        distance   = str(self.header.get('distance'))
        mosflm_seg = str(self.preferences.get("mosflm_seg", "1"))

        index = False
        index_res = False
        for x, line in enumerate(inp):
            print mosflm_seg, seg, x, line
            temp.append(line)
            if mosflm_seg != '1':
                if line.startswith(' This may take some time......'):
                    index = x
                    seg = True
                if line.startswith(' Testing to find the best combination'):
                    index = x
                    seg = True
            else:
                if line.startswith(' Checking completeness of data'):
                    index = x
            if line.startswith(' Breakdown as a Function of Resolution'):
                index_res = temp.index(line)
            if line.startswith(' Mean multiplicity'):
                index_mult = temp.index(line)
                mult2 = ((temp[index_mult]).split()[-1])
            if line.count('** ERROR ** The matrix Umat is not a simple rotation matrix'):
                if self.multicrystalstrat:
                    return "sym"
        if seg:
            strat.append(temp[index:index + 10 + 2*int(mosflm_seg)])
        elif index:
            strat.append(temp[index:index + 12])
        counter = 0
        for line in strat:
            comp = line[3].split()[3]
            while counter < int(mosflm_seg):
                s1 = float(line[5 + counter].split()[1])
                e1 = float(line[5 + counter].split()[3])
                images1 = int((e1 - s1) / float(osc_range))
                ni.append(images1)
                if s1 < 0:
                    s1 += 360
                if s1 > 360:
                    s1 -= 360
                start.append(s1)
                if e1 < 0:
                    e1 += 360
                if e1 > 360:
                    e1 -= 360
                end.append(e1)
                counter += 1
                rn.append(counter)
        if index_res:
            res.append(temp[index_res:index_res + 17])
        for line in res:
            resolution = line[15].split()[0]
        if anom:
            j1 = ' anom '
        else:
            j1 = ' '
        data = {'strategy'+j1+'run number': rn,
                'strategy'+j1+'phi start': start,
                'strategy'+j1+'phi end': end,
                'strategy'+j1+'num of images': ni,
                'strategy'+j1+'resolution': resolution,
                'strategy'+j1+'completeness': comp,
                'strategy'+j1+'redundancy': mult2,
                'strategy'+j1+'distance': distance,
                'strategy'+j1+'image exp time': self.time,
                'strategy'+j1+'delta phi': osc_range}
        return data

    except:
        self.logger.exception('**Error in Parse.ParseOutputMosflm_strat**')
        return(None)

def ParseOutputStacAlign(self, inp):
  """
  parse Stac Alignment.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputStacAlign')
  v1    = []
  v2    = []
  omega = []
  kappa = []
  phi   = []
  trans = []
  rank  = []
  no_sol = []
  goni = []

  try:
    orientations = inp[0]
    log = inp[1:]
    split = (orientations.split('<possible_orientation>')[1:])
    for line in split:
      v1.append(line[line.index('<v1>'):line.index('</v1')].strip('<v1>'))
      v2.append(line[line.index('<v2>'):line.index('</v2')].strip('<v2>'))
      omega.append(line[line.index('<omega>'):line.index('</omega')].strip('<omega>'))
      kappa.append(line[line.index('<kappa>'):line.index('</kappa')].strip('<kappa>'))
      phi.append(line[line.index('<phi>'):line.index('</phi')].strip('<phi>'))
      trans.append(line[line.index('<trans>'):line.index('</trans')].strip('<trans>'))
      rank.append(line[line.index('<rank>'):line.index('</rank')].strip('<rank>'))
    for line in log:
      if line.startswith(' - Could not find solution'):
        temp = []
        junk1 = line.index('V1:')
        junk2 = line.index('V2:')
        temp.append(line[junk1+4:junk2-3])
        temp.append(line[junk2+4:-1])
        no_sol.append(temp)
      if line.startswith(' - Goniometer does not allow the solution'):
        goni.append(line)

    stac = { 'v1'            :  v1,
             'v2'            :  v2,
             'omega'         : omega,
             'kappa'         : kappa,
             'phi'           : phi,
             'trans'         : trans,
             'rank'          : rank,
             'no_sol'        : no_sol,
             'goni limited'  : goni  }
    return(stac)

  except:
    self.logger.exception('**Error in Parse.ParseOutputStacAlign**')
    return(None)

def ParseOutputStacStrat(self, inp):
  """
  parse Stac Strategy.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputStacStrat')
  strat_id    = []
  omegas      = []
  omegaf      = []
  kappa       = []
  phi         = []
  comp        = []
  rank        = []

  try:
    split = (inp.split('<generated_sweep>')[1:])
    for line in split:
      strat_id.append(line[line.index('<strategyID>'):line.index('</strategyID>')].strip('<strategyID>'))
      omegas.append(line[line.index('<omegaStart>'):line.index('</omegaStart>')].strip('<omegaStart>'))
      omegaf.append(line[line.index('<omegaEnd>'):line.index('</omegaEnd>')].strip('<omegaEnd>'))
      kappa.append(line[line.index('<kappa>'):line.index('</kappa>')].strip('<kappa>'))
      phi.append(line[line.index('<phi>'):line.index('</phi>')].strip('<phi>'))
      comp.append(line[line.index('<completeness>'):line.index('</completeness>')].strip('<completeness>'))
      rank.append(line[line.index('<rank>'):line.index('</rank>')].strip('<rank>'))
    stac = { 'strat ID'      :  strat_id,
             'omega start'   :  omegas,
             'omega finish'  :  omegaf,
             'kappa'         :  kappa,
             'phi'           :  phi,
             'completeness'  :  comp,
             'rank'          :  rank     }
    return(stac)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputStacStrat**')
    return(None)

def ParseOutputShelx(self,inp,inp2=False):
  """
  Parse Shelx CDE output.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputShelx')
  import shutil
  try:
    temp   = []
    temp2  = []
    data = []
    shelxc_res = []
    shelxc_data = []
    shelxc_isig = []
    shelxc_comp = []
    shelxc_dsig = []
    shelxc_chi  = []
    shelxc_cc   = []
    shelxd_try = []
    shelxd_cca = []
    shelxd_ccw = []
    shelxd_fom = []
    shelxd_cfom = []
    #shelxe_cc = []
    shelxe_contrast = []
    shelxe_con = []
    shelxe_sites = []
    shelxe_mapcc = []
    shelxe_res = []
    fom = []
    se_cc = []
    build_cc = []
    build_nres = []
    contrast = []
    con = []
    index = []
    junk = []
    junk2 = []
    junk3 = []
    sites_occ = []
    inverse = False
    nosol = False
    #fa = True
    failed_inv = False
    failed_ninv = False
    #par = False
    cycles = False
    ind = []
    mad = []
    count = 0
    counter = 0
    """
    if inp2 == []:
        fa = False
    """
    for x,line in enumerate(inp):
      temp.append(line)
      if line.startswith(' ** ARRAYS TOO SMALL TO STORE REFLECTION DATA'):
        return ('array')
      """
      junk1 = line.find('threads running in parallel')
      if junk1 != -1:
        par = True
      """
      if line.count('Reflections read from'):
        data.append(line.split()[4])
      if line.startswith(' Resl.'):
        if line.split()[2] == '-':
          split = line.split()[3::2]
        else:
          split = line.split()[2:]
        while len(split) < 11:
          split.append('0.00')
        shelxc_res.append(split)
      if line.startswith(' N(data)'):
        split = line.split()[1:]
        while len(split) < 11:
          split.append('0')
        shelxc_data.append(split)
      if line.startswith(' <I/sig>'):
        split = line.split()[1:]
        while len(split) < 11:
          split.append('0.0')
        shelxc_isig.append(split)
      if line.startswith(' %Complete'):
        split = line.split()[1:]
        while len(split) < 11:
          split.append('0.0')
        shelxc_comp.append(split)
      if line.startswith(' <d"/sig>'):
        split = line.split()[1:]
        while len(split)  < 11:
          split.append('0.00')
        shelxc_dsig.append(split)
      if line.startswith(' Chi-sq'):
        split = line.split()[1:]
        while len(split)  < 11:
          split.append('0.00')
        shelxc_chi.append(split)
      if line.startswith(' CC(1/2)'):
        split = line.split()[1:]
        while len(split)  < 11:
          split.append('0.00')
        shelxc_cc.append(split)
      #Look for MAD CC.
      if line.count('Correlation coefficients (%)'):
        ind.append(x)
      if line.count('For zero signal'):
        ind.append(x)
      if line.startswith(' Try  '):
        shelxd_try.append(line.split()[1][:-1])
        """
        if par:
          shelxd_cca.append(line[31:37].strip())
          shelxd_ccw.append(line[38:43].strip())
          shelxd_fom.append(line[73:80].strip())
        else:
          shelxd_cca.append(line[23:30].strip())
          shelxd_ccw.append(line[31:37].strip())
          shelxd_fom.append(line[70:76].strip())
        """
        shelxd_cca.append(line[line.index('Weak')+4:line.index('Weak')+9].strip())
        shelxd_ccw.append(line[line.index('Weak')+11:line.index('Weak')+16].strip())
        shelxd_fom.append(line[line.index('PATFOM')+6:].strip())
        shelxd_cfom.append(line[line.index('CFOM')+4:line.index('CFOM')+9].strip())
      if inp2:
        """
        if line.startswith(' Pseudo-free CC'):
          junk.append((line.split()[3]))
          #se_cc.append((line.split()[3]))
        """
        if line.startswith(' Estimated mean FOM ='):
          fom.append(line.split()[4])
          se_cc.append(line.split()[8])
        #Determine when invert was used to find which failed
        if line.startswith(' -i '):
          junk.append(line.split()[1])
        #Decide if there is an error in ShelxE and which hand it occurred.
        if line.count('+  SHELXE finished'):
          counter += 1
          l = [build_cc,build_nres]
          for p in l:
            if len(p) < counter:
              p.append('0')
          if temp[temp.index(line)-3].startswith(' ** '):
            count += 1
            if junk[-1] == 'invert':
              failed_inv = True
            if junk[-1] == 'unset':
              failed_ninv = True
            """
            if junk[-1] == 'NOT':
              failed_ninv = True
            """
        if line.startswith(' CC for partial structure'):
          build_cc.append(line.split()[8])
        if line.count('residues left after pruning'):
          build_nres.append(line.split()[0])
        if line.count('<wt> ='):
          if line.split()[3] == 'Contrast':
            contrast.append(line.split()[5][:-1])
            con.append(line.split()[8])
            cycles = line.split()[12]
        if line.count('<mapCC>'):
          shelxe_mapcc.extend(line.split()[1:])
        #Fix if low res is greater than 10A.
        if line.count('d    inf'):
          if len(line.split()[2]) == 1:
            shelxe_res.extend(line.split()[3::2])
          else:
            shelxe_res.append('15.00')
            shelxe_res.extend(line.split()[4::2])
        if line.count('Chain tracing'):
          #Check to see if autotracing is turned on. If not then set the results to 0.
          if line.split()[0] == '0.0':
            build_cc.append('0.000')
            build_nres.append('0')
            shelxe_contrast.append('')
            if self.shelx_build:
              for i in range(0,int(cycles)):
                contrast.append('0.000')
                con.append('0.000')
    #Figure out name and order of data in log.
    data = data[:len(shelxc_isig)]
    #Grab CC between MAD datasets
    if len(ind) == 2:
      for line in temp[ind[0]+2:ind[1]-1]:
        mad.append(line.split())
    #If autotracing failed.
    if count > 0:
      if self.shelx_build:
        if count == 2:
          return ('trace failed both')
        else:
          if failed_inv:
            return ('trace failed inv')
          if failed_ninv:
            return ('trace failed ninv')
    else:
      l = len(shelxd_try)
      if l == 0:
        shelxd_try = ['1']
      else:
        if self.multiShelxD:
          shelxd_try = []
          for i in range(1,l+1):
            shelxd_try.append(str(i))
      """
      #Had to add since ShelxD does not print PATFOM if it is 0.00 for iteration
      for x in range(len(index1)):
        if temp[index1[x]+1].startswith(' PATFOM'):
          shelxd_fom.append(temp[index1[x]+1].split()[1])
        else:
          shelxd_fom.append('0.00')
      """
      if inp2:
        for x in range(len(inp)):
          if inp[x].startswith('  Site     x'):
            index.append(x)
          if inp[x].startswith(' Site    x'):
            index.append(x)
        #shelxe_cc.append(junk[3])
        #shelxe_cc.append(junk[-1])
        for line in contrast:
          junk3.append(float(line))
        avg_contrast1 = sum(junk3[0:int(cycles)])/int(cycles)
        shelxe_contrast= contrast[0:int(cycles)]
        shelxe_con = con[0:int(cycles)]
        if self.shelx_build:
          avg_contrast2 = sum(junk3[int(cycles)*2:int(cycles)*3])/int(cycles)
          shelxe_contrast.extend(contrast[int(cycles)*2:int(cycles)*3])
          shelxe_con.extend(con[int(cycles)*2:int(cycles)*3])
          s1 = 'junkt'
        else:
          avg_contrast2 = sum(junk3[int(cycles):int(cycles)*2])/int(cycles)
          shelxe_contrast.extend(contrast[int(cycles):int(cycles)*2])
          shelxe_con.extend(con[int(cycles):int(cycles)*2])
          s1 = 'junk'
        if avg_contrast1 > avg_contrast2:
          i = 0
          pdb = '%s.pdb'%s1
          shelxe_sites.extend(temp[index[0]+1:index[1]-1])
        else:
          inverse = True
          i = 1
          pdb = '%s_i.pdb'%s1
          shelxe_sites.extend(temp[index[2]+1:index[3]-1])
        #Here if ShelxE autotracing works.
        shelxe_pdb = 'None'
        if self.shelx_build:
          if os.path.exists(pdb):
            shutil.copy(pdb,'shelxe_autotrace.pdb')
            path = os.path.join(os.getcwd(),'shelxe_autotrace.pdb')
            shelxe_pdb = path
        shelxe_cc  = se_cc[i]
        shelxe_fom = fom[i]
        shelxe_trace_cc = build_cc[i]
        shelxe_trace_nres = build_nres[i]
        if abs(avg_contrast1 - avg_contrast2) < 0.05:
          nosol = True
        for line in inp2:
          temp2.append(line)
          if line.startswith('REM Best'):
            best_try = '1'
            best_cc  = line.split()[5]
            best_ccw = line.split()[7]
            best_cfom = line.split()[9]
          if line.startswith('REM TRY'):
            best_try = line.split()[2]
            best_cc  = line.split()[4]
            best_ccw = line.split()[6]
            best_cfom = line.split()[8]
          if line.startswith('UNIT'):
            index2 = temp2.index(line)
          if line.startswith('HKLF'):
            index3 = temp2.index(line)
        junk2.extend(temp2[index2+1:index3])
        for line in junk2:
          sites_occ.append(line.split()[5])
      else:
        #Set all the params if no fa file exists.
        shelxe_res = shelxc_res
        #for i in range(0,20):
        for i in range(0,int(cycles)):
          shelxe_mapcc.append('0.00')
        #for i in range(0,40):
        for i in range(0,int(cycles)*2):
          shelxe_contrast.append('0.00')
          shelxe_con.append('0.00')
        #shelxe_cc.append('0.00')
        shelxe_sites.append('1   0.0000   0.0000   0.0000   0.0000    0.000')
        best_try = '1'
        best_cc = '0.000'
        best_ccw= '0.000'
        best_cfom= '0.000'
        sites_occ.append('0.0000')
        nosol = True
        shelxe_fom = '0.000'
        shelxe_cc  = '0.000'
        shelxe_pdb = None
        shelxe_trace_cc = '0.000'
        shelxe_trace_nres = '0'
      #Fix issue if results are negative
      l1 = [shelxd_ccw,shelxd_cca,shelxd_fom,shelxd_cfom]
      for x in range(len(l1)):
        for line in l1[x]:
          if line.startswith('-'):
            index = l1[x].index(line)
            l1[x].remove(line)
            l1[x].insert(index,'0.00')
      #If SHELXD fails, set results to 0.0
      if len(shelxc_dsig) == 0:
        shelxc_dsig = [['0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0']]
      if len(shelxc_cc) == 0:
        shelxc_cc = [['0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0']]
      if len(shelxd_fom) == 0:
        shelxd_fom = ['0.00']
      if len(shelxd_cca) == 0:
        shelxd_cca = ['0.00']
      if len(shelxd_ccw) == 0:
        shelxd_ccw = ['0.00']
      if len(shelxd_cfom) == 0:
        shelxd_cfom = ['0.00']
        nosol = True

      shelx = { 'shelx_data'         : data,
                'shelxc_res'         : shelxc_res,
                'shelxc_data'        : shelxc_data,
                'shelxc_isig'        : shelxc_isig,
                'shelxc_comp'        : shelxc_comp,
                'shelxc_dsig'        : shelxc_dsig,
                'shelxc_chi-sq'      : shelxc_chi,
                'shelxc_cchalf'      : shelxc_cc,
                'shelxd_try'         : shelxd_try,
                'shelxd_cca'         : shelxd_cca,
                'shelxd_ccw'         : shelxd_ccw,
                'shelxd_fom'         : shelxd_fom,
                'shelxd_cfom'        : shelxd_cfom,
                'shelxd_best_occ'    : sites_occ,
                'shelxd_best_try'    : best_try,
                'shelxd_best_cc'     : best_cc,
                'shelxd_best_ccw'    : best_ccw,
                'shelxd_best_cfom'   : best_cfom,
                'shelxe_fom'         : shelxe_fom,
                'shelxe_trace_pdb'   : shelxe_pdb,
                'shelxe_trace_cc'    : shelxe_trace_cc,
                'shelxe_trace_nres'  : shelxe_trace_nres,
                'shelxe_cc'          : shelxe_cc,
                'shelxe_cc2'         : se_cc,
                'shelxe_mapcc'       : shelxe_mapcc,
                'shelxe_res'         : shelxe_res,
                'shelxe_contrast'    : shelxe_contrast,
                'shelxe_con'         : shelxe_con,
                'shelxe_sites'       : shelxe_sites,
                'shelxe_inv_sites'   : str(inverse),
                'shelxe_nosol'       : str(nosol),
                'MAD_CC'             : mad       }
      return(shelx)

  except:
    self.logger.exception('**Error in Parse.ParseOutputShelx**')
    return(None)

def ParseOutputShelxC(self, inp):
  """
  Parse Shelx C output.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputShelxC')
  try:
    temp   = []
    shelxc_res = []
    shelxc_dsig = False

    for line in inp:
      line.rstrip()
      temp.append(line)
      """
      if line.startswith('** NO REFLECTIONS WITH  E >'):
        return (None)
      """
      if line.startswith(' Resl.'):
        shelxc_res.extend(line.split()[3::2])
        while len(shelxc_res) < 11:
          shelxc_res.append('0.00')
      if line.startswith(' N(data)'):
        shelxc_data = line.split()[1:]
        while len(shelxc_data) < 11:
          shelxc_data.append('0')
      if line.startswith(' <I/sig>'):
        shelxc_isig = line.split()[1:]
        while len(shelxc_isig) < 11:
          shelxc_isig.append('0.0')
      if line.startswith(' %Complete'):
        shelxc_comp = line.split()[1:]
        while len(shelxc_comp) < 11:
          shelxc_comp.append('0.0')
      if line.startswith(' <d"/sig>'):
        shelxc_dsig = line.split()[1:]
        while len(shelxc_dsig)  < 11:
          shelxc_dsig.append('0.00')
    #If SHELXD fails, set results to 0.0
    if shelxc_dsig == False:
      shelxc_dsig = ['0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0']

    shelx = { 'shelxc_res'      : shelxc_res,
              'shelxc_data'     : shelxc_data,
              'shelxc_isig'     : shelxc_isig,
              'shelxc_comp'     : shelxc_comp,
              'shelxc_dsig'     : shelxc_dsig,
                                                }
    return(shelx)

  except:
    self.logger.exception('**Error in Parse.ParseOutputShelxC**')
    return(None)

def ParseOutputAutoSol(self,inp):
  """
  Parse phenix.autosol output.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputAutoSol')
  try:
    tmp  = []
    dir1 = False
    bayes_cc = '0'
    fom = '0'
    sites_start = '0'
    sites_refined = '0'
    res_built = '0'
    side_built = '0'
    num_chains = '0'
    mm_cc = '0.0'
    r_rfree = '0.0/0.0'
    for x,line in enumerate(inp):
      tmp.append(line)
      #Only grab the first time
      if line.startswith('Working directory:'):
        if dir1 == False:
          dir1 = line.split()[2]
      if line.count('SG: '):
        sg = line[4:-1].replace(' ','')
      if line.count('Guesses of scattering factors'):
        ha_type = line.split()[5]
        index = x
      if line.count('Solution #'):
        bayes_cc = line.split()[4]
        fom = line.split()[-1]
      if line.startswith('Sites:'):
        sites_start = line.split()[1]
        sites_refined = line.split()[-1]
      if line.count('Residues built:'):
        res_built = line.split()[2]
      if line.count('Side-chains built:'):
        side_built = line.split()[2]
      if line.count('Chains:'):
        num_chains = line.split()[1]
      if line.count('Overall model-map correlation:'):
        mm_cc = line.split()[3]
      if line.count('R/R-free:'):
        r_rfree = line.split()[1]
      """
      if line.startswith('Density modification logfile'):
        dmr = line.split()[5][3:7]
      """
    scat_fac = tmp[index+2].split()[2:4]
    wave = tmp[index+2].split()[1]

    phenix = { 'directory'       : dir1,
               'sg'              : sg,
               'wavelength'      : wave,
               'ha_type'         : ha_type,
               "f'"              : scat_fac[0],
               'f"'              : scat_fac[1],
               'bayes-cc'        : bayes_cc,
               'fom'             : fom,
               'sites_start'     : sites_start,
               'sites_refined'   : sites_refined,
               'res_built'       : res_built,
               'side_built'      : side_built,
               'num_chains'      : num_chains,
               'model-map_cc'    : mm_cc,
               'r/rfree'         : r_rfree,
               #'den_mod_r'       : dmr
                                                   }
    return(phenix)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputAutoSol**')
    return(setAutoSolFalse('ERROR'))

def ParseOutputAutoBuild(self,inp):
  """
  Parse phenix.autobuild.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputAutoBuild')
  try:
    temp = []
    for line in inp:
      line.rstrip()
      temp.append(line)
      if line.startswith('This is new best model with score'):
        index = temp.index(line)
      if line.startswith('Working directory:'):
        dir1 = line.split()[2]
      """
      if line.startswith('Current overall_best model and map'):
        index2 = temp.index(line)
      """
      if line.startswith('Model ('):
        pdb = line.split()[-1]
      if line.startswith('R and R-free:'):
        r = line.split()[3]
        rfree = line.split()[4]
      if line.startswith('Map-model CC:'):
        mmcc = line.split()[-1]
      if line.startswith('from: refine'):
        mtz = line.split()[-1]
      if line.startswith('from: overall_best_refine'):
        mtz = line.split()[-1]
    resi_built = temp[index-1].split()[3][6:]
    seq_placed = temp[index-1].split()[4][7:]
    chains = temp[index-1].split()[5][7:]
    score = temp[index].split()[8]
    autobuild = { 'AutoBuild_pdb'      : pdb,
                  'AutoBuild_mtz'      : mtz,
                  'AutoBuild_rfac'     : r,
                  'AutoBuild_rfree'    : rfree,
                  'AutoBuild_mmcc'     : mmcc,
                  'AutoBuild_built'    : resi_built,
                  'AutoBuild_placed'   : seq_placed,
                  'AutoBuild_chains'   : chains,
                  'AutoBuild_score'    : score,
                  'AutoBuild_dir'      : dir1
                                                 }
    return(autobuild)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputAutoBuild**')
    return(None)

def ParseOutputPhaser(self,inp):
  """
  Parse Phaser output.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputPhaser')
  try:
    pdb   = False
    st    = False
    clash = 'NC'
    #end   = len(inp)
    end    = False
    temp  = []
    tncs  = False
    nmol  = 0
    for x,line in enumerate(inp):
      temp.append(line)
      directory = os.getcwd()
      #if line.startswith('FATAL RUNTIME ERROR: The composition'):
        #return('matthews')
      if line.count('SPACEGROUP'):
        sg = line.split()[-1]
      if line.count('Solution') or line.count('Partial Solution '):
        if line.count('written'):
          if line.count('PDB'):
            pdb = line.split()[-1]
          if line.count('MTZ'):
            mtz = line.split()[-1]
        if line.count('RFZ='):
          st = x
      if line.count('SOLU SET'):
        st = x
      if line.count('SOLU ENSEMBLE'):
        end = x
    if st:
      for line in inp[st:end]:
        if line.count('SOLU 6DIM'):
          nmol += 1
        for param in line.split():
          if param.startswith('RFZ'):
            if param.count('=') == 1:
              rfz = param[param.find('=')+param.count('='):]
          if param.startswith('RF*0'):
            rfz = 'NC'
          if param.startswith('TFZ'):
            if param.count('=') == 1:
              tfz = param[param.find('=')+param.count('='):]
          if param.startswith('TF*0'):
            tfz = 'NC'
          if param.startswith('PAK'):
            clash = param[param.find('=')+param.count('='):]
          if param.startswith('LLG'):
            llgain = param[param.find('=')+param.count('='):]
          if param.startswith('+TNCS'):
            tncs = True
    if pdb == False:
      phaser = setPhaserFailed('No solution')
    else:
      phaser = {      'AutoMR nosol': 'False',
                      'AutoMR pdb'  : pdb,
                      'AutoMR mtz'  : mtz,
                      'AutoMR gain' : llgain,
                      'AutoMR rfz'  : rfz,
                      'AutoMR tfz'  : tfz,
                      'AutoMR clash': clash,
                      'AutoMR dir'  : directory,
                      'AutoMR sg'   : sg,
                      'AutoMR tNCS' : tncs,
                      'AutoMR nmol' : nmol,
                      'AutoMR adf'  : 'None',
                      'AutoMR peak' : 'None'}
    return(phaser)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputPhaser**')
    return(setPhaserFailed('No solution'))

def ParseOutputPhaserNCS(self,inp):
  if self.verbose:
    self.logger.debug('Parse::ParseOutputPhaserNCS')
  try:
    temp = []
    start = []
    d = {}
    for x,line in enumerate(inp):
      temp.append(line)
      if line.count('$$ loggraph $$'):
        start.append(x)
    if len(start) > 0:
      for i in range(len(start)):
        if i == 0:
          title = 'before'
        else:
          title = 'after'
        temp2 = []
        for line in temp[start[i]+1:]:
          if len(line.split()) == len(temp[start[i]+1].split()):
            temp2.append(line.split())
          else:
            break
        d[title] = temp2
    out = {'CID': d}
    return(out)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputPhaserNCS**')

def ParseOutputXtriage_NEW(self,inp):
  """
  Parse phenix.xtriage output.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputXtriage')
  import math
  #try:
  temp = []
  junk = []
  anom = {}
  pat_p = []
  pat = {}
  t = False
  twin_info = {}
  summary = []
  pts = False
  twin = False
  pat_st = False
  pat_dist = False
  pat_info = {}
  coset = []
  plots = {}
  #l = [('Intensity','int'),('Z scores','z'),('Anomalous','anom'),
  #     ('<I/sigma_I>','i'),('NZ','nz'),('L test','ltest')]
  l = [('Intensity','int'),('Anomalous','anom'),
       ('NZ','nz'),('L test','ltest')]
  for x,line in enumerate(inp):
    temp.append(line)
    if line.startswith('bin '):
      junk.append(line)
    if line.startswith('$TABLE:'):
      if t == False:
        t = x
      for i in range(len(l)):
        if line.count(l[i][0]):
          plots[l[i][1]] = {'start':x+7}
    if line.startswith('  Multivariate Z score'):
      z_score = line.split()[4]
    if line.count('The full list of Patterson peaks is'):
      pat_st = x
    if line.startswith(' Frac. coord.'):
      pat_x = line.split()[3]
      pat_y = line.split()[4]
      pat_z = line.split()[5]
    if line.startswith(' Distance to origin'):
      pat_dist = line.split()[4]
    """
    if line.startswith(' Height (origin=100)'):
      pat_height = line.split()[3]
    """
    if line.count('Height relative to origin'):
      pat_height = line.split()[-2]
    if line.startswith(' p_value'):
      pat_p = line.split()[-1]
      if float(pat_p)<=0.05:
        pts = True
    """
    if line.startswith('Patterson analyses'):
      index1 = x
    if line.count('---Patterson analyses---'):
      index1 = x
    """
    if line.count('---Final verdict---'):
      sum_s = x
    if line.count('---Statistics independent of twin laws---'):
      sum_e = x

    """
    if line.startswith('Systematic absences'):
      pat_fn = x
    if line.startswith('| Type | Axis   | R metric'):
      twin = True
      twin_st = x
    if line.startswith('M:  Merohedral twin law'):
      twin_fn = x
    if line.startswith('Statistics depending on twin'):
      twin2_st = x
    if line.startswith('  Coset number'):
      coset.append(x)
    """
    if line.count('| Type | Axis   | R metric (%)'):
      twin = True
      twin_st = x
    if line.count('---Statistics depending on twin laws---'):
      twin2_st = x
    if line.startswith('  Coset number'):
      coset.append(x)

  if pat_st:
    i = 1
    for line in temp[pat_st+4:]:
      if line.split()[0] == '|':
        d = {'frac x'    : line.split('|')[1].replace(' ','').split(',')[0],
             'frac y'    : line.split('|')[1].replace(' ','').split(',')[1],
             'frac z'    : line.split('|')[1].replace(' ','').split(',')[2],
             'peak'      : line.split('|')[2].replace(' ',''),
             'p-val'     : line.split('|')[3].replace(' ','')}
        pat[str(i)] = d
        i +=1
      else:
        break
  elif pat_dist:
    d = {'frac x': pat_x,
         'frac y': pat_y,
         'frac z': pat_z,
         'peak'  : pat_height,
         'p-val' : pat_p,
         'dist'  : pat_dist  }
    pat['1'] = d
  print pat
  """
  if pat_dist:
    data2 = {'frac x': pat_x,
             'frac y': pat_y,
             'frac z': pat_z,
             'peak'  : pat_height,
             'p-val' : pat_p,
             'dist'  : pat_dist  }
    pat['1'] = data2

  else:
    skip = False

  if pat_st:
    i = 2
    for line in temp[pat_st+2:pat_fn]:
      split = line.split()
      if line.startswith('('):
        if skip == False:
          x = line[1:7].replace(' ','')
          y = line[8:14].replace(' ','')
          z = line[15:21].replace(' ','')
          pk = line[25:34].replace(' ','')
          p = line[38:-2].replace(' ','')
          data = {'frac x'    : x,
                  'frac y'    : y,
                  'frac z'    : z,
                  'peak'      : pk,
                  'p-val'     : p}
          pat[str(i)] = data
          i +=1
        skip = False

      #NOT SURE IF IN NEW VERSION???
      if line.startswith(' space group'):
        pts = True
        pts_sg = temp.index(line)
        i1 = 1
        for line2 in temp[pts_sg+1:pat_fn]:
          if line2.split() != []:
            a = line2.find('(')
            b = line2.find(')')
            c = line2.rfind('(')
            d = line2.rfind(')')
            sg = line2[:a-1].replace(' ','')+' '+line2[a:b+1].replace(' ','')
            op = line2[b+1:c].replace(' ','')
            ce = line2[c+1:d]
            data2 = {'space group'    : sg,
                     'operator'       : op,
                     'cell'           : ce}
            pat_info[i1] = data2
            i1 +=1
  """
  if twin:
    for line in temp[twin_st+2:] :
      if len(line.split()) == 13:
        law = line.split()[11]
        data = {'type'     : line.split()[1],
                'axis'     : line.split()[3],
                'r_metric' : line.split()[5],
                'd_lepage' : line.split()[7],
                'd_leb'    : line.split()[9]}
        twin_info[law] = data
      else:
        break
    for line in temp[twin2_st+5:t]:
      if len(line.split()) == 13:
        law = line.split()[1]
        data = {'r_obs'      : line.split()[5],
                'britton'    : line.split()[7],
                'h-test'     : line.split()[9],
                'ml'         : line.split()[11]}
        twin_info[law].update(data)
      else:
        break
    if len(coset) > 0:
      for line in coset[1:]:
        sg = temp[line][38:-2]
        try:
          for i in range(2,4):
            if len(temp[line+i].split()) > 0:
              law = temp[line+i].split()[1]
              if twin_info.has_key(law):
                twin_info[law].update({'sg':sg})
        except:
          self.logger.exception('Warning. Missing Coset info.')
    else:
        for key in twin_info.keys():
            twin_info[key].update({'sg':'NA'})

  for line in junk[10:20]:
    if len(line.split()) == 7:
      anom[line.split()[4]] = line.split()[6]
    else:
      anom[line.split()[4]] = '0.0000'
  #Save plots
  for i in range(len(l)):
    temp3 = []
    for line in temp[plots[l[i][1]].get('start'):]:
      if len(temp[plots[l[i][1]].get('start')].split()) == len(line.split()):
        #Convert resolution
        if i < 2:
          temp2 = []
          temp2.append(str(math.sqrt(1/float(line.split()[0]))))
          temp2.extend(line.split()[1:])
          temp3.append(temp2)
        else:
          split = line.split()
          if split[1] == 'nan':
              split[1] = '0.0'
          temp3.append(split)
      else:
        break
    plots[l[i][1]].update({'data':temp3})
  for line in temp[sum_s+3:sum_e-1]:
    summary.append(line)
  xtriage = {'Xtriage anom'         : anom,
             'Xtriage anom plot'    : plots['anom'].get('data'),
             'Xtriage int plot'     : plots['int'].get('data'),
             #'Xtriage i plot'       : plots['i'].get('data'),
             #'Xtriage z plot'       : plots['z'].get('data'),
             'Xtriage nz plot'      : plots['nz'].get('data'),
             'Xtriage l-test plot'  : plots['ltest'].get('data'),
             'Xtriage z-score'      : z_score,
             'Xtriage pat'          : pat,
             'Xtriage pat p-value'  : pat_p,
             'Xtriage summary'      : summary,
             'Xtriage PTS'          : pts,
             'Xtriage PTS info'     : pat_info,
             'Xtriage twin'         : twin,
             'Xtriage twin info'    : twin_info,       }
  return(xtriage)
  """
  except:
    self.logger.exception('**ERROR in Parse.ParseOutputXtriage**')
    return(setXtriageFailed(self))
  """
def ParseOutputXtriage(self,inp):
  """
  Parse phenix.xtriage output.
  """
  if self.verbose:
      self.logger.debug('Parse::ParseOutputXtriage')
  import math
  #try:
  temp = []
  junk = []
  anom = {}
  pat_p = []
  pat = {}
  twin_info = {}
  summary = []
  pts = False
  twin = False
  pat_st = False
  pat_dist = False
  skip = True
  pat_info = {}
  coset = []
  plots = {}
  l = [('Intensity','int'),('Z scores','z'),('Anomalous','anom'),
       ('<I/sigma_I>','i'),('NZ','nz'),('L test','ltest')]
  for x,line in enumerate(inp):
    temp.append(line)
    if line.startswith('bin '):
      junk.append(line)
    """
    if line.startswith('##                    Basic statistics'):
      start = x
    """
    if line.startswith('$TABLE:'):
      for i in range(len(l)):
        if line.count(l[i][0]):
          plots[l[i][1]] = {'start':x+6}
    if line.startswith('  Multivariate Z score'):
      z_score = line.split()[4]
    if line.startswith(' Frac. coord.'):
      pat_x = line.split()[3]
      pat_y = line.split()[4]
      pat_z = line.split()[5]
    if line.startswith(' Distance to origin'):
      pat_dist = line.split()[4]
    if line.startswith(' Height (origin=100)'):
      pat_height = line.split()[3]
    """
    if line.count('Height relative to origin'):
      pat_height = line.split()[5]
    """
    if line.startswith(' p_value(height)'):
      pat_p = line.split()[2]
      if float(pat_p)<=0.05:
        pts = True
    if line.startswith('Patterson analyses'):
      index1 = x
    if line.startswith('The full list of Patterson peaks is:'):
      pat_st = x
    if line.startswith('Systematic absences'):
      pat_fn = x
    if line.startswith('| Type | Axis   | R metric'):
      twin = True
      twin_st = x
    if line.startswith('M:  Merohedral twin law'):
      twin_fn = x
    if line.startswith('Statistics depending on twin'):
      twin2_st = x
    if line.startswith('  Coset number'):
      coset.append(x)
  if pat_dist:
    data2 = {'frac x': pat_x,
             'frac y': pat_y,
             'frac z': pat_z,
             'peak'  : pat_height,
             'p-val' : pat_p,
             'dist'  : pat_dist  }
    pat['1'] = data2
  else:
    skip = False

  if pat_st:
    i = 2
    for line in temp[pat_st+2:pat_fn]:
      split = line.split()
      if line.startswith('('):
        if skip == False:
          x = line[1:7].replace(' ','')
          y = line[8:14].replace(' ','')
          z = line[15:21].replace(' ','')
          pk = line[25:34].replace(' ','')
          p = line[38:-2].replace(' ','')
          data = {'frac x'    : x,
                  'frac y'    : y,
                  'frac z'    : z,
                  'peak'      : pk,
                  'p-val'     : p}
          pat[str(i)] = data
          i +=1
        skip = False
      if line.startswith(' space group'):
        pts = True
        pts_sg = temp.index(line)
        i1 = 1
        for line2 in temp[pts_sg+1:pat_fn]:
          if line2.split() != []:
            a = line2.find('(')
            b = line2.find(')')
            c = line2.rfind('(')
            d = line2.rfind(')')
            sg = line2[:a-1].replace(' ','')+' '+line2[a:b+1].replace(' ','')
            op = line2[b+1:c].replace(' ','')
            ce = line2[c+1:d]
            data2 = {'space group'    : sg,
                     'operator'       : op,
                     'cell'           : ce}
            pat_info[i1] = data2
            i1 +=1
  if twin:
    for line in temp[twin_st+2:twin_fn-1]:
      split = line.split()
      law = split[11]
      data = {'type'     : split[1],
              'axis'     : split[3],
              'r_metric' : split[5],
              'd_lepage' : split[7],
              'd_leb'    : split[9]}
      twin_info[law] = data
    for line in temp[twin2_st+4:index1-2]:
      split = line.split()
      law = split[1]
      data = {'r_obs'      : split[5],
              'britton'    : split[7],
              'h-test'     : split[9],
              'ml'         : split[11]}
      twin_info[law].update(data)
    if len(coset) > 0:
      for line in coset[1:]:
        sg = temp[line][38:-2]
        try:
          for i in range(2,4):
            if len(temp[line+i].split()) > 0:
              law = temp[line+i].split()[1]
              if twin_info.has_key(law):
                twin_info[law].update({'sg':sg})
        except:
          self.logger.exception('Warning. Missing Coset info.')
    else:
      crap = {'sg':'NA'}
      for key in twin_info.keys():
        twin_info[key].update(crap)
  for line in junk[10:20]:
    if len(line.split()) == 7:
      anom[line.split()[4]] = line.split()[6]
    else:
      anom[line.split()[4]] = '0.0000'
  #Save plots
  for i in range(len(l)):
    temp3 = []
    for line in temp[plots[l[i][1]].get('start'):]:
      if len(temp[plots[l[i][1]].get('start')].split()) == len(line.split()):
        #Convert resolution
        if i < 4:
          temp2 = []
          temp2.append(str(math.sqrt(1/float(line.split()[0]))))
          temp2.extend(line.split()[1:])
          temp3.append(temp2)
        else:
          split = line.split()
          if split[1] == 'nan':
            split[1] = '0.0'
          temp3.append(split)
      else:
        break
    plots[l[i][1]].update({'data':temp3})

  for line in temp[index1+5:-3]:
    summary.append(line)
  xtriage = {'Xtriage anom'         : anom,
             'Xtriage anom plot'    : plots['anom'].get('data'),
             'Xtriage int plot'     : plots['int'].get('data'),
             'Xtriage i plot'       : plots['i'].get('data'),
             'Xtriage z plot'       : plots['z'].get('data'),
             'Xtriage nz plot'      : plots['nz'].get('data'),
             'Xtriage l-test plot'  : plots['ltest'].get('data'),
             'Xtriage z-score'      : z_score,
             'Xtriage pat'          : pat,
             'Xtriage pat p-value'  : pat_p,
             'Xtriage summary'      : summary,
             'Xtriage PTS'          : pts,
             'Xtriage PTS info'     : pat_info,
             'Xtriage twin'         : twin,
             'Xtriage twin info'    : twin_info,       }
  return(xtriage)
  """
  except:
      self.logger.exception('**ERROR in Parse.ParseOutputXtriage**')
      return(setXtriageFailed(self))
  """

def ParseOutputMolrep(self,inp):
  """
  Parse Molrep SRF output.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputMolrep')
  try:
    #log_path = os.path.join(os.getcwd(),'molrep.doc')
    #srf_path = os.path.join(os.getcwd(),'molrep_rf.jpg')
    temp = []
    pat = {}
    pts = False
    for line in inp:
      temp.append(line)
      if line.startswith('INFO: pseudo-translation was detected'):
        ind1 = temp.index(line)
        pts = True
      if line.startswith('INFO:  use keyword: "PST"'):
        ind2 = temp.index(line)
    if pts:
      for line in temp[ind1:ind2]:
        split = line.split()
        if split[0] == 'Origin':
          junk = {'peak' : split[-2],
                  'psig' : split[-1]}
          pat['origin'] = junk
        if split[0].isdigit():
          junk1 = {'peak' : split[-2],
                   'psig' : split[-1]}
          pat[split[0]] = junk1
        if split[0] == 'Peak':
          ind3 = temp.index(line)
          pat[split[1][:-1]].update({'frac x' : temp[ind3+1].split()[-3]})
          pat[split[1][:-1]].update({'frac y' : temp[ind3+1].split()[-2]})
          pat[split[1][:-1]].update({'frac z' : temp[ind3+1].split()[-1]})

    molrep  =  {#'Molrep log'    : log_path,
                #'Molrep jpg'    : srf_path,
                'Molrep PTS'    : pts,
                'Molrep PTS_pk' : pat,
                                          }
    return(molrep)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputMolrep**')
    return(setMolrepFailed(self))

def ParseOutputScala(self,inp):
  """
  Parse Scala output.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputScala')
  try:
    temp = []
    sg = False
    index = {}
    ref = []
    r_plot = {}
    i_plot = {}
    c_plot = {}
    ref_plot = {}
    #start = False
    for x,line in enumerate(inp):
      temp.append(line)
      if line.count('$TABLE: Analysis against resolution'):
        index['res_s'] = x
      if line.count('$TABLE: Analysis against intensity'):
        index['i_s'] = x
      if line.count('<a name="cmpltmultScala">'):
        index['i_f'] = x
      if line.count('$TABLE: Completeness, multiplicity,'):
        index['c_s'] = x
      if line.count('Correlation coefficients for anomalous differences'):
        index['c_f'] = x
      if line.count('$TABLE: Axial reflections,'):
        ref.append(x)
      if line.count('<a name="erroranalysisScala">'):
        ref.append(x)
      if line.count('Space group:'):
        sg = line[line.find(':')+1:].replace(' ','')
    #Resolution_plot
    temp1 = []
    i = 1
    for line in temp[index['res_s']:index['i_s']]:
      split = line.strip().split()
      #Fix * issue.
      for x,p in enumerate(split):
        if p.count('*'):
          split[x] = split[x][:split[x].find('*')]
          split.insert(x+1,'0.0')
      if line.strip().startswith(str(i)):
        temp1.append(split)
        if i == 1:
          r_plot['header'] = temp[temp.index(line)-2].split()
        i += 1
      if line.count('Overall:'):
        r_plot['Overall'] = split[1:]
      """
      if line.strip().startswith(str(i)):
        temp1.append(line.split())
        if i == 1:
          r_plot['header'] = temp[temp.index(line)-2].split()
        i += 1
      if line.count('Overall:'):
        if len(line.split()) == 14:
          junk = line.split()
          for x,p in enumerate(junk):
            if p.count('*'):
              junk[x] = junk[x][:junk[x].find('*')]
              junk.insert(x+1,'0.0')
        else:
          r_plot['Overall'] = line.split()[1:]
      """
    r_plot['data'] = temp1
    #Intensity_plot
    i = 0
    temp1 = []
    for line in temp[index['i_s']:index['i_f']]:
      split = line.strip().split()
      #Fix * issue.
      for x,p in enumerate(split):
        if p.count('*'):
          split[x] = split[x][:split[x].find('*')]
          split.insert(x+1,'0.0')
      if line.strip().startswith('$$  $$'):
        i_plot['header'] = temp[temp.index(line)-1].split()
        i = 1
        temp.remove(line)
      if line.count('Overall'):
        #i_plot['Overall'] = line.split()[1:]
        i_plot['Overall'] = split[1:]
        i = 0
      if i:
        #if len(line.split()) == 15:
        if len(split) == len(i_plot['header']):
          temp1.append(split)
        #if len(line.split()) == len(i_plot['header']):
          #temp1.append(line.split())
    i_plot['data'] = temp1
    #Completeness plot
    i = 0
    temp1 = []
    for line in temp[index['c_s']:index['c_f']]:
      split = line.strip().split()
      #Fix * issue.
      for x,p in enumerate(split):
        if p.count('*'):
          split[x] = split[x][:split[x].find('*')]
          split.insert(x+1,'0.0')
      if line.strip().startswith('$$  $$'):
        c_plot['header'] = temp[temp.index(line)-1].split()
        i = 1
        temp.remove(line)
      if line.count('Overall'):
        c_plot['Overall'] = split[1:]
        i = 0
      if i:
        if len(split) == len(c_plot['header']):
          temp1.append(split)
      """
      if line.strip().startswith('$$  $$'):
        c_plot['header'] = temp[temp.index(line)-1].split()
        i = 1
        temp.remove(line)
      if line.count('Overall'):
        c_plot['Overall'] = line.split()[1:]
        i = 0
      if i:
        if len(line.split()) == len(c_plot['header']):
          temp1.append(line.split())
      """
    c_plot['data'] = temp1
    #Reflections plot
    i = 0
    x = len(ref)-1
    while x != 0:
      for line in temp[ref[0]:ref[-1]]:
        if line.count('$$ $$'):
          axis = line.split()[0]
          ref_plot[axis+'_header'] = line.split()[:-2]
          temp1 = []
          i = 1
          x -= 1
        if line.startswith(' $$'):
          ref_plot[axis+'_data'] = temp1
          i = 0
        if i:
          if len(line.split()) == 4:
            temp1.append(line.split())

    results = {'i_plot'  : i_plot,
               'r_plot'  : r_plot,
               'c_plot'  : c_plot,
               'ref_plot': ref_plot,
               'SG'      : sg,
               }
    return(results)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputScala**')
    print '**ERROR in Parse.ParseOutputScala**'

def ParseOutputAimless(self,inp):
  """
  Parse output from Aimless.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputAimless')
  try:
    temp = []
    sg = False
    index = {}
    #ref = []
    r_plot = {}
    i_plot = {}
    c_plot = {}
    #ref_plot = {}
    #start = False
    merge = False
    for x,line in enumerate(inp):
      temp.append(line)
      if line.count('$TABLE:  Analysis against resolution, XDSdataset:'):
        index['res_s'] = x
      if line.count('By 4sinTheta/Lambda^2 bins (statistics with and without anomalous)'):
        index['res_f'] = x
      if line.count('$TABLE:  Analysis against intensity'):
        index['i_s'] = x
      if line.count('Completeness and multiplicity, including reflections measured only once'):
        index['i_f'] = x
      if line.count('Rmeas by resolution for each run'):
        merge = x
      if line.count('$TABLE:  Completeness & multiplicity v. resolution,'):
        index['c_s'] = x
      if line.count('Analysis of standard deviations'):
        index['c_f'] = x
      if line.count('Space group:'):
        sg = line[line.find(':')+1:].replace(' ','')
    if merge:
      index['i_f'] = merge
    #Resolution_plot
    temp1 = []
    i = 1
    for line in temp[index['res_s']:index['res_f']]:
      split = line.strip().split()
      #Fix * issue.
      for x,p in enumerate(split):
        if p.count('*'):
          split[x] = split[x][:split[x].find('*')]
          split.insert(x+1,'0.0')
      if line.strip().startswith(str(i)):
        temp1.append(split)
        i += 1
      if line.count('Overall:'):
        r_plot['Overall'] = split[1:]
        r_plot['header'] = temp[temp.index(line)+1].split()
    r_plot['data'] = temp1
    #Intensity_plot
    i = 0
    temp1 = []
    for line in temp[index['i_s']:index['i_f']]:
      split = line.strip().split()
      #Fix * issue.
      for x,p in enumerate(split):
        if p.count('*'):
          split[x] = split[x][:split[x].find('*')]
          split.insert(x+1,'0.0')
      if line.strip().startswith('$$'):
        i = 1
      if line.count('Overall'):
        i_plot['Overall'] = split[1:]
        i_plot['header'] = temp[temp.index(line)+2].split()
        i = 0
      if i:
        if len(split) == 12:
          temp1.append(split)
    i_plot['data'] = temp1
    #Completeness plot
    i = 1
    temp1 = []
    for line in temp[index['c_s']:index['c_f']]:
      split = line.strip().split()
      #Fix * issue.
      for x,p in enumerate(split):
        if p.count('*'):
          split[x] = split[x][:split[x].find('*')]
          split.insert(x+1,'0.0')
      if line.strip().startswith(str(i)):
        temp1.append(split)
        i += 1
      if line.count('Overall:'):
        c_plot['Overall'] = split[1:]
        c_plot['header'] = temp[temp.index(line)+1].split()
    c_plot['data'] = temp1

    results = {'i_plot'  : i_plot,
               'r_plot'  : r_plot,
               'c_plot'  : c_plot,
               #'ref_plot': ref_plot,
               'SG'      : sg,
               }
    return(results)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputScala**')
    print '**ERROR in Parse.ParseOutputScala**'

def ParseOutputGxparm(self,inp,l=False):
  """
  Parse out sym in GXPARM.XDS.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputGxparm')
  #try:
  for line in inp:
    if len(line.split()) == 7:
      if l:
        out = line.split()
      else:
        out = line.split()[0]
  return(out)

def ParseOutputCorrect(self,inp,short=True):
  """
  Parse out sym in CORRECT.LP or XSCALE.LP.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputCorrect')
  try:
    if short:
      #Just see if refinement converged.
      counter = 0
      num = False
      for line in inp:
        if line.count('E.S.D. OF CELL PARAMETERS'):
          num = line.split()[4:7]
      if num:
        for line in num:
          term = str(float(line))
          if term.count('0.05'):
            counter += 1
        if len(num) == counter:
          return(False)
        else:
          return(True)
      else:
        return(False)
    else:
      qual = {}
      temp = []
      isa = False
      for x,line in enumerate(inp):
        if line.count('a        b          ISa'):
          isa = inp[x+1].split()[-1]
        if line.count('SUBSET OF INTENSITY DATA WITH SIGNAL/NOISE >= -3.0'):
          st = x
        if line.count('NUMBER OF REFLECTIONS IN SELECTED SUBSET OF IMAGES'):
          fi = x
        if line.count('STATISTICS OF INPUT DATA SET'):
          fi = x
      for line in inp[st+4:fi-2]:
        if line.count('total'):
          qual['Overall'] = line.strip().split()[1:]
        else:
          temp.append(line.strip().split())
      qual['data'] = temp
      results = {'Quality': qual}
      if isa:
        results['ISa'] = isa
      return(results)

  except:
    self.logger.exception('**ERROR in Parse.ParseOutputCorrect**')

def ParseOutputDialsSpot(self,inp):
  """
  Parse dials.find_spots results.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputDialsSpot')
  #try:
  tot_spots = 0
  fil_spots = 0
  for line in inp:
    if line.count('spot intensities'):
      tot_spots += int(line.split()[1])
    if line.count('reflections to strong.pickle'):
      fil_spots += int(line.split()[1])

  d = {'total spots': tot_spots,
       'filtered spots' : fil_spots,
       'log' : inp,
       }
  return(d)

def ParseOutputDialsIndex(self,inp):
  """
  Parse dials.index results.
  """
  if self.verbose:
      self.logger.debug('Parse::ParseOutputDialsIndex')
  #try:
  failed = False
  max_cell = '0'
  res_lim = '0'
  cen = '0'
  cell = False
  sg = '0'
  ref = '0'
  rmsdx = '0'
  rmsdy = '0'
  rmsdz = '0'

  for line in inp:
    if line.count('Sorry:'):
      failed = True
    if line.count('Found max_cell'):
      max_cell = line.split()[2]
    if line.count('Setting d_min'):
      res_lim = line.split()[2]
    if line.count('centroids used'):
      cen = line.split()[4]
    #Just grab the last round results
    if line.count('Unit cell:'):
      cell = line[line.find('(')+1:-2].split(', ')
    if line.count('Space group:'):
      sg = line[line.find(':')+1:].rstrip().replace(' ','')
    if line.count('model 1 '):
      ref = line.split()[2][1:]
    if line.startswith('| 0   |'):
      rmsdx = line.split()[5]
      rmsdy = line.split()[7]
      rmsdz = line.split()[9]

  d = {'log'       : inp,
       'max_cell'  : max_cell,
       'res_limit' : res_lim,
       'centroids' : cen,
       'unit_cell' : cell,
       'space_group': sg,
       'reflections': ref,
       'rmsd_x'     : rmsdx,
       'rmsd_y'     : rmsdy,
       'rmsd_z'     : rmsdz,
       'failed'     : failed,
       }

  return(d)

def ParseOutputDialsRefine(self,log,bravais=False):
  """
  Parse dials.refine_bravais_settings results.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputDialsRefine')
  #try:
  #import decimal
  #decimal.getcontext().prec = 3
  #print decimal.getcontext()
  if bravais:
    sol = bravais
    failed = False
  else:
    sol = {}
    failed = True
  ust = '0'
  ticks = '0'
  tt = '0'
  wt = '0'
  l = []
  l1 = []
  e = False

  for x,line in enumerate(log):
    if line.count('Sorry:'):
      failed = True
    #if line.count('Experimental models after refinement'):
    #   l.append(x)
    if line.count('A = UB:'):
      l1.append(x)
    if line.startswith('usr+sys'):
      ust = line.split()[2]
      ticks = line.split()[5]
      tt = line.split()[7]
    if line.startswith('wall clock'):
      wt = line.split()[3]
  """
  if failed == False:
    #Grab the model results after refinement. Log not in order.
    while e == False:
      for x in range(len(l1)):
        for i in l:
          if 0 < l1[x] - i < 50:
              e = l1[x] - i + 3
        #In case there is a problem...
        if x == l1[-1]:
          e = 40
    for x in range(len(l)):
      cell = False
      for line in log[l[x]:l[x]+e]:
        if line.count('Unit cell:'):
          cell = line[line.find('(')+1:line.find(')')].split(', ')
      if cell:
        for run in sol.keys():
          l1 = []
          for i in sol[run].get('unit_cell'):
            l1.append(str(round(i,3)).zfill(3))
            #l1.append(str(decimal.Decimal.from_float(i)))
            #l1.append(str(decimal.Decimal(i,3)))
          print l1

  """

  d = {'log'          : log,
       'failed'       : failed,
       'sol'          : sol,
       'sys time'     : ust,
       'ticks'        : ticks,
       'time per tick': tt,
       'wall time'    : wt,
       }
  return(d)

def ParseOutputDialsRefine_OLD(self,log,bravais=False):
  """
  Parse dials.refine_bravais_settings results.
  """
  if self.verbose:
    self.logger.debug('Parse::ParseOutputDialsRefine')
  #try:
  if bravais:
    sol = bravais
  else:
    sol = {}
  ust = '0'
  ticks = '0'
  tt = '0'
  wt = '0'
  failed = False

  for line in log:
    if line.count('Sorry:'):
      failed = True
    if line.startswith('usr+sys'):
      ust = line.split()[2]
      ticks = line.split()[5]
      tt = line.split()[7]
    if line.startswith('wall clock'):
      wt = line.split()[3]

  d = {'log'          : log,
       'failed'       : failed,
       'sol'          : sol,
       'sys time'     : ust,
       'ticks'        : ticks,
       'time per tick': tt,
       'wall time'    : wt,
       }
  return(d)

def ParseOutputXOalign(self,log):
  if self.verbose:
    self.logger.debug('Parse::ParseOutputXOalign')
  #try:
  conv = {'[1 1 0]':'ab', '[1 0 1]': 'ac', '[0 1 1]': 'bc', '[1 0 0]': 'a*', '[0 1 0]': 'b*', '[0 0 1]': 'c*'}
  alignment = []
  st = []
  sol = {}
  for x,line in enumerate(log):
    if line.count('Solutions for Datum positions:'):
      #alignment.append(line[line.find(':')+1:-1].strip(' ').split(',  '))
      a = line[line.find(':')+1:-1].strip(' ').split(',  ')
      if conv.keys().count(a[0]):
        a1 = []
        for axis in a:
          a1.append(conv[axis])
        alignment.append(a1)
      else:
        alignment.append(a)
      st.append(x+3)
  for x in range(len(st)):
    l = []
    for line in log[st[x]:]:
      if line.count('*** No solutions found ***'):
        l.append('No solutions found')
      elif len(line.split()) == 4:
        l.append(line.split())
      else:
        break
    sol[float(x)] = {'solution': l, 'V1': alignment[x][0],'V2': alignment[x][1]}
  return(sol)

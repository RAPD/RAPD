"""
Routines for creating summaries fro user interfaces of some core agents
"""

__licenses__ = """
This file is part of RAPD

Copyright (C) 2011-2016, Cornell University
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
__created__ = "2011-04-19"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

# Standard imports
import os

# RAPD imports
import utils.xutils as Utils
# import rapd_utils as Utils

def summaryLabelit(self):
  """
  Print Labelit results to screen and create variable with results for the summary_short and summary_long php files.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryLabelit')
  try:
    labelit_face      = self.labelit_results.get('Labelit results').get('labelit_face')
    labelit_solution  = self.labelit_results.get('Labelit results').get('labelit_solution')
    labelit_metric    = self.labelit_results.get('Labelit results').get('labelit_metric')
    labelit_rmsd      = self.labelit_results.get('Labelit results').get('labelit_rmsd')
    labelit_spots_fit = self.labelit_results.get('Labelit results').get('labelit_spots_fit')
    labelit_system    = self.labelit_results.get('Labelit results').get('labelit_system')
    labelit_cell      = self.labelit_results.get('Labelit results').get('labelit_cell')
    labelit_volume    = self.labelit_results.get('Labelit results').get('labelit_volume')
    mosflm_face       = self.labelit_results.get('Labelit results').get('mosflm_face')
    mosflm_solution   = self.labelit_results.get('Labelit results').get('mosflm_solution')
    mosflm_sg         = self.labelit_results.get('Labelit results').get('mosflm_sg')
    mosflm_beam_x     = self.labelit_results.get('Labelit results').get('mosflm_beam_x')
    mosflm_beam_y     = self.labelit_results.get('Labelit results').get('mosflm_beam_y')
    mosflm_distance   = self.labelit_results.get('Labelit results').get('mosflm_distance')
    mosflm_res        = self.labelit_results.get('Labelit results').get('mosflm_res')
    mosflm_mos        = self.labelit_results.get('Labelit results').get('mosflm_mos')
    mosflm_rms        = self.labelit_results.get('Labelit results').get('mosflm_rms')
    #output            = self.labelit_results.get('Labelit results').get('output')
    #mosaicity      = str(self.labelit_results.get('Labelit results').get('mosaicity'))

    l = [('Mosflm Integration Results','mosflm',
          ['&nbsp','Solution','Spacegroup','Beam X','Beam Y','Distance','Resolution','Mosaicity','RMS'],
          [mosflm_face,mosflm_solution,mosflm_sg,mosflm_beam_x,mosflm_beam_y,
           mosflm_distance,mosflm_res,mosflm_mos,mosflm_rms]),

         ('Labelit Results','labelit',
          ['&nbsp','Solution','Metric','RMSD','# of Spots','Crystal System',
           'a','b','c','&alpha;','&beta;','&gamma;','Volume'],
          [labelit_face,labelit_solution,labelit_metric,labelit_rmsd,
           labelit_spots_fit,labelit_system,labelit_cell,labelit_volume])]

    labelit = ''
    #Run for Mosflm and Labelit results.
    for z in range(2):
      labelit +='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
      labelit +='%6s<h1 class="results">%s</h1>\n'%('',l[z][0])
      labelit +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="%s">\n'%('',l[z][1])
      labelit +='%9s<thead align="center">\n%11s<tr>\n'%('','')
      for p in l[z][2]:
        labelit +='%13s<th>%s</th>\n'%('',p)
      labelit +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
      for x in range(len(l[z][3][1])):
        labelit +='%11s<tr class="gradeA">\n'%''
        for p in l[z][3]:
          if p == labelit_system:
            labelit +="%13s<td>%s %s</td>\n" % ('',p[x][0],p[x][1])
          elif p == labelit_cell:
            for y in range(len(p[x])):
              labelit +="%13s<td>%s</td>\n" % ('',p[x][y])
          else:
            labelit +="%13s<td>%s</td>\n" % ('',p[x])
        labelit +="%11s</tr>\n"%''
      labelit +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
    self.labelit_summary = labelit

  except:
    self.logger.exception('**ERROR in Summary.summaryLabelit.**')

def summaryDistl(self):
  """
  Print Distl summary to screen and create variable for input into summary_long.php.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryDistl')

  try:
    total_spots      = self.distl_results.get('Distl results').get('total spots')
    spots_in_res     = self.distl_results.get('Distl results').get('spots in res')
    good_spots       = self.distl_results.get('Distl results').get('good Bragg spots')
    distl_res        = self.distl_results.get('Distl results').get('distl res')
    labelit_res      = self.distl_results.get('Distl results').get('labelit res')
    max_cell         = self.distl_results.get('Distl results').get('max cell')
    ice_rings        = self.distl_results.get('Distl results').get('ice rings')
    overloads        = self.distl_results.get('Distl results').get('overloads')
    min1             = self.distl_results.get('Distl results').get('min signal strength')
    max1             = self.distl_results.get('Distl results').get('max signal strength')
    mean1            = self.distl_results.get('Distl results').get('mean int signal')

    #Create distl variable for summary_long.php
    distl  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    distl +='%6s<h1 class="results">Peak Picking Results</h1>\n'%''
    distl +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="distl">\n'%''
    distl +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    l = ['Total Spots','Spots in Res','Good Bragg Spots','Overloaded Spots','Distl Res','Labelit Res',
         'Max Cell','Ice Rings','Min Signal Strength','Max Signal Strength','Mean Int Signal']
    for p in l:
      distl +='%13s<th>%s</th>\n'%('',p)
    distl +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
    l = [total_spots,spots_in_res,good_spots,overloads,distl_res,
         labelit_res,max_cell,ice_rings,min1,max1,mean1]
    for x in range(len(total_spots)):
      distl +='%11s<tr class="gradeA">\n'%''
      for p in l:
        distl +="%13s<td>%s</td>\n" % ('',p[x])
      distl +="%11s</tr>\n"%''
    distl +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
    self.distl_summary = distl

  except:
    self.logger.exception('**ERROR in Summary.summaryDistl**')

def summaryRaddose(self):
  """
  print RADDOSE results to screen and create variable for php file.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryRaddose')
  try:
    hen_lim       = self.raddose_results.get("raddose_results").get('henderson limit')
    dose          = self.raddose_results.get("raddose_results").get('dose per image')
    exp_dose_lim  = self.raddose_results.get("raddose_results").get('exp dose limit')

    raddose  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    raddose +='%6s<h1 class="results">Raddose Results</h1>\n'%''
    raddose +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="raddose">\n'%''
    raddose +='%9s<thead>\n%11s<tr>\n'%('','')
    raddose +=('%13s<th></th>\n'%'')*11
    """
    for i in range(11):
      raddose +='%13s<th></th>\n'%''
    """
    raddose +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
    l = [('Dose (G/s)',dose),('Time (S) to reach Henderson limit (20 MGy)',hen_lim),
         ('Time (S) to reach experimental dose limit (30 MGy)',exp_dose_lim)]
    for p in l:
      raddose +='%11s<tr>\n%13s<th>%s</th>\n'%('','',p[0])
      raddose +="%13s<td>%s</td>\n%11s</tr>\n" % ('',p[1],'')
    raddose +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
    self.raddose_summary = raddose

  except:
    self.logger.exception('**ERROR in Summary.summaryRaddose.**')

def summaryBest(self,anom=False):
  """
  print BEST results to screen and creates variable for php file.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryBest')
  try:
    if anom:
      j  = 'self.best_anom_results'
      j1 = 'Best ANOM results'
      j2 = ' anom '
    else:
      j  = 'self.best_results'
      j1 = 'Best results'
      j2 = ' '
    run_number      = eval("%s.get('%s').get('strategy%srun number')" % (j,j1,j2))
    phi_start       = eval("%s.get('%s').get('strategy%sphi start')" % (j,j1,j2))
    num_images      = eval("%s.get('%s').get('strategy%snum of images')" % (j,j1,j2))
    delta_phi       = eval("%s.get('%s').get('strategy%sdelta phi')" % (j,j1,j2))
    time            = eval("%s.get('%s').get('strategy%simage exp time')" % (j,j1,j2))
    distance        = eval("%s.get('%s').get('strategy%sdistance')" % (j,j1,j2))
    phi_end         = eval("%s.get('%s').get('strategy%sphi end')" % (j,j1,j2))
    res             = eval("%s.get('%s').get('strategy%sres limit')" % (j,j1,j2))
    completeness    = eval("%s.get('%s').get('strategy%scompleteness')" % (j,j1,j2))
    redundancy      = eval("%s.get('%s').get('strategy%sredundancy')" % (j,j1,j2))
    rot_range       = eval("%s.get('%s').get('strategy%srot range')" % (j,j1,j2))
    r_factor        = eval("%s.get('%s').get('strategy%sR-factor')" % (j,j1,j2))
    i_sig           = eval("%s.get('%s').get('strategy%sI/sig')" % (j,j1,j2))
    tot_time        = eval("%s.get('%s').get('strategy%stotal exposure time')" % (j,j1,j2))
    data_col_time   = eval("%s.get('%s').get('strategy%sdata collection time')" % (j,j1,j2))
    blind           = eval("%s.get('%s').get('strategy%sfrac of unique in blind region')" % (j,j1,j2))
    #attenuation     = float(eval("%s.get('%s').get('strategy%sattenuation')" % (j,j1,j2)))
    best_trans      = eval("%s.get('%s').get('strategy%snew transmission')" % (j,j1,j2))
    #best_trans = Utils.calcTransmission(self,attenuation)
    if self.sample_type != 'Ribosome':
      if self.high_dose:
        if float(max(time)) > 3.0:
          time = len(time)*['3.0',]
      if self.iso_B:
        if float(max(time)) > 2.0:
          time = len(time)*['1.0',]

    if self.verbose:
      if anom:
        print '\n\tOptimal Plan of ANOMALOUS data collection'
      else:
        print '\n\t\tOptimal Plan of data collection'
      print '\t\t================================'
      print '\tResolution limit is set by the radiation damage\n'
      print '-----------------------------------------------------------------------------------'
      print ' N |  Omega_start |  N.of.images | Rot.width |  Exposure | Distance | % Transmission |'
      print '-----------------------------------------------------------------------------------'
      for x in range(len(run_number)):
        print '%2s | %8s   | %7s      |%9s  | %9s | %7s  |     %3s      |' \
          % (run_number[x],phi_start[x],num_images[x],delta_phi[x],
             time[x],distance[x],best_trans[x])
  except:
    self.logger.exception('**summaryBest. Could not display Best results to screen.**')
  #Create Best variable for php files.
  try:
    best ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    if anom:
      best +='%7s<h1 class="results">ANOMALOUS data collection strategy from BEST</h1>\n'%''
    else:
      best +='%7s<h1 class="results">Data collection strategy from BEST</h1>\n'%''
    if self.high_dose:
      best +='%7s<h4 class="results">Dosage is too high! Crystal will last for %s images. '\
              'Strategy calculated from realistic dosage.</h4>\n'%('',self.crystal_life)
    if anom:
      line = '%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="bestanom">\n'%''
      best += line
      best0 = line
      best1 ='%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="bestanom1">\n'%''
    else:
      line = '%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="best">\n'%''
      best += line
      best0 = line
      best1 ='%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="best1">\n'%''
    best +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    l = ['N','Omega Start','Omega End','Rot Range','N of Images',
         'Delta Omega','Exposure time','Distance','% Transmission']
    for p in l:
      best +='%13s<th>%s</th>\n'%('',p)
    best +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
    for x in range(len(run_number)):
      ss = int(num_images[x])*(float(delta_phi[x]))
      se = float(phi_start[x])+ss
      if se > 360:
        se -= 360
      if anom:
        best +='%11s<tr class="gradeD">\n'%''
      else:
        best +='%11s<tr class="gradeC">\n'%''
      l = [run_number[x],phi_start[x],se,ss,num_images[x],delta_phi[x],time[x],distance[x],best_trans[x]]
      for i in xrange(len(l)):
        if i in (1,2,3):
          best +="%13s<td><b>%s</b></td>\n" % ('',l[i])
        else:
          best +="%13s<td>%s</td>\n" % ('',l[i])
      best +="%11s</tr>\n"%''
    best +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
    if anom:
      self.best_anom_summary = best
      self.best1_anom_summary = best.replace(best0,best1)
    else:
      self.best_summary = best
      self.best1_summary = best.replace(best0,best1)
    best_long ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    """
    best_long +="%7s<h2 class='results'>Image: %s</h2>\n" % ('',self.header.get('fullname'))
    if self.header2:
      best_long +="%7s<h2 class='results'>Image: %s</h2>\n" % ('',self.header2.get('fullname'))
    """
    if anom:
      best_long +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="bestanomdata">\n'%''
    else:
      best_long +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="bestdata">\n'%''
    best_long +='%9s<thead>\n%11s<tr>\n'%('','')
    for i in range(5):
      best_long +='%13s<th></th>\n'%''
    best_long +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
    l = [('Resolution Limit','%s Angstroms'%res),('Anomalous data',anom),
         ('Omega_start - Omega_finish','%s-%s'%(phi_start[0],phi_end)),
         ('Total rotation range','%s Degrees'%rot_range),
         ('Total N.of images',sum(int(i) for i in num_images)),
         ('Overall Completeness',completeness),('Redundancy',redundancy),
         ('R-factor (outer shell)',r_factor),('I/Sigma (outer shell)',i_sig),
         ('Total Exposure time','%s sec'%tot_time),
         ('Total Data Collection time','%s sec'%data_col_time),
         ('Frac of unique ref in blind region',blind)]
    for p in l:
      best_long +='%11s<tr>\n%13s<th>%s</th>\n'%('','',p[0])
      best_long +='%13s<td>%s</td>\n%11s</tr>\n'%('',p[1],'')
    best_long +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
    if anom:
      self.best_anom_summary_long = best_long
    else:
      self.best_summary_long = best_long

  except:
    self.logger.exception('**Summary.summaryBest. Could not create Best html variable.**')

def summaryMosflm(self, anom=False):
    """
    Create html files Mosflm strategy.

    Keyword argument
    anom -- (default False)
    """

    if self.verbose:
        self.logger.debug('Summary::summaryMosflm')

    try:
        if anom:
            j  = 'self.mosflm_strat_anom_results'
            j1 = 'Mosflm ANOM strategy results'
            j2 = ' anom '
        else:
            j  = 'self.mosflm_strat_results'
            j1 = 'Mosflm strategy results'
            j2 = ' '
        run_number = eval("%s.get('%s').get('strategy%srun number')" % (j, j1, j2))
        phi_start = eval("%s.get('%s').get('strategy%sphi start')" % (j, j1, j2))
        phi_end = eval("%s.get('%s').get('strategy%sphi end')" % (j, j1, j2))
        num_images = eval("%s.get('%s').get('strategy%snum of images')" % (j, j1, j2))
        res = eval("%s.get('%s').get('strategy%sresolution')" % (j, j1, j2))
        completeness = eval("%s.get('%s').get('strategy%scompleteness')" % (j, j1, j2))
        redundancy = eval("%s.get('%s').get('strategy%sredundancy')" % (j, j1, j2))
        distance = eval("%s.get('%s').get('strategy%sdistance')" % (j, j1, j2))
        time = eval("%s.get('%s').get('strategy%simage exp time')" % (j, j1, j2))
        delta_phi = eval("%s.get('%s').get('strategy%sdelta phi')" % (j, j1, j2))
        mosflm_trans = Utils.calcTransmission(self)
        if self.verbose:
            if anom:
                print '\n\n\t\tOptimal Plan of ANOMALOUS data collection according to Mosflm'
            else:
                print '\n\n\t\tOptimal Plan of data collection according to Mosflm'
            print '\t\t================================\n'
            print '-----------------------------------------------------------------------------------'
            print ' N |  Omega_start |  N.of.images | Rot.width |  Exposure | Distance | % Transmission |'
            print '-----------------------------------------------------------------------------------'
            for x in range(len(run_number)):
                print '%2s | %8s   | %7s      |%9s  | %9s | %7s  |     %3.0f      |' \
                    % (run_number[x], phi_start[x], num_images[x], delta_phi, time, distance, mosflm_trans)
    except:
        self.logger.exception('**summaryMosflm_strat Could not print Mosflm strategy to screen.**')

    # Create Mosflm variable for php files.
    try:
        mosflm ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%('','','')
        if anom:
          mosflm +='%7s<h1 class="results">ANOMALOUS data collection strategy from Mosflm</h1>\n'%''
        else:
          mosflm +='%7s<h1 class="results">Data collection strategy from Mosflm</h1>\n'%''
        if self.high_dose:
          mosflm +='%7s<h4 class="results">Dosage is too high! Crystal will last for %s images. '\
                    'Strategy calculated from realistic dosage.</h4>\n'%('',self.crystal_life)
        if self.multicrystalstrat:
          for line in self.preferences.get('reference_data'):
            mosflm +='%7s<h2 class="results">Data collected from %s taken into account for strategy.</h2>\n'%('',line[3])
        if anom:
          line    ='%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="stratanom">\n'%''
          mosflm += line
          mosflm0 = line
          mosflm1 = '%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="stratanom1">\n'%''
        else:
          line    ='%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="strat">\n'%''
          mosflm += line
          mosflm0 = line
          mosflm1 = '%7s<table cellpadding="0" cellspacing="0" border="10" class="display" id="strat1">\n'%''
        mosflm +='%9s<thead align="center">\n%11s<tr>\n'%('','')
        l = ['N','Omega Start','Omega End','Rot Range','N of Images',
             'Delta Omega','Exposure time','Distance','% Transmission']
        for p in l:
          mosflm +='%13s<th>%s</th>\n'%('',p)
        mosflm +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
        tot_sweep = []
        for x in range(len(run_number)):
            ss = int(num_images[x])*(float(delta_phi))
            se = float(phi_start[x])+ss
            if se > 360:
                se -= 360
            tot_sweep.append(ss)
            if anom:
                mosflm +='%11s<tr class="gradeD">\n'%''
            else:
                mosflm +='%11s<tr class="gradeC">\n'%''
            if self.high_dose:
                time = '1.00'
            l = [run_number[x], phi_start[x], se, ss, num_images[x],
                 delta_phi, time, distance, mosflm_trans]
            for p in l:
                mosflm +="%13s<td>%s</td>\n" % ('',p)
            mosflm +="%11s</tr>\n"%''
        mosflm +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
        if anom:
            self.mosflm_strat_anom_summary = mosflm
            self.mosflm_strat1_anom_summary = mosflm.replace(mosflm0,mosflm1)
        else:
            self.mosflm_strat_summary = mosflm
            self.mosflm_strat1_summary = mosflm.replace(mosflm0,mosflm1)
        mosflm_long ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
        mosflm_long +="%7s<h2 class='results'>Image: %s</h2>\n" % ('',self.header.get('fullname'))
        if self.header2:
            mosflm_long +="%7s<h2 class='results'>Image: %s</h2>\n" % ('',self.header2.get('fullname'))
        if anom:
            mosflm_long +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="mosflmanomdata">\n'%''
        else:
            mosflm_long +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="mosflmdata">\n'%''
        mosflm_long +='%9s<thead>\n%11s<tr>\n'%('','')
        for i in range(5):
            mosflm_long +='%13s<th></th>\n'%''
        mosflm_long +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
        l = [('Resolution Limit','%s Angstroms'%res),('Anomalous data',anom),
             ('Omega_start - Omega_finish','%s-%s'%(phi_start[0],phi_end[-1])),
             ('Total rotation range','%s Degrees'%sum(tot_sweep)),
             ('Total N.of images',sum(int(i) for i in num_images)),
             ('Overall Completeness',completeness),('Redundancy',redundancy)]
        for p in l:
            mosflm_long +='%11s<tr>\n%13s<th>%s</th>\n'%('','',p[0])
            mosflm_long +='%13s<td>%s</td>\n%11s</tr>\n'%('',p[1],'')
        mosflm_long +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
        if anom:
            self.mosflm_strat_anom_summary_long = mosflm_long
        else:
            self.mosflm_strat_summary_long = mosflm_long
    except:
        self.logger.exception('**Summary.summaryMosflm Could not Mosflm strategy html.**')

def summaryShelx(self):
  """
  Print out SHELX CDE results to logger and create html/php variables.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryShelx')
  try:
    shelxc_res       = self.shelx_results.get('Shelx results').get('shelxc_res')
    shelxc_data      = self.shelx_results.get('Shelx results').get('shelxc_data')
    shelxc_isig      = self.shelx_results.get('Shelx results').get('shelxc_isig')
    shelxc_comp      = self.shelx_results.get('Shelx results').get('shelxc_comp')
    shelxc_dsig      = self.shelx_results.get('Shelx results').get('shelxc_dsig')
    shelxc_chi       = self.shelx_results.get('Shelx results').get('shelxc_chi-sq')
    shelxc_cc        = self.shelx_results.get('Shelx results').get('shelxc_cchalf')
    shelx_data       = self.shelx_results.get('Shelx results').get('shelx_data')
    mad_cc           = self.shelx_results.get('Shelx results').get('MAD_CC')
    shelxe_cc        = self.shelx_results.get('Shelx results').get('shelxe_cc')
    shelxe_sites     = self.shelx_results.get('Shelx results').get('shelxe_sites')
    shelxe_nosol     = self.shelx_results.get('Shelx results').get('shelxe_nosol')
    shelxe_fom       = self.shelx_results.get('Shelx results').get('shelxe_fom')
    shelxe_trace_cc  = self.shelx_results.get('Shelx results').get('shelxe_trace_cc')
    shelxe_nres      = self.shelx_results.get('Shelx results').get('shelxe_trace_nres')
    #Check if additional params are present from unmerged input.
    if not len(shelxc_chi) > 0:
      shelxc_chi = False
    #SHELXC
    shelxc  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    shelxc +='%7s<h1 class="results">SHELXC Results</h1>\n'%''
    if float(self.resolution) != 0.0:
      shelxc +='%7s<h4 class="results">User set SAD high resolution cutoff to %s Angstroms. '\
               '(Table will still show all resolution bins)</h4>\n'%('',self.resolution)
    fi = len(shelx_data)
    if len(mad_cc) > 0:
      fi += 1
    for z in range(fi):
      shelxc +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxc%s">\n'%('',z)
      #Create table of CC's for MAD data.
      if z == len(shelx_data):
        shelxc +='%9s<h2 class="results">Correlation coefficients between signed '\
                 'anomalous differences</h2>\n%9s<thead align="left">\n'%('','')
      else:
        shelxc +='%9s<h2 class="results">%s</h2>\n%9s<thead align="left">\n'%('',shelx_data[z],'')
      shelxc +='%11s<tr></tr>\n%11s<tr>\n%13s<th>Resolution</th>\n'%(3*('',))
      for x in range(len(shelxc_res[z])):
        shelxc +='%13s<th>%s</th>\n'%('',shelxc_res[z][x])
        """
        #Have to include a single data line or Tables do not load properly?? (OLD)
        if x == len(shelxc_res[z]) - 1:
          shelxc +='%13s<td>%s</td>\n'%('',shelxc_res[z][x])
        else:
          shelxc +='%13s<th>%s</th>\n'%('',shelxc_res[z][x])
        """
      shelxc +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
      if z == len(shelx_data):
        for x in range(len(mad_cc)):
          shelxc +='%11s<tr class="gradeA">\n'%''
          for y in range(len(mad_cc[x])):
            if y == 0:
              #shelxc +='%13s<th>%s</th>\n'%('',mad_cc[x][y])
              if x%2 == 0:
                shelxc +='%13s<td class="Name0">%s</td>\n'%('',mad_cc[x][y])
              else:
                shelxc +='%13s<td class="Name1">%s</td>\n'%('',mad_cc[x][y])
            else:
              shelxc +='%13s<td>%s</td>\n'%('',mad_cc[x][y])
          shelxc +="%11s</tr>\n"%''
      else:
        if shelxc_chi:
          l = [(shelxc_data[z],'N(data)'),(shelxc_chi[z],'Chi<sup>2</sup>'),
               (shelxc_isig[z],'&ltI/sig&gt'),(shelxc_comp[z],'% Complete'),
               (shelxc_dsig[z],'&ltd"/sig&gt'),(shelxc_cc[z],'CC(1/2)')]
        else:
          l = [(shelxc_data[z],'N(data)'),(shelxc_isig[z],'&ltI/sig&gt'),
               (shelxc_comp[z],'% Complete'),(shelxc_dsig[z],'&ltd"/sig&gt')]
        for i in range(len(l)):
          #shelxc +='%11s<tr class="gradeA">\n%13s<th>%s</th>\n'%('','',l[i][1])
          if i%2 == 0:
            shelxc +='%11s<tr class="gradeA">\n%13s<td class="Name0">%s</td>\n'%('','',l[i][1])
          else:
            shelxc +='%11s<tr class="gradeA">\n%13s<td class="Name1">%s</td>\n'%('','',l[i][1])
          #shelxc +='%11s<tr class="gradeA">\n%13s<td class="name">%s</td>\n'%('','',l[i][1])
          for x in range(len(l[i][0])):
            shelxc +="%13s<td>%s</td>\n" % ('',l[i][0][x])
          shelxc +='%11s</tr>\n'%''
      shelxc +='%9s</tbody>\n%7s</table>\n'%('','')
    shelxc +="%6s</div>\n%5s</div>\n%4s</div>\n" % (3*('',))
    """
    if len(mad_cc) > 0:
      z += 1
      shelxc +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxc'+str(z)+'">\n'
      shelxc +='        <h2 class="results">Correlation coefficients (%) between signed anomalous differences</h2>\n'
      shelxc +='          <thead align="left">\n'
      shelxc +='            <tr>\n'
      shelxc +='            </tr>\n'
      shelxc +='            <tr>\n'
      shelxc +='              <th>Resolution</th>\n'
      for x in range(0,10):
        shelxc +='              <th>'+shelxc_res[z][x]+'</th>\n'
      shelxc +='              <td>'+shelxc_res[z][10]+'</td>\n'
      shelxc +='            </tr>\n'
      shelxc +='          </thead>\n'
      shelxc +='          <tbody align="left">\n'
      for x in range(len(mad_cc)):
        shelxc +='            <tr class="gradeA">\n'
        for y in range(len(mad_cc[x])):
          if y == 0:
            shelxc +='              <th>'+mad_cc[x][y]+'</th>\n'
          else:
            shelxc +="              <td>"+mad_cc[x][y]+"</td>\n"
        shelxc +="            </tr>\n"
      shelxc +='          </tbody>\n'
      shelxc +="        </table>\n"
    shelxc +="       </div>\n"
    shelxc +="      </div>\n"
    shelxc +="     </div>\n"
    """
    self.shelxc_summary = shelxc
    #SHELXD
    shelxd  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    shelxd +='%7s<h1 class="results">SHELXD Results</h1>\n'%''
    shelxd +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxd">\n'%''
    shelxd +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    l = ['Space Group','Max CCall','Max CCweak','Max CFOM','Max PATFOM']
    for p in l:
      shelxd +='%13s<th>%s</th>\n'%('',p)
    shelxd +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
    for line in self.shelxd_dict.keys():
      inv_sg = Utils.convertSG(self,Utils.checkInverse(self,Utils.convertSG(self,line))[0],True)
      if self.shelx_nosol == False:
        if self.shelx_sg in (line,inv_sg):
          shelxd +='%11s<tr class="gradeDD">\n'%''
        else:
          shelxd +='%11s<tr class="gradeA">\n'%''
      else:
        shelxd +='%11s<tr class="gradeA">\n'%''
      if line == inv_sg:
        shelxd +="%13s<td>%s</td>\n" % ('',line)
      else:
        shelxd +="%13s<td>%s (%s)</td>\n" % ('',line,inv_sg)
      l = [self.shelxd_dict[line].get('cc'),self.shelxd_dict[line].get('ccw'),
           self.shelxd_dict[line].get('cfom'),self.shelxd_dict[line].get('fom')]
      for p in l:
        shelxd +="%13s<td>%s</td>\n" % ('',p)
      shelxd +='%11s</tr>\n'%''
    shelxd +="%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n" % (5*('',))
    self.shelxd_summary = shelxd
    #SHELXE
    shelxe  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    shelxe +='%7s<h1 class="results">SHELXE Results</h1>\n'%''
    if self.shelx_nosol:
      shelxe +='%7s<h4 class="results">SHELXE did NOT find a reliable solution, however here are the best results (%s)</h4>\n'%('',self.shelx_sg)
    else:
      shelxe +='%7s<h4 class="results">SHELXE may have found a solution in %s with a solvent fraction of %s</h4>\n'%('',self.shelx_sg,self.solvent_content)
      if shelxe_nosol == 'True':
        shelxe +='%7s<h4 class="results">SHELXE could not determine the "hand" reliably.</h4>\n'%''
    shelxe +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxe">\n'%''
    shelxe +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    l = ['Site','x','y','z','occ*Z','density']
    for p in l:
      shelxe +='%13s<th>%s</th>\n'%('',p)
    shelxe +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
    for line in shelxe_sites:
      shelxe +='%11s<tr class="gradeA">\n'%''
      for i in range(len(line.split())):
        shelxe +="%13s<td>%s</td>\n" % ('',line.split()[i])
      shelxe +="%11s</tr>\n"%''
    shelxe +='%9s</tbody>\n%7s</table>\n'%('','')
    shelxe +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxe2">\n'%''
    shelxe +='%9s<tbody align="left">\n%9s<br>\n'%('','')
    l = [('SHELXE FOM',shelxe_fom),('SHELXE Pseudo-free CC (>60 is good)',shelxe_cc)]
    if self.shelx_build:
      l.extend([('SHELXE autotraced # of residues',shelxe_nres),
                ('SHELXE autotraced CC (>25 is good)',shelxe_trace_cc)])
    for i in range(len(l)):
      shelxe +='%11s<tr>\n%13s<th>%s</th>\n%13s<td>%s</td>\n%11s</tr>\n'%('','',l[i][0],'',l[i][1],'')
    shelxe +='%9s</tbody>\n%7s</table>\n'%('','')
    if self.autosol_build:
      if self.shelx_nosol == False:
        if self.pp:
          if self.autosol_failed:
            shelxe +='%7s<h4 class="results">Phenix AutoSol FAILED.</h4>\n'%''
          else:
            shelxe +='%7s<h3 class="results">Phenix AutoSol completed successfully.</h3>\n'%''
        else:
          shelxe +='%7s<h4 class="results">Phasing and autobuilding will now be attempted in Phenix AutoSol.</h4>\n'%''
    shelxe +="%6s</div>\n%5s</div>\n%4s</div>\n" % (3*('',))
    self.shelxe_summary = shelxe

  except:
    self.logger.exception('**ERROR in Summary.summaryShelx**')

def summaryAutoSol(self,autobuild=False):
  """
  Create html variables.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryAutoSol')
  try:
    #dir1       = self.autosol_results.get('AutoSol results').get('directory')
    sg        = self.autosol_results.get('AutoSol results').get('sg')
    bayescc   = self.autosol_results.get('AutoSol results').get('bayes-cc')
    fom       = self.autosol_results.get('AutoSol results').get('fom')
    sites_st  = self.autosol_results.get('AutoSol results').get('sites_start')
    sites_ref = self.autosol_results.get('AutoSol results').get('sites_refined')
    res       = self.autosol_results.get('AutoSol results').get('res_built')
    side      = self.autosol_results.get('AutoSol results').get('side_built')
    chains    = self.autosol_results.get('AutoSol results').get('num_chains')
    mmcc      = self.autosol_results.get('AutoSol results').get('model-map_cc')
    r         = self.autosol_results.get('AutoSol results').get('r/rfree')
    #Only run if map is input and not implemented yet.
    if autobuild:
      res    = self.autobuild_results.get('AutoBuild results').get('AutoBuild_built')
      placed = self.autobuild_results.get('AutoBuild results').get('AutoBuild_placed')
      chains = self.autobuild_results.get('AutoBuild results').get('AutoBuild_chains')
      mmcc   = self.autobuild_results.get('AutoBuild results').get('AutoBuild_mmcc')
      rfree  = self.autobuild_results.get('AutoBuild results').get('AutoBuild_rfree')
      rfac   = self.autobuild_results.get('AutoBuild results').get('AutoBuild_rfac')
      score  = self.autobuild_results.get('AutoBuild results').get('AutoBuild_score')
      #self.pdb  = self.autobuild_results.get('AutoBuild results').get('AutoBuild_pdb')
      #self.mtz  = self.autobuild_results.get('AutoBuild results').get('AutoBuild_mtz')
      r = rfac+' / '+rfree

    autosol ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    if autobuild:
      autosol +='%7s<h1 class="results">Phenix AutoBuild Results</h1>\n'%''
    else:
      autosol +='%7s<h1 class="results">Phenix AutoSol Results</h1>\n'%''
    autosol +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="autosol">\n'%''
    autosol +='%9s<thead align="left">\n%11s<tr>\n%13s<th colspan="2">Statistics</th>\n'%(3*('',))
    autosol +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
    l = [('Space Group',sg),('Bayesian CC',bayescc),('FOM',fom),('Number of starting sites',sites_st),
        ('Number of refined sites',sites_ref),('Number of residues built',res),('Number of side-chains built',side),
        ('Total number of chains',chains),('model-map CC',mmcc),('Refined R/R-free',r)]
    if self.autobuild:
      l.extend([('Number of sequenced residues built',placed),('Build Score',score)])
    for i in range(len(l)):
      autosol +='%11s<tr class="gradeA">\n%13s<th>%s</th>\n%13s<td>%s</td>\n%11s</tr>\n'%('','',l[i][0],'',l[i][1],'')
    autosol +="%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n" % (5*('',))
    """
    autosol +='    <div id="container">\n'
    autosol +='     <div class="full_width big">\n'
    autosol +='      <div id="demo">\n'
    autosol +="      <h1 class='Results'>Output PDB file</h1>\n"
    autosol +='       <div id="Jmol_mainWrapper">\n'
    autosol +='        <div style="margin:auto;width:550px;height:550px;border:solid 1px lightgray;padding: 0.5em;" id="jmol_box">\n'
    autosol +="         <script>\n"
    autosol +='            jmolInitialize("js/jmol-12.1.13",true);\n'
    autosol +='            jmolApplet(["100%","100%"],\n'
    autosol +='                        "load '+pdb+';select all; spacefill off; wireframe off; backbone off; cartoon on;color cartoon structure;set antialiasDisplay true;");\n'
    autosol +="         </script>\n"
    autosol +="        </div>\n"
    autosol +="        <h2 class='Results'>Tip: right-mouse click on Jmol to get access to additional Jmol functionality.</h2>\n"
    autosol +="       </div>\n"
    autosol +="      </div>\n"
    autosol +="     </div>\n"
    autosol +="    </div>\n"
    """
    if autobuild:
      self.autobuild_summary = autosol
    else:
      self.autosol_summary = autosol

  except:
    self.logger.exception('**ERROR in Summary.summaryAutoSol**')

def summaryXtriage(self):
  """
  Create the summary info from Xtriage for html file.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryXtriage')
  try:
    #xtriage_anom       = self.xtriage_results.get('Xtriage results').get('Xtriage anom')
    xtriage_pat        = self.xtriage_results.get('Xtriage results').get('Xtriage pat')
    xtriage_sum        = self.xtriage_results.get('Xtriage results').get('Xtriage summary')
    xtriage_pts        = self.xtriage_results.get('Xtriage results').get('Xtriage PTS')
    xtriage_pts_info   = self.xtriage_results.get('Xtriage results').get('Xtriage PTS info')
    xtriage_twin       = self.xtriage_results.get('Xtriage results').get('Xtriage twin')
    xtriage_twin_info  = self.xtriage_results.get('Xtriage results').get('Xtriage twin info')
    if xtriage_sum != 'None':
      xtriage  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
      xtriage +='%7s<h1 class="results">Unit Cell Info</h1>\n'%''
      xtriage +='%7s<table cellpadding="0" cellspacing="0" border="1" class="display" id="xtriage-auto2">\n'%''
      xtriage +='%9s<thead align="center">\n%11s<tr>\n'%('','')
      l = ['Space Group','a','b','c','&alpha;','&beta;','&gamma;']
      for p in l:
        xtriage +='%13s<th>%s</th>\n'%('',p)
      xtriage +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n%11s<tr class="gradeA">\n'%(4*('',))
      xtriage +="%13s<td>%s</td>\n" % ('',self.input_sg)
      for i in range(len(self.cell2)):
        xtriage +="%13s<td>%s</td>\n" % ('',self.cell2[i])
      xtriage +="%11s</tr>\n%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n" % (6*('',))
      xtriage +='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
      xtriage +='%7s<h1 class="results">Patterson Analysis</h1>\n'%''
      if xtriage_pts:
        self.pts = True
        xtriage +='%7s<h4 class="results">WARNING! Pseudo-translation is detected.</h4>\n'%''
      xtriage +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="xtriage_pat">\n'%''
      xtriage +='%9s<thead align="left">\n%11s<tr>\n'%('','')
      l = ['Off-origin Peak','Height (Percent compared to origin)','X','Y','Z']
      for p in l:
        xtriage +='%13s<th>%s</th>\n'%('',p)
      xtriage +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
      peaks = xtriage_pat.keys()
      peaks.sort()
      for i in range(len(peaks)):
        if xtriage_pts:
          xtriage +='%11s<tr class="gradeD">\n'%''
        else:
          xtriage +='%11s<tr class="gradeA">\n'%''
        l = [peaks[i],xtriage_pat[peaks[i]].get('peak'),xtriage_pat[peaks[i]].get('frac x'),
             xtriage_pat[peaks[i]].get('frac y'),xtriage_pat[peaks[i]].get('frac z')]
        for p in l:
          xtriage +='%13s<td>%s</td>\n'%('',p)
        xtriage +='%11s</tr>\n'%''
      xtriage +="%9s</tbody>\n%7s</table>\n" % ('','')
      if len(xtriage_pts_info.keys()) != 0:
        xtriage +='%7s<h4 class="results">If the observed pseudo-translationals are crystallographic, then the following info is possible.</h4>\n'%''
        xtriage +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="xtriage_pts">\n'%''
        xtriage +='%9s<thead align="left">\n%11s<tr>\n'%('','')
        l = ['Space Group','Operator','Unit Cell']
        for p in l:
          xtriage +='%13s<th>%s</th>\n'%('',p)
        xtriage +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
        for key in xtriage_pts_info.keys():
          xtriage +='%11s<tr class="gradeD">\n'%''
          l = [xtriage_pts_info[key].get('space group'),xtriage_pts_info[key].get('operator'),xtriage_pts_info[key].get('cell')]
          for p in l:
            xtriage +='%13s<td>%s</td>\n'%('',p)
          xtriage +='%11s</tr>\n'%''
        xtriage +="%9s</tbody>\n%7s</table>\n" % ('','')
      xtriage +="%6s</div>\n%5s</div>\n%4s</div>\n" % (3*('',))
      if xtriage_twin:
        self.twin = True
        xtriage +='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
        xtriage +='%7s<h1 class="results">Twinning Analysis</h1>\n'%''
        xtriage +='%7s<h2 class="results">Carefully inspect the table and plots to determine if twinning may be present.</h2>\n'%''
        xtriage +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="xtriage_twin">\n'%''
        xtriage +='%9s<thead align="left">\n%11s<tr>\n'%('','')
        l = ['Operator','Type','Axis','Apparent SG','R obs','Britton alpha','H-test alpha','ML alpha']
        for p in l:
          xtriage +='%13s<th>%s</th>\n'%('',p)
        xtriage +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
        for law in xtriage_twin_info.keys():
          l = [law,xtriage_twin_info[law].get('type'),xtriage_twin_info[law].get('axis'),xtriage_twin_info[law].get('sg'),
               xtriage_twin_info[law].get('r_obs'),xtriage_twin_info[law].get('britton'),xtriage_twin_info[law].get('h-test'),
               xtriage_twin_info[law].get('ml')]
          xtriage +='%11s<tr class="gradeA">\n'%''
          for p in l:
            xtriage +='%13s<td>%s</td>\n'%('',p)
          xtriage +='%11s</tr>\n'%''
        xtriage +="%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n" % (5*('',))
      if xtriage_sum:
        xtriage +='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
        xtriage +='%7s<h1 class="results">Xtriage Summary</h1>\n%7s<P class="t">\n'%('','')
        for line in xtriage_sum:
          xtriage +='%9s%s\n'%('',line)
        xtriage +='%7s</P>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(4*('',))
      self.xtriage_summary = xtriage

  except:
    self.logger.exception('**ERROR in Summary.summaryXtraige**')
      #Utils.failedHTML(self,'jon_summary_xtriage')

def summaryMolrep(self):
  """
  Prepare images nd tables for html output.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryMolrep')
  try:
    molrep_pk  = self.molrep_results.get('Molrep results').get('Molrep PTS_pk')
    molrep  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    molrep +="%7s<h1 class='Results'>Molrep Self-Rotation Function</h1>\n"%''
    if self.gui:
      molrep +="%7s<div id='molrep_jpg' style='text-align:center'></div>\n"%''
    else:
      molrep +='%7s<IMG SRC="%s">\n'%('',self.molrep_results.get('Molrep results').get('Molrep jpg'))
    if self.molrep_results.get('Molrep results').get('Molrep PTS'):
      molrep +='%7s<h4 class="results">WARNING pseudotranslation is detected</h4>\n'%''
      molrep +='%7s<table cellpadding="2" cellspacing="2" border="0" class="display" id="molrep">\n'%''
      molrep +='%9s<thead align="left">\n%11s<tr>\n'%('','')
      l = ['Peak','Height','Height/sig','% of origin peak','X','Y','Z']
      for p in l:
        molrep +='%13s<th>%s</th>\n'%('',p)
      molrep +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n%11s<tr class="gradeA">\n'%(4*('',))
      l = ['Origin',molrep_pk['origin'].get('peak'),molrep_pk['origin'].get('psig'),'100','0','0','0']
      for p in l:
        molrep +='%13s<td>%s</td>\n'%('',p)
      molrep +='%11s</tr>\n'%''
      peaks = molrep_pk.keys()
      peaks.remove('origin')
      peaks.sort()
      for x in range(len(peaks)):
        molrep +='%11s<tr class="gradeA">\n'%''
        l = [peaks[x],molrep_pk[peaks[x]].get('peak'),molrep_pk[peaks[x]].get('psig'),
             str(round(float(molrep_pk[peaks[x]].get('peak'))/float(molrep_pk['origin'].get('peak'))*100)),
             molrep_pk[peaks[x]].get('frac x'),molrep_pk[peaks[x]].get('frac y'),molrep_pk[peaks[x]].get('frac z')]
        for p in l:
          molrep +='%13s<td>%s</td>\n'%('',p)
        molrep +='%11s</tr>\n'%''
      molrep +="%9s</tbody>\n%7s</table>\n" % ('','')
    molrep +="%6s</div>\n%5s</div>\n%4s</div>\n" % (3*('',))
    self.molrep_summary = molrep

  except:
    self.logger.exception('**ERROR in Summary.summaryMolrep**')
    Utils.failedHTML(self,'jon_summary_molrep')

def summaryCell(self,inp='phaser'):
  """
  Summary of unit cell analysis.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryCell')

  sol = []
  n = 7
  l2 = []
  ckeys = []
  nkeys = []
  percent = False
  results = False
  if inp == 'phaser':
    title = 'phaser-cell'
    title2 = 'phaser-pdb'
    n += 1
  elif inp == 'pdbquery':
    title = 'pdbquery-cell'
    title2 = 'pdbquery-pdb'
    if self.search_common:
      l2 = self.common
  else:
    #Not SURE if this is ACTIVE!
    title = 'sad-cell'
    title2 = 'sad-pdb'

  def sortResults():
    #Sort results by pass or fail and if present in self.common
    for i in range(2):
      f = []
      p = []
      for k in self.phaser_results.keys():
        if i == 0:
          for r in l2:
            if k.count(r):
              if self.phaser_results[k]['AutoMR results']['AutoMR gain'] in ('No solution','Timed out','NA','DL Failed'):
                f.append(k)
              else:
                p.append(k)
          f.sort()
          p.sort()
          ckeys = p+f
        else:
          if k not in ckeys:
            if self.phaser_results[k]['AutoMR results']['AutoMR gain'] in ('No solution','Timed out','NA','DL Failed'):
              f.append(k)
            else:
              p.append(k)
          f.sort()
          p.sort()
          nkeys = p+f
    return((ckeys,nkeys))

  def tD(inp1):
    if inp1%2 == 0:
      return('Name1')
    else:
      return('Name0')

  def gen(inp2):
    j = 0
    temp = ''
    best = False
    #Find the solution with the highest LLG.
    _l = []
    for i in range(2):
      for run in inp2:
        llg = self.phaser_results[run].get('AutoMR results').get('AutoMR gain')
        if llg not in ('No solution','Timed out','NA','DL Failed','Still running'):
          if i == 0:
            _l.append(int(llg))
          else:
            if int(llg) == _l[0]:
              best = run
      if i == 0:
        _l.sort()
        _l.reverse()
    com1 = ''
    for line in inp2:
      skip = False
      llg   = self.phaser_results[line].get('AutoMR results').get('AutoMR gain')
      if inp == 'phaser':
        l = [self.phaser_results[line].get('AutoMR results').get('AutoMR nmol')]
      else:
        l = []
      l.extend([llg,self.phaser_results[line].get('AutoMR results').get('AutoMR rfz'),
         self.phaser_results[line].get('AutoMR results').get('AutoMR tfz'),
         self.phaser_results[line].get('AutoMR results').get('AutoMR clash')])
      if llg in ('No solution','Timed out','NA','DL Failed'):
        l.append('')
        com1 +='%11s<tr class="gradeAA">\n'%''
      elif llg == 'Still running':
        l.append('')
        com1 +='%11s<tr class="gradeH">\n'%''
      else:
        sol.append(line)
        l.append('<button id="mr:%s">Download</button>'%line)
        if inp == 'pdbquery':
          c1 = 'DD'
        else:
          c1 = 'D'
        if best:
          if best == line:
            c1 = 'F'
        com1 +='%11s<tr class="grade%s">\n'%('',c1)
      #com1 +='%13s<td>%s</td>\n'%('',line)
      if inp == 'phaser':
        #If more than 1 SM in SG.
        if multi:
          if line.split('_')[0] == temp:
            com1 +='%13s<td class="%s">&nbsp</td>\n'%('',tD(j))
          else:
            temp = line.split('_')[0]
            j+=1
            com1 +='%13s<td class="%s">%s</td>\n'%('',tD(j),line.split('_')[0])
          if line == keys[-1]:
            #If last then make line.
            skip = True
          else:
            if temp != keys[keys.index(line)+1].split('_')[0]:
              #If the next SG is different, make a line.
              skip = True
        else:
          j+=1
          com1 +='%13s<td class="%s">%s</td>\n'%('',tD(j),line.split('_')[0])
        if line.split('_')[1] == 'all':
          tag = '(all chains)'
        else:
          tag = '(chain: %s)'%line.split('_')[1]
        if self.pdb_name:
          com1 +='%13s<td>%s %s</td>\n'%('',self.pdb_name,tag)
        elif self.pdb_code:
          com1 +='%13s<td>%s %s</td>\n'%('',os.path.basename(self.input_pdb),tag)
        else:
          com1 +='%13s<td>%s</td>\n'%('',tag)
      else:
        com1 +='%13s<td class="small">%s</td>\n'%('',line)
        #Only grabbing the first description to make table simpler.
        com1 +='%13s<td class="small">%s</td>\n'%('',self.phaser_results[line].get('Name','No Name')[:50])
      for p in l:
        com1 +='%13s<td class="small">%s</td>\n'%('',p)
      com1 +="%11s</tr>\n"%''
      if skip:
        #p = 7+n
        com1 +="%11s<tr class='gradeE'>\n%13s%s\n%11s</tr>\n" % ('','',n*'<td>','')
    com1 +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
    return(com1)

  try:
    cell  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    if inp == 'phaser':
      cell +='%7s<h1 class="results">Phaser Results</h1>\n'%''
    else:
      cell +='%7s<h1 class="results">Unit Cell Analysis</h1>\n'%''
      #sort results
      ckeys,nkeys = sortResults()
    cell +='%7s<table cellpadding="0" cellspacing="0" border="1" class="display" id="%s">\n'%('',title)
    cell +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    l = ['a','b','c','&alpha;','&beta;','&gamma;']
    for p in l:
      cell +='%13s<th>%s</th>\n'%('',p)
    cell +='%11s</tr>\n%9s<tbody align="center">\n%11s<tr class="gradeA">\n'%(3*('',))
    for i in range(len(self.cell2)):
      cell +="%13s<td>%s</td>\n" % ('',self.cell2[i])
    cell +="%11s</tr>\n%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n" % (6*('',))
    if len(l2) > 0:
      #Write the results for the common contaminating proteins.
      cell += '%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
      cell += '%7s<h1 class="results">MR results for common contaminating proteins</h1>\n'%''
      cell +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="pdbquery-cc">\n'%''
      cell +='%9s<thead align="left">\n%11s<tr>\n'%('','')
      cell +="%13s<th colspan='%s'></th>\n%13s<th colspan='4' align='center'>Phaser Statistics</th>\n%11s</tr>\n%11s<tr>\n" % ('',n-5,'','','')
      l = ['PDB ID','Description','LL-Gain','RF Z-score','TF Z-score','# of Clashes','&nbsp']
      for p in l:
        cell +='%13s<th>%s</th>\n'%('',p)
      cell +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
      cell += gen(ckeys)
      """
      f = []
      p = []
      for k in self.phaser_results.keys():
        for r in l2:
          if k.count(r):
            if self.phaser_results[k]['AutoMR results']['AutoMR gain'] in ('No solution','Timed out','NA','DL Failed'):
              f.append(k)
            else:
              p.append(k)
          else:
            #Set results to show PDB results other than in self.common
            results = True
      f.sort()
      p.sort()
      ckeys = p+f
      print ckeys
      cell += (gen(ckeys))
      """
    self.cell_summary = cell

    if self.percent:
      percent = str(self.percent*100)
    opdb  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    #Get keys from pdbs that actually ran thru Phaser
    if self.phaser_results.keys() == ['None']:
      opdb +='%7s<h4 class="results">There are no structures in the PDB with similar unit cell dimensions</h4>\n'%''
    else:
      if inp == 'pdbquery':
        #if results == True:
        if len(nkeys) > 0:
          opdb +='%7s<h4 class="results">Structures with unit cell dimensions within +/- %s %%</h4>\n'%('',percent)
        else:
          opdb +='%7s<h4 class="results">There are no structures deposited in the PDB with unit cell dimensions within +- %s %%</h4>\n'%('',percent)
      else:
        tncs = False
        for sg in self.phaser_results.keys():
          if self.phaser_results[sg].get('AutoMR results').get('AutoMR tNCS'):
            tncs = True
        if tncs:
          opdb +='%7s<h4 class="results">Phaser detected tNCS and has corrected for it.</h4>\n'%''
      opdb +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="%s">\n'%('',title2)
      opdb +='%9s<thead align="left">\n%11s<tr>\n'%('','')
      #opdb +="%13s<th colspan='%s'></th>\n%13s<th colspan='4' align='center'>Phaser Statistics</th>\n%11s</tr>\n%11s<tr>\n" % ('',2+n,'','','')
      opdb +="%13s<th colspan='%s'></th>\n%13s<th colspan='4' align='center'>Phaser Statistics</th>\n%11s</tr>\n%11s<tr>\n" % ('',n-5,'','','')
      if inp == 'phaser':
        l = ['Space Group','Search model','N placed']
      else:
        l = ['PDB ID','Description']
      l.extend(['LL-Gain','RF Z-score','TF Z-score','# of Clashes','&nbsp'])
      for p in l:
        opdb +='%13s<th>%s</th>\n'%('',p)
      opdb +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
      #For cell analysis
      keys = self.phaser_results.keys()
      if inp == 'phaser':
        keys = self.phaser_jobs
        keys.sort()
        multi = False
        for s in keys:
          if s.split('_')[1] != 'all':
            multi = True
        opdb += gen(keys)
      elif inp == 'pdbquery':
        opdb += gen(nkeys)
        """
        f = []
        p = []
        for r in keys:
          run = True
          if l2:
            #Only get PDB's not in self.common
            if r in ckeys:
              run = False
          if run:
            if self.phaser_results[r]['AutoMR results']['AutoMR gain'] in ('No solution','Timed out','NA','DL Failed'):
              f.append(r)
            else:
              p.append(r)
        f.sort()
        p.sort()
        keys = p+f
      opdb += gen(keys)
      """
      if len(sol) != 0:
        tooltips  = "%8s//Tooltips\n%8s$('#pdb tbody td').each(function(){\n" % ('','')
        for i in range(len(sol)):
          if i == 0:
            tooltips += "%11sif ($(this).text() == '%s') {\n" % ('',sol[i])
          else:
            tooltips += "%11selse if ($(this).text() == '%s') {\n" % ('',sol[i])
          tooltips += "%14sthis.setAttribute('title','%s');\n%11s}\n" % ('',os.path.join(self.working_dir,sol[i]+'.tar.bz2'),'')
        tooltips += '%8s});\n'%''
        self.tooltips = tooltips
    self.pdb_summary = opdb

  except:
    self.logger.exception('**ERROR in Summary.summaryCell**')

def summaryCell_OLD(self,inp='phaser'):
  """
  Summary of unit cell analysis.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryCell')

  j = 0

  def tD(inp1):
    if inp1%2 == 0:
      return('Name1')
    else:
      return('Name0')

  try:
    sol = []
    n = 7
    l1 = []
    temp = ''
    percent = False
    best = False
    if inp == 'phaser':
      title = 'phaser-cell'
      title2 = 'phaser-pdb'
      l2 = False
      n += 1
    elif inp == 'pdbquery':
      title = 'pdbquery-cell'
      title2 = 'pdbquery-pdb'
    else:
      #Not SURE if this is ACTIVE!
      title = 'sad-cell'
      title2 = 'sad-pdb'
    cell  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
    if inp == 'phaser':
      cell +='%7s<h1 class="results">Phaser Results</h1>\n'%''
    else:
      cell +='%7s<h1 class="results">Unit Cell Analysis</h1>\n'%''
    cell +='%7s<table cellpadding="0" cellspacing="0" border="1" class="display" id="%s">\n'%('',title)
    cell +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    l = ['a','b','c','&alpha;','&beta;','&gamma;']
    for p in l:
      cell +='%13s<th>%s</th>\n'%('',p)
    cell +='%11s</tr>\n%9s<tbody align="center">\n%11s<tr class="gradeA">\n'%(3*('',))
    for i in range(len(self.cell2)):
      cell +="%13s<td>%s</td>\n" % ('',self.cell2[i])
    cell +="%11s</tr>\n%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n" % (6*('',))
    self.cell_summary = cell
    if self.percent:
      percent = str(self.percent*100)
    #Get keys from pdbs that actually ran thru Phaser
    if self.phaser_results.keys() != ['None']:
      opdb  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
      if inp != 'phaser':
        if percent:
          opdb +='%7s<h4 class="results">Structures with unit cell dimensions within +/- %s %%</h4>\n'%('',percent)
        elif inp == 'pdbquery':
          opdb +='%7s<h4 class="results">Could not download similar PDB files because their server did not respond...</h4>\n'%''
        #SAD?
        else:
          opdb +='%7s<h4 class="results">Structures with similar unit cell dimensions</h4>\n'%''
      else:
        tncs = False
        for sg in self.phaser_results.keys():
          if self.phaser_results[sg].get('AutoMR results').get('AutoMR tNCS'):
            tncs = True
        if tncs:
          opdb +='%7s<h4 class="results">Phaser detected tNCS and has corrected for it.</h4>\n'%''
      opdb +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="%s">\n'%('',title2)
      opdb +='%9s<thead align="left">\n%11s<tr>\n'%('','')
      #opdb +="%13s<th colspan='%s'></th>\n%13s<th colspan='4' align='center'>Phaser Statistics</th>\n%11s</tr>\n%11s<tr>\n" % ('',2+n,'','','')
      opdb +="%13s<th colspan='%s'></th>\n%13s<th colspan='4' align='center'>Phaser Statistics</th>\n%11s</tr>\n%11s<tr>\n" % ('',n-5,'','','')
      if inp == 'phaser':
        l = ['Space Group','Search model','N placed']
      else:
        l = ['PDB ID','Description']
      l.extend(['LL-Gain','RF Z-score','TF Z-score','# of Clashes','&nbsp'])
      for p in l:
        opdb +='%13s<th>%s</th>\n'%('',p)
      opdb +='%11s</tr>\n%9s</thead>\n%9s<tbody align="left">\n'%(3*('',))
      #For cell analysis
      keys = self.phaser_results.keys()
      if inp == 'phaser':
        keys = self.phaser_jobs
        keys.sort()
        multi = False
        for s in keys:
          if s.split('_')[1] != 'all':
            multi = True
      elif inp == 'pdbquery':
        f = []
        p = []
        for r in self.phaser_results.keys():
          if self.phaser_results[r]['AutoMR results']['AutoMR gain'] in ('No solution','Timed out','NA','DL Failed'):
            f.append(r)
          else:
            p.append(r)
        f.sort()
        p.sort()
        keys = p+f
      #Find the solution with the highest LLG.
      for i in range(2):
        for run in keys:
          llg = self.phaser_results[run].get('AutoMR results').get('AutoMR gain')
          if llg not in ('No solution','Timed out','NA','DL Failed','Still running'):
            if i == 0:
              l1.append(int(llg))
            else:
              if int(llg) == l1[0]:
                best = run
        if i == 0:
          l1.sort()
          l1.reverse()
      for line in keys:
        skip = False
        llg   = self.phaser_results[line].get('AutoMR results').get('AutoMR gain')
        if inp == 'phaser':
          l = [self.phaser_results[line].get('AutoMR results').get('AutoMR nmol')]
        else:
          l = []
        l.extend([llg,self.phaser_results[line].get('AutoMR results').get('AutoMR rfz'),
           self.phaser_results[line].get('AutoMR results').get('AutoMR tfz'),
           self.phaser_results[line].get('AutoMR results').get('AutoMR clash')])
        if llg in ('No solution','Timed out','NA','DL Failed'):
          l.append('')
          opdb +='%11s<tr class="gradeAA">\n'%''
        elif llg == 'Still running':
          l.append('')
          opdb +='%11s<tr class="gradeH">\n'%''
        else:
          sol.append(line)
          l.append('<button id="mr:%s">Download</button>'%line)
          if inp == 'pdbquery':
            c1 = 'DD'
          else:
            c1 = 'D'
          if best:
            if best == line:
              c1 = 'F'
          opdb +='%11s<tr class="grade%s">\n'%('',c1)
        #opdb +='%13s<td>%s</td>\n'%('',line)
        if inp == 'phaser':
          #If more than 1 SM in SG.
          if multi:
            if line.split('_')[0] == temp:
              opdb +='%13s<td class="%s">&nbsp</td>\n'%('',tD(j))
            else:
              temp = line.split('_')[0]
              j+=1
              opdb +='%13s<td class="%s">%s</td>\n'%('',tD(j),line.split('_')[0])
            if line == keys[-1]:
              #If last then make line.
              skip = True
            else:
              if temp != keys[keys.index(line)+1].split('_')[0]:
                #If the next SG is different, make a line.
                skip = True
          else:
            j+=1
            opdb +='%13s<td class="%s">%s</td>\n'%('',tD(j),line.split('_')[0])
          if line.split('_')[1] == 'all':
            tag = 'all chains'
          else:
            tag = 'chain: %s'%line.split('_')[1]
          if self.pdb_name:
            opdb +='%13s<td>%s %s</td>\n'%('',self.pdb_name,tag)
          elif self.pdb_code:
            opdb +='%13s<td>%s %s</td>\n'%('',os.path.basename(self.input_pdb),tag)
          else:
            opdb +='%13s<td>%s</td>\n'%('',tag)
        else:
          opdb +='%13s<td>%s</td>\n'%('',line)
          #Only grabbing the first description to make table simpler.
          opdb +='%13s<td>%s</td>\n'%('',self.phaser_results[line].get('Name','No Name')[:50])
          """
          if line.count('_'):
            opdb +='%13s<td>%s</td>\n'%('',self.cell_output[line[:line.rfind('_')]].get('Name','No Name')[:50])
          else:
            opdb +='%13s<td>%s</td>\n'%('',self.cell_output[line].get('Name','No Name')[:50])
          """
        for p in l:
          opdb +='%13s<td>%s</td>\n'%('',p)
        opdb +="%11s</tr>\n"%''
        if skip:
          #p = 7+n
          opdb +="%11s<tr class='gradeE'>\n%13s%s\n%11s</tr>\n" % ('','',n*'<td>','')
      opdb +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
      if len(sol) != 0:
        tooltips  = "%8s//Tooltips\n%8s$('#pdb tbody td').each(function(){\n" % ('','')
        for i in range(len(sol)):
          if i == 0:
            tooltips += "%11sif ($(this).text() == '%s') {\n" % ('',sol[i])
          else:
            tooltips += "%11selse if ($(this).text() == '%s') {\n" % ('',sol[i])
          tooltips += "%14sthis.setAttribute('title','%s');\n%11s}\n" % ('',os.path.join(self.working_dir,sol[i]+'.tar.bz2'),'')
        tooltips += '%8s});\n'%''
        self.tooltips = tooltips
    else:
      opdb  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
      if percent:
        opdb +='%7s<h4 class="results">There are no structures deposited in the PDB with unit cell dimensions within +- %s %%</h4>\n'%('',percent)
      else:
        opdb +='%7s<h4 class="results">There are no structures in the PDB with similar unit cell dimensions</h4>\n'%''
      opdb +='%6s</div>\n%5s</div>\n%4s</div>\n'%(3*('',))
    self.pdb_summary = opdb

  except:
    self.logger.exception('**ERROR in Summary.summaryCell**')

def summaryAutoCell(self,labelit=False):
  """
  show unit cell info in output html file.
  """
  if self.verbose:
    self.logger.debug('Summary::summaryAutoCell')
  try:
    #Grab unit cell results and creates variable for displaying in summary_short.php.
    cell,symmetry = Utils.getLabelitCell(self,'all')
    l1 = ['Space Group','a','b','c','&alpha;','&beta;','&gamma;']
    l2 = [symmetry,cell]
    if labelit:
      """
      #Not as good res limit
      if self.best_results.get('Best results') != 'FAILED':
        mosflm_res = self.best_results.get('Best results').get('strategy res limit')
      else:
        mosflm_res = self.labelit_results.get('Labelit results').get('mosflm_res')[0]
      """
      mosflm_res = self.labelit_results.get('Labelit results').get('mosflm_res')[0]
      mosflm_mos = self.labelit_results.get('Labelit results').get('mosflm_mos')
      l1.extend(['mosaicity','resolution'])
      l2.extend([mosflm_mos[0],mosflm_res])
      auto  ='%7s<table cellpadding="0" cellspacing="0" border="1" class="display" id="auto">\n'%''
    else:
      auto  ='%7s<table cellpadding="0" cellspacing="0" border="1" class="display" id="xoalign-auto">\n'%''
    auto +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    for p in l1:
      auto +='%13s<th>%s</th>\n'%('',p)
    auto +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n%11s<tr class="gradeA">\n'%(4*('',))
    for p in l2:
      if p == cell:
        for i in range(len(cell)):
          auto +="%13s<td>%s</td>\n" % ('',p[i])
      else:
        auto +="%13s<td>%s</td>\n" % ('',p)
    auto +='%11s</tr>\n%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(6*('',))
    if labelit:
      self.auto_summary = auto
    else:
      self.auto1_summary = auto

  except:
    self.logger.exception('**ERROR in Summary.summaryAutoCell**')

def summarySTAC_OLD(self):
  """
  Generate STAC html/php file.
  """
  if self.verbose:
    self.logger.debug('Summary::summarySTAC')
  try:
    #STAC alignment results
    if self.stacalign_results:
      v1          = self.stacalign_results.get('STAC align results').get('v1')
      v2          = self.stacalign_results.get('STAC align results').get('v2')
      align_omega = self.stacalign_results.get('STAC align results').get('omega')
      align_kappa = self.stacalign_results.get('STAC align results').get('kappa')
      align_phi   = self.stacalign_results.get('STAC align results').get('phi')
      trans       = self.stacalign_results.get('STAC align results').get('trans')
      #align_rank = self.stacalign_results.get('STAC align results').get('rank')
      #goni_lim    = self.stacalign_results.get('STAC align results').get('goni limited')
      no_sol      = self.stacalign_results.get('STAC align results').get('no_sol')
    #STAC strategy results
    if self.stac_strat:
      if self.stacstrat_results:
        if self.stacstrat_results.get('STAC strat results') != 'FAILED':
          strat_id     = self.stacstrat_results.get('STAC strat results').get('strat ID')
          omega_start  = self.stacstrat_results.get('STAC strat results').get('omega start')
          omega_end    = self.stacstrat_results.get('STAC strat results').get('omega finish')
          strat_kappa  = self.stacstrat_results.get('STAC strat results').get('kappa')
          strat_phi    = self.stacstrat_results.get('STAC strat results').get('phi')
          completeness = self.stacstrat_results.get('STAC strat results').get('completeness')
          strat_rank   = self.stacstrat_results.get('STAC strat results').get('rank')
    #Rename axis in v1 and v2
    d = {'(1.0;0.0;0.0)':'a*','(0.0;1.0;0.0)':'b*','(0.0;0.0;1.0)':'c*'}
    for v in ('v1','v2'):
      for x,line in enumerate(eval(v)):
        for d1 in (d.keys()):
          if line.startswith(d1):
            eval(v).remove(line)
            eval(v).insert(x,d[d1])

    l1 = ['ID','V1','V2','Omega','Kappa','Phi']
    #l2 = [str(x+1),v1,v2,align_omega,align_kappa,align_phi]
    l2 = [x,v1,v2,align_omega,align_kappa,align_phi]

    #l2 = [v1,v2,align_omega,align_kappa,align_phi]
    if self.stac_trans:
      l1.append('Translation')
      l2.append(trans)

    stac_align  ='%7s<h1 class="results">STAC Alignment Results</h1>\n'%''
    if self.align == 'smart':
      stac_align +='%7s<h4 class="results">Alignment for maximum spot separation without blind zone.</h4>\n'%''
    if self.align == 'anom':
      stac_align +='%7s<h4 class="results">Alignment for bringing Bijvoet pairs to the same image.</h4>\n'%''
    if self.align == 'long':
      stac_align +='%7s<h4 class="results">Aligning the long axis parallel to the spindle axis.</h4>\n'%''
    if self.align == 'all':
      stac_align +='%7s<h4 class="results">Aligning each axis parallel to the spindle axis.</h4>\n'%''
    if self.align == 'a':
      stac_align +='%7s<h4 class="results">Aligning a* parallel to the spindle axis.</h4>\n'%''
    if self.align == 'b':
      stac_align +='%7s<h4 class="results">Aligning b* parallel to the spindle axis.</h4>\n'%''
    if self.align == 'c':
      stac_align +='%7s<h4 class="results">Aligning c* parallel to the spindle axis.</h4>\n'%''
    if self.align == 'ab':
      stac_align +='%7s<h4 class="results">Splitting a* and b* parallel to the spindle axis.</h4>\n'%''
    if self.align == 'ac':
      stac_align +='%7s<h4 class="results">Splitting a* and c* parallel to the spindle axis.</h4>\n'%''
    if self.align == 'bc':
      stac_align +='%7s<h4 class="results">Splitting b* and c* parallel to the spindle axis.</h4>\n'%''
    if self.align == 'multi':
      data = str(self.header.get('dataset_repr'))
      stac_align +='%7s<h4 class="results">Aligning crystal to same orientation as %s.</h4>\n'%('',data)

    stac_align +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="stac_align">\n'%''
    stac_align +='%9s<thead align="center">\n%11s<tr>\n'%('','')
    for p in l1:
      stac_align +='%13s<th>%s</th>\n'%('',p)
    stac_align +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
    #When there aren't any solutions.
    for x in range(len(v1)):
      l2 = [x,v1[x],v2[x],align_omega[x],align_kappa[x],align_phi[x]]
      stac_align +='%11s<tr class="gradeA">\n'%''
      for i in range(len(l2)):
        if i == 0:
          stac_align +='%13s<td>%s</td>\n'%('',str(l2[i]+1))
        elif i > 2:
          stac_align +='%13s<td>%5.2f</td>\n'%('',float(l2[i]))
        else:
          stac_align +='%13s<td>%s</td>\n'%('',l2[i])
      stac_align +="%11s</tr>\n"%''
    n = x
    for x in range(len(no_sol)):
      stac_align +='%11s<tr class="gradeC">\n'%''
      #Count up from previous solutions
      n +=1
      for i in range(len(l1)):
        if i == 0:
          stac_align +='%13s<td>%s</td>\n'%('',n)
        elif i in (1,2):
          stac_align +='%13s<td>%s</td>\n'%('',no_sol[x][i-1])
        else:
          stac_align +='%13s<td>no solution</td>\n'%''
      stac_align +="%11s</tr>\n"%''
    stac_align +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
    self.stac_align_summary = stac_align
    if self.stac_strat:
      if self.stacstrat_results:
        if self.stacstrat_results.get('STAC strat results') != 'FAILED':
          stac_strat  ='%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',))
          stac_strat +='%7s<h1 class="results">STAC Strategy Results</h1>\n'%''
          stac_strat +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="stac_strat">\n'%''
          stac_strat +='%9s<thead align="center">\n%11s<tr>\n'%''
          l = ['ID','Omega Start','Omega End','Kappa','Phi','Completeness','Rank']
          for p in l:
            stac_strat +='%13s<th>%s</th>\n'%('',p)
          stac_strat +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
          for x in range(len(strat_id)):
            l = [strat_id[x],omega_start[x],omega_end[x],strat_kappa[x],strat_phi[x],completeness[x],strat_rank[x]]
            stac_strat +='%11s<tr class="gradeA">\n'%''
            for p in l:
              stac_strat +="%13s<td>%5.2f</td>\n" % ('',float(p))
            stac_strat +="%11s</tr>\n"%''
          stac_strat +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
          self.stac_strat_summary = stac_strat

  except:
    self.logger.exception('**Error in Summary.summarySTAC**')

def summaryXOalign(self):
  """
  Generate part of the output for XOalign
  """
  if self.verbose:
    self.logger.debug('Summary::summaryXOalign')
  #try:


  xoalign  ='%7s<h1 class="results">XOalign Results</h1>\n'%''
  #if self.align == 'smart':
  #  xoalign +='%7s<h4 class="results">Alignment for maximum spot separation without blind zone.</h4>\n'%''
  #if self.align == 'anom':
  #  xoalign +='%7s<h4 class="results">Alignment for bringing Bijvoet pairs to the same image.</h4>\n'%''
  if self.align == 'long':
    xoalign +='%7s<h4 class="results">Aligning the long axis parallel to the spindle axis.</h4>\n'%''
  if self.align == 'all':
    xoalign +='%7s<h4 class="results">Aligning each axis parallel to the spindle axis.</h4>\n'%''
  if self.align == 'a':
    xoalign +='%7s<h4 class="results">Aligning a* parallel to the spindle axis.</h4>\n'%''
  if self.align == 'b':
    xoalign +='%7s<h4 class="results">Aligning b* parallel to the spindle axis.</h4>\n'%''
  if self.align == 'c':
    xoalign +='%7s<h4 class="results">Aligning c* parallel to the spindle axis.</h4>\n'%''
  if self.align == 'ab':
    xoalign +='%7s<h4 class="results">Splitting a* and b* parallel to the spindle axis.</h4>\n'%''
  if self.align == 'ac':
    xoalign +='%7s<h4 class="results">Splitting a* and c* parallel to the spindle axis.</h4>\n'%''
  if self.align == 'bc':
    xoalign +='%7s<h4 class="results">Splitting b* and c* parallel to the spindle axis.</h4>\n'%''
  """
  if self.align == 'multi':
    data = str(self.header.get('dataset_repr'))
    xoalign +='%7s<h4 class="results">Aligning crystal to same orientation as %s.</h4>\n'%('',data)
  """
  xoalign +='%7s<table cellpadding="0" cellspacing="0" border="0" class="display" id="xoalign">\n'%''
  xoalign +='%9s<thead align="center">\n%11s<tr>\n'%('','')
  l1 = ['V1','V2','Omega','Kappa','Phi']
  for p in l1:
    xoalign +='%13s<th>%s</th>\n'%('',p)
  xoalign +='%11s</tr>\n%9s</thead>\n%9s<tbody align="center">\n'%(3*('',))
  k = self.xoalign_results.keys()
  for x in range(len(k)):
    if len(self.xoalign_results[k[x]].get('solution')) == 1:
      xoalign +='%11s<tr class="gradeC">\n'%''
      xoalign += '%13s<td>%s</td>\n'%('',self.xoalign_results[k[x]].get('V1'))
      xoalign += '%13s<td>%s</td>\n'%('',self.xoalign_results[k[x]].get('V2'))
      xoalign +=3*('%13s<td>no solution</td>\n'%'')
      xoalign +="%11s</tr>\n"%''
    else:
      for y in range(len(self.xoalign_results[k[x]].get('solution'))):
        xoalign +='%11s<tr class="gradeA">\n'%''
        xoalign += '%13s<td>%s</td>\n'%('',self.xoalign_results[k[x]].get('V1'))
        xoalign += '%13s<td>%s</td>\n'%('',self.xoalign_results[k[x]].get('V2'))
        xoalign += '%13s<td>%5.2f</td>\n'%('',float(self.xoalign_results[k[x]].get('solution')[y][1]))
        xoalign += '%13s<td>%5.2f</td>\n'%('',float(self.xoalign_results[k[x]].get('solution')[y][2]))
        xoalign += '%13s<td>%5.2f</td>\n'%('',float(self.xoalign_results[k[x]].get('solution')[y][3]))
        xoalign +="%11s</tr>\n"%''
  xoalign +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
  self.xoalign_summary = xoalign

  """
  #When there aren't any solutions.
  for x in range(len(v1)):
    l2 = [x,v1[x],v2[x],align_omega[x],align_kappa[x],align_phi[x]]
    xoalign +='%11s<tr class="gradeA">\n'%''
    for i in range(len(l2)):
      if i == 0:
        xoalign +='%13s<td>%s</td>\n'%('',str(l2[i]+1))
      elif i > 2:
        xoalign +='%13s<td>%5.2f</td>\n'%('',float(l2[i]))
      else:
        xoalign +='%13s<td>%s</td>\n'%('',l2[i])
    xoalign +="%11s</tr>\n"%''
  n = x
  for x in range(len(no_sol)):
    xoalign +='%11s<tr class="gradeC">\n'%''
    #Count up from previous solutions
    n +=1
    for i in range(len(l1)):
      if i == 0:
        xoalign +='%13s<td>%s</td>\n'%('',n)
      elif i in (1,2):
        xoalign +='%13s<td>%s</td>\n'%('',no_sol[x][i-1])
      else:
        xoalign +='%13s<td>no solution</td>\n'%''
    xoalign +="%11s</tr>\n"%''
  xoalign +='%9s</tbody>\n%7s</table>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(5*('',))
  self.xoalign_summary = xoalign
  """


def summaryLabelitBC(self):
  """
  Create the table for the Labelit BC summary.NOT USED!!
  """
  if self.verbose:
    self.logger.debug('Summary::summaryLabelitBC')
  try:
    if self.labelit_results.has_key('best'):
      x = 2
    else:
      x = 1
    labelit ='    <div id="container">\n'
    for i in range(0,x):
      if i == 0:
        j = "['0']"
      else:
        j = "['best']"
        labelit +='    <div id="container">\n'
      labelit_face      = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_face')")
      labelit_solution  = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_solution')")
      labelit_metric    = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_metric')")
      labelit_fit       = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_fit')")
      labelit_rmsd      = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_rmsd')")
      labelit_spots_fit = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_spots_fit')")
      labelit_system    = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_system')")
      labelit_cell      = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_cell')")
      labelit_volume    = eval("self.labelit_results"+j+".get('Labelit results').get('labelit_volume')")
      x_beam            = eval("self.labelit_results"+j+".get('beam_X')")
      y_beam            = eval("self.labelit_results"+j+".get('beam_Y')")
      labelit +='    <div class="full_width big">\n'
      labelit +='      <div id="demo">\n'
      if i == 0:
        labelit +='        <h1 class="results">Labelit Results with Original Beam Center ('+str(self.x_beam)+', '+str(self.y_beam)+')</h1>\n'
        labelit +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="labelit1">\n'
      else:
        labelit +='        <h1 class="results">Labelit Results with NEW Beam Center ('+str(x_beam)+', '+str(y_beam)+')</h1>\n'
        labelit +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="labelit2">\n'
      labelit +='          <thead align="center">\n'
      labelit +='            <tr>\n'
      labelit +='              <th>&nbsp</th>\n'
      labelit +='              <th>Solution</th>\n'
      labelit +='              <th>Metric</th>\n'
      labelit +='              <th>Fit</th>\n'
      labelit +='              <th>RMSD</th>\n'
      labelit +='              <th># of Spots</th>\n'
      labelit +='              <th>Crystal System</th>\n'
      labelit +='              <th>a</th>\n'
      labelit +='              <th>b</th>\n'
      labelit +='              <th>c</th>\n'
      labelit +='              <th>&alpha;</th>\n'
      labelit +='              <th>&beta;</th>\n'
      labelit +='              <th>&gamma;</th>\n'
      labelit +='              <th>Volume</th>\n'
      labelit +='            </tr>\n'
      labelit +='          </thead>\n'
      labelit +='          <tbody align="center">\n'
      for x in range(len(labelit_solution)):
        system = labelit_system[x][0]+' '+labelit_system[x][1]
        labelit +='            <tr class="gradeA">\n'
        labelit +="              <td>"+labelit_face[x]+"</td>\n"
        labelit +="              <td>"+labelit_solution[x]+"</td>\n"
        labelit +="              <td>"+labelit_metric[x]+"</td>\n"
        labelit +="              <td>"+labelit_fit[x]+"</td>\n"
        labelit +="              <td>"+labelit_rmsd[x]+"</td>\n"
        labelit +="              <td>"+labelit_spots_fit[x]+"</td>\n"
        labelit +="              <td>"+system+"</td>\n"
        labelit +="              <td>"+labelit_cell[x][0]+"</td>\n"
        labelit +="              <td>"+labelit_cell[x][1]+"</td>\n"
        labelit +="              <td>"+labelit_cell[x][2]+"</td>\n"
        labelit +="              <td>"+labelit_cell[x][3]+"</td>\n"
        labelit +="              <td>"+labelit_cell[x][4]+"</td>\n"
        labelit +="              <td>"+labelit_cell[x][5]+"</td>\n"
        labelit +="              <td>"+labelit_volume[x]+"</td>\n"
        labelit +="            </tr>\n\n"
      labelit +='          </tbody>\n'
      labelit +='        </table>\n'
      labelit +='      </div>\n'
      labelit +='     </div>\n'
      labelit +='    </div>\n'
    if x == 1:
      labelit +='    <div id="container">\n'
      labelit +='    <div class="full_width big">\n'
      labelit +='      <div id="demo">\n'
      labelit +='    <h4 class="results">The original beam center produced the best results</h3>\n'
      labelit +="      </div>\n"
      labelit +="    </div>\n"
      labelit +="    </div>\n"

    labelit +='    <div id="container">\n'
    labelit +='    <div class="full_width big">\n'
    labelit +='      <div id="demo">\n'
    labelit +='        <h1 class="results">All Beam Center Results</h1>\n'
    labelit +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="labelit3">\n'
    labelit +='          <thead align="center">\n'
    labelit +='            <tr>\n'
    labelit +='              <th>P1 Labelit RMSD</th>\n'
    labelit +='              <th>P1 Mosflm RMS</th>\n'
    labelit +='              <th>P1 Mosflm X beam</th>\n'
    labelit +='              <th>P1 Mosflm Y beam</th>\n'
    labelit +='              <th>Space Group</th>\n'
    labelit +='              <th>Metric</th>\n'
    labelit +='              <th>Labelit RMSD</th>\n'
    labelit +='              <th>Mosflm RMS</th>\n'
    labelit +='              <th>Input X beam</th>\n'
    labelit +='              <th>Input Y beam</th>\n'
    labelit +='              <th>Labelit X beam</th>\n'
    labelit +='              <th>Labelit Y beam</th>\n'
    labelit +='              <th>Mosflm X beam</th>\n'
    labelit +='              <th>Mosflm Y beam</th>\n'
    labelit +='              <th>Run</th>\n'
    labelit +='            </tr>\n'
    labelit +='          </thead>\n'
    labelit +='          <tbody align="center">\n'
    runs = self.labelit_results.keys()
    for run in runs:
      if run.startswith('bc'):
        if type(self.labelit_results[run].get('Labelit results')) == dict:
          metric = self.labelit_results[run].get('labelit_stats').get('best').get('metric')
          sg = self.labelit_results[run].get('labelit_stats').get('best').get('SG')
          p1_rmsd = self.labelit_results[run].get('labelit_stats').get('P1').get('rmsd')
          sg_rmsd = self.labelit_results[run].get('labelit_stats').get('best').get('rmsd')
          p1_rms = self.labelit_results[run].get('labelit_stats').get('P1').get('mos_rms')
          sg_rms = self.labelit_results[run].get('labelit_stats').get('best').get('mos_rms')
          mos_x = self.labelit_results[run].get('labelit_stats').get('P1').get('mos_x')
          mos_y = self.labelit_results[run].get('labelit_stats').get('P1').get('mos_y')
          mos_x2 = self.labelit_results[run].get('labelit_stats').get('best').get('mos_x')
          mos_y2 = self.labelit_results[run].get('labelit_stats').get('best').get('mos_y')
          labelit_x = self.labelit_results[run].get('Labelit results').get('labelit_bc').get('labelit_x_beam')
          labelit_y = self.labelit_results[run].get('Labelit results').get('labelit_bc').get('labelit_y_beam')
          input_x = self.labelit_results[run].get('beam_X')
          input_y = self.labelit_results[run].get('beam_Y')
          if self.mosflm_sg == sg:
            labelit +='            <tr class="gradeA">\n'
            labelit +="              <td>"+p1_rmsd+"</td>\n"
            labelit +="              <td>"+p1_rms+"</td>\n"
            labelit +="              <td>"+mos_x+"</td>\n"
            labelit +="              <td>"+mos_y+"</td>\n"
            labelit +="              <td>"+sg+"</td>\n"
            labelit +="              <td>"+metric+"</td>\n"
            labelit +="              <td>"+sg_rmsd+"</td>\n"
            labelit +="              <td>"+sg_rms+"</td>\n"
            labelit +="              <td>"+input_x+"</td>\n"
            labelit +="              <td>"+input_y+"</td>\n"
            labelit +="              <td>"+labelit_x+"</td>\n"
            labelit +="              <td>"+labelit_y+"</td>\n"
            labelit +="              <td>"+mos_x2+"</td>\n"
            labelit +="              <td>"+mos_y2+"</td>\n"
            labelit +="              <td>"+run+"</td>\n"
            labelit +="            </tr>\n\n"
    labelit +='          </tbody>\n'
    labelit +='        </table>\n'
    labelit +='      </div>\n'
    labelit +='     </div>\n'
    labelit +='    </div>\n'

    self.labelit_summary = labelit

  except:
    self.logger.exception('**ERROR in Summary.summaryLabelit.**')

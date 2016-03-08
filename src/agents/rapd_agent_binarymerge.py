"""
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

__created__ = "2011-03-24"
__maintainer__ = "Surajit Banerjee"
__email__ = "sbanerjee@anl.gov"
__status__ = "Production"

"""
Simple combining of two wedges created by the integration pipeline of rapd
"""

# This is an active rapd agent
RAPD_AGENT = True

# This handler's request type
AGENT_TYPE = "echo"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "d64d3ebde56211e58da3c82a1400d5bc"

# Standard imports
import logging
import logging.handlers
import multiprocessing
import os
import shutil
import subprocess
import time
import unittest
from xml.dom.minidom import parse

# Additional imports
from numpy import interp
# from MySQLdb import TIME

# RAPD imports
from rapd_agent_stats import AutoStats
from rapd_communicate import Communicate
from xia2 import Xia

class RapdAgent(multiprocessing.Process):
    """
    To merge 'SIMPLY' two data sets from RAPD's integration pipeline
    """
    def __init__(self,input,logger):
        """
        Initialize the SimpleMerge process
        """

        logger.info('SimpleMerge::__init__')
        self.command = input
        self.logger  = logger
        self.results = False
        self.summary = {}
        multiprocessing.Process.__init__(self,name='SimpleMerge')
        self.start()

    def run(self):
        self.logger.debug('SimpleMerge::run')
        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """
        Before running the main process
        - change to the current directory
        - copy files to the working directory
        """

        self.logger.debug('SimpleMerge::preprocess')

        self.dirs = self.command[1]
        self.original_data = self.command[2]['original']
        self.secondary_data = self.command[2]['secondary']
        self.repr = self.command[2]['repr']
        self.settings = self.command[3]
        self.controller_address = self.command[-1]
        #self.process_id = self.command[2]['image_data']['process_id']
        self.process_id = self.command[2]['process_id']
        #self.in_files = (self.command[2]['original']['merge_file'],
        #                 self.command[2]['secondary']['merge_file'])
        #Make and move to the work directory
        if os.path.isdir(self.dirs['work']) == False:
            os.makedirs(self.dirs['work'])
        os.chdir(self.dirs['work'])
        #copy the files to be merged to the work directory
        shutil.copy(self.command[2]['original']['merge_file'],"a.mtz")
        shutil.copy(self.command[2]['secondary']['merge_file'],"b.mtz")
        self.in_files = ("a.mtz","b.mtz")

    def process(self):
        """
        analyze, copy file as reference, check basis, rebatch, combine, etc.
        """

        self.logger.debug('SimpleMerge::process')

        # Analyze the reflections for batches and reflections
        batches,reflections = self.getFileInfo(self.in_files)
        self.logger.debug(batches)
        self.logger.debug(reflections)

        #check the number of reflections to make a reference file
        ref_max = (None,0)
        print reflections
        for ref_file,ref_refls in reflections.iteritems():
            if (ref_refls > ref_max[1]):
                ref_max = (ref_file,ref_refls)
        self.logger.debug('%s with %d reflections will be used as the reference file' % ref_max)
        shutil.copyfile(ref_max[0],'./reference.mtz')


        referenced_files = []
        referenced_batches = {}
        for in_file in self.in_files:
            ref_file = self.referenceFile(hklref = 'reference.mtz',
                                          hklin = in_file)
            #save the reference files
            referenced_files.append(ref_file)
            #Make sure we keep track of batch information
            referenced_batches[ref_file] = batches[in_file]
        self.logger.debug(referenced_files)
        self.logger.debug(referenced_batches)

        # Rebatch all the files
        ready_files = []
        scale_batches = []
        batch_inc = 0

        #rebatch each file
        for counter,ref_file in enumerate(referenced_files):
            for batch in referenced_batches[ref_file]:
                batch0 = batch[0] + batch_inc
                batch1 = batch[1] + batch_inc
                scale_batches.append((batch0,batch1))
            ready_files.append(self.prepareFile(in_file=ref_file,
                                                batch=batch_inc))
            batch_inc += referenced_batches[ref_file][-1][1]

        # Combine the files into one
        combined_file = self.combineFiles(files=ready_files)

        # Scale the files, adjusting for I/sigI of 2.0 in the outer shell
        scale = self.Scale(in_file=combined_file,
                           batches=scale_batches)

        # Check the spacegroup
        check,correct,operators = self.performCheck(in_file=scale)

        # Rescale if in a new spacegroup
        if (correct == False):
            combined_file = self.correctSpacegroup(combined_file,operators)
            scale = self.Scale(in_file=combined_file,
                               batches=scale_batches)
            check,correct,operators = self.performCheck(in_file=scale)

        # Finish the data
        finish = self.finishData(in_file=check)

        # Parse the results
        graphs,tables = self.parseScala('scala1.log')

        #work_dir = self.dirs['work']
        #self.run_analysis(os.path.join(os.getcwd(),finish), work_dir)

        #print tables
        scalaHTML = self.scalaPlots(graphs,tables)
        parseHTML = self.parseResults('scala1.log')
        summary = self.parseResults('scala1.log')
        longHTML = self.makeLongResults(['performcheck.log','scala1.log',
                                         'truncate.log','performcheck.log'])
        work_dir = self.dirs['work']
        merge_files = self.clean_fs(work_dir)
        self.logger.info("Done with clean_fs")
        self.run_analysis(merge_files.get('mtzfile'), work_dir)
        """
        {'reference' : file_base + '_prep.mtz',
                     'mergable' : file_base + '_sortedMergable.mtz',
                     'mtzfile' : file_base + '_free.mtz',
                     'anomalous_sca' : file_base + '_anomalous.sca',
                     'native_sca' : file_base + '_native.sca',
                     'scala_log' : file_base + '_scala.log',
                     'downloadable' : file_base + '.tar.bz2'}
        """
        # Assign to a result
        self.results = {'plots' : scalaHTML,
                        'short' : parseHTML[0],
                        'long'  : longHTML,
                        'summary' : parseHTML[1],
                        'merge_file' : merge_files['mergable'],
                        'download_file' : merge_files['downloadable'],
                        'mtz_file' : merge_files['mtzfile']}

    def getFileInfo(self,in_files):
        """
        Information about batches
        """

        self.logger.debug('SimpleMerge::getFileInfo %s' %str(in_files))

        batches = {}
        reflections = {}

        for file in in_files:
            p = subprocess.Popen('pointless hklin %s > info.log' % file, shell=True)
            sts = os.waitpid(p.pid, 0)[1]

            batches[file] = []

            for line in open('info.log'):
                if ('consists of batches' in line):
                    batch_start = int(line.split()[6])
                    batch_end = int(line.split()[8])
                    batches[file].append((batch_start,batch_end))
                    self.logger.debug('%s has batches %d to %d' % (file,batch_start,batch_end))
                if ('Number of reflections  =' in line):
                    reflections[file] = int(line.split('=')[1].strip())

        return(batches,reflections)

    def referenceFile(self,hklref,hklin):
        """
        Sync the space group as the reference file using POINTLESS
        """

        self.logger.debug('referenceFile hklref: %s hklin: %s' % (hklref,hklin))
        out_file = hklin.replace('.mtz','_ref.mtz')
        comfile = open('ref.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('pointless hklref '+hklref+' hklin '+hklin+' hklout '+out_file+'> ref.log <<eof \n')
        comfile.write('SETTING C2 \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('./ref.sh',0755)
        time.sleep(0.5)
        p = subprocess.Popen('./ref.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        try:
            pass #os.remove('ref.sh')
            #os.remove('ref.log')
        except:
            self.logger.exception("Couldn't remove ref files")
        return(out_file)

    def prepareFile(self,in_file,batch):
        """
        Rebatching the file using REBATCH
        """

        self.logger.debug('prepareFile file: %s batch: %d' % (in_file,batch))
        out_file = in_file.replace('.mtz','_prep.mtz')

        comfile = open('prep.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('rebatch hklin '+in_file+' hklout '+out_file+'> prep.log <<eof \n')
        comfile.write('batch add '+str(batch)+' \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('prep.sh',0755)
        p = subprocess.Popen('./prep.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('prep.sh')
        os.remove('prep.log')

        return(out_file)

    def combineFiles(self,files,VERBOSE=False):
        """
        Combining all reflection using MTZUTILS
        and sorting them using SORTMTZ
        """

        self.logger.debug('combineFiles files: %s' % str(files))

        if (len(files) > 2):
            self.logger.debug('combineFiles only work for pairs - exiting.')
            sys.exit()

        elif (len(files) == 2):
            comfile = open('combine.sh','w')
            comfile.write('#!/bin/csh \n')
            comfile.write('mtzutils ')
            top = len(files)
            for i in range(top):
                comfile.write('hklin'+str(top-i)+' '+files[top-i-1]+' ')
            comfile.write('hklout combined.mtz > combine.log <<eof \n')
            comfile.write('merge \n')
            comfile.write('eof \n')
            comfile.close()
            os.chmod('combine.sh',0755)
            p = subprocess.Popen('./combine.sh',shell=True)
            sts = os.waitpid(p.pid, 0)[1]
            os.remove('combine.sh')
            #os.remove('combine.log')

            comfile = open('sort.sh','w')
            comfile.write('#!/bin/csh \n')
            comfile.write('sortmtz hklin combined.mtz hklout sorted.mtz > sort.log <<eof \n')
            comfile.write('H K L M/ISYM BATCH \n')
            comfile.write('eof \n')
            comfile.close()
            os.chmod('sort.sh',0755)
            p = subprocess.Popen('./sort.sh',shell=True)
            sts = os.waitpid(p.pid, 0)[1]
            os.remove('sort.sh')
            os.remove('sort.log')

            return('sorted.mtz')

    def Scale(self,in_file,batches,VERBOSE=False):
        """
        Scaling files using SCALA, check for highest resolution,
        Scale back again with the new highest resolution
        """

        self.logger.debug('Scale in_file: %s batches: %s' % (in_file, str(batches)))

        batch_inc = 0

        comfile = open('scala.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('scala hklin '+in_file+' hklout scaled.mtz > scala.log <<eof \n')
        comfile.write('bins 10 \n')
        for i in range(len(batches)):
            comfile.write('run '+str(i+1)+' batch '+str(batches[i][0])+' to '+str(batches[i][1])+'  \n')
            comfile.write('name run '+str(i+1)+' project RAPD crystal RAPD dataset DATA \n')
        comfile.write('scales constant \n')
        comfile.write('exclude sdmin 2.0 \n')
        comfile.write('sdcorrection fixsdb noadjust norefine both 1.0 0.0 \n')
        comfile.write('anomalous on \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('scala.sh',0755)
        p = subprocess.Popen('./scala.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('scala.sh')

        scalog = open('scala.log', 'r').readlines()

        new_hi_res = False
        count = 0
        IsigI = 0
        hires = 0
        for line in scalog:
            if 'Average I,sd and Sigma' in line:
                count = 1
            if count > 0:
                sline = line.split()
                if (len(sline) > 10 and sline[0].isdigit()):
                    prev_IsigI = IsigI
                    prev_hires = hires
                    IsigI = float(sline[12])
                    hires = float(sline[2])
                    if IsigI < 2.0:
                        new_hi_res = interp([2.0],[IsigI,prev_IsigI],
                                            [hires,prev_hires])
                        break

            if count > 0 and 'Overall' in line:
                break

        comfile = open('scala1.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('scala hklin '+in_file+' hklout scaled.mtz > scala1.log <<eof \n')
        comfile.write('bins 10 \n')
        for i in range(len(batches)):
            comfile.write('run '+str(i+1)+' batch '+str(batches[i][0])+' to '+str(batches[i][1])+'  \n')
            comfile.write('name run '+str(i+1)+' project RAPD crystal RAPD dataset DATA \n')
        comfile.write('scales constant \n')
        comfile.write('exclude sdmin 2.0 \n')
        comfile.write('sdcorrection fixsdb noadjust norefine both 1.0 0.0 \n')
        comfile.write('anomalous on \n')
        if new_hi_res:
            comfile.write('resolution high '+str(new_hi_res[0])+' \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('scala1.sh',0755)
        p = subprocess.Popen('./scala1.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        #os.remove('scala1.sh')

        scalogf = open('scala1.log', 'r').readlines()

        return('scaled.mtz')
        return('scala1.log')



    def performCheck(self,in_file):
        """
        Check the Space Group of the scaled and merged data
        """

        self.logger.debug('performCheck in_file: %s' % in_file)

        comfile = open('pcheck.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('pointless hklin '+in_file+' xmlout performcheck.xml > performcheck.log << eof \n')
        comfile.write('SETTING C2 \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('pcheck.sh',0755)
        p = subprocess.Popen('./pcheck.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('pcheck.sh')

        dom1 = parse('performcheck.xml')

        sg_start = False
        for node in dom1.getElementsByTagName('SpacegroupName'):
            if not (sg_start):
                sg_start = node.firstChild.data.strip()
        for node in dom1.getElementsByTagName('BestSolution'):
            for cnode in node.getElementsByTagName('GroupName'):
                soln_group = cnode.firstChild.data.strip()
            for cnode in node.getElementsByTagName('ReindexOperator'):
                soln_operator = cnode.firstChild.data.strip()

        self.logger.debug('Starting spacegroup: %s' % sg_start)
        self.logger.debug('Best solution: %s' % soln_group)
        self.logger.debug('Reindex operator: %s' % soln_operator)

        if (sg_start == soln_group):
            self.logger.debug('Data is in the correct spacegroup')
            return(in_file,True,None)
        else:
            self.logger.debug('Data is NOT in the correct spacegroup')
            return(in_file,False,(soln_operator,soln_group))

    def correctSpacegroup(self,in_file,operators):
        """
        Correct the Space Group
        """

        self.logger.debug('correctSpacegroup in_file: %s %s %s' % (in_file,operators[0],operators[1]))
        soln_operator,soln_group = operators

        comfile = open('correct.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('pointless hklin '+in_file+' hklout corrected.mtz xmlout correct.xml > correct.log << eof \n')
        comfile.write('SETTING C2 \n')
        comfile.write('REINDEX %s \n' % soln_operator)
        comfile.write('SPACEGROUP %s \n' % soln_group)
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()

        os.chmod('correct.sh',0755)
        p = subprocess.Popen('./correct.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('correct.sh')

        return('corrected.mtz')

    def finishData(self,in_file, VERBOSE=False):
        """
        Finish the data by truncating and adding free R flag in it
        """

        self.logger.debug('finishData in_file: %s' % in_file)

        comfile = open('truncate.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('truncate hklin '+in_file+' hklout truncated.mtz > truncate.log <<eof \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('truncate.sh',0755)
        p = subprocess.Popen('./truncate.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('truncate.sh')

        comfile = open('freer.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('freerflag hklin truncated.mtz hklout freer.mtz > freer.log <<eof \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('freer.sh',0755)
        p = subprocess.Popen('./freer.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('freer.sh')

        comfile = open('mtz2native.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('mtz2various hklin truncated.mtz hklout native.sca > mtz2native.log <<eof \n')
        comfile.write('OUTPUT SCALEPACK \n')
        comfile.write('labin I(+)=IMEAN SIGI(+)=SIGIMEAN \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('mtz2native.sh',0755)
        p = subprocess.Popen('./mtz2native.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('mtz2native.sh')

        self.fixMtz2Sca('native.sca')

        comfile = open('mtz2anom.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('mtz2various hklin truncated.mtz hklout anomalous.sca > mtz2anom.log <<eof \n')
        comfile.write('OUTPUT SCALEPACK \n')
        comfile.write('labin I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-) SIGI(-)=SIGI(-) \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        os.chmod('mtz2anom.sh',0755)
        p = subprocess.Popen('./mtz2anom.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        os.remove('mtz2anom.sh')

        self.fixMtz2Sca('anomalous.sca')

        return('freer.mtz')

    def fixMtz2Sca(self,scafile):
        """
        Fix the space problem in the spacegroup symbol
        """

        self.logger.debug('fixMtz2Sca file:%s' % scafile)

        inlines = open(scafile,'r').readlines()
        symline = inlines[2]
        newline = symline[:symline.index(symline.split()[6])]+''.join(symline.split()[6:])+'\n'
        inlines[2] = newline

        outfile = open(scafile,'w')
        for line in inlines:
            outfile.write(line)
        #return()

    def scala_plots(self, graphs, tables):
        """
        generate plots html file from scala results
        """

        self.logger.debug('scala_plots')
        # plotThese contains a list of graph titles that you want plotted
        # additional plots may be requested by adding the title (stripped
        # of leading and trailing whitespace) to plotThese.
        plotThese = {
                     #'Mn(k) & 0k (at theta = 0) v range' : 'Scales',
                     #'B  v range'                        : 'Bfactor',
                     'Rmerge v Batch for all runs'       : 'R vs frame',
                     'I/sigma, Mean Mn(I)/sd(Mn(I))'     : 'I/sigma',
                     'Rmerge v Resolution'               : 'R vs Res',
                     'Average I,sd and Sigma'            : 'I vs Res',
                     'Completeness v Resolution'         : '%Comp',
                     'Multiplicity v Resolution'         : 'Redundancy',
                     'Rpim (precision R) v Resolution'   : 'Rpim',
                     'Rmeas, Rsym & PCV v Resolution'    : 'Rmeas',
                     #'Rd vs. Dose difference'            : 'Rd',
                     'Anom & Imean CCs v resolution -'     : 'Anom Corr',
                     'RMS correlation ratio'            : 'RCR'
                     }

        scala_plot = """<html>
<head>
  <style type="text/css">
    body     { background-image: none; }
    .x-label { position:relative; text-align:center; top:10px; }
    .title   { font-size:30px; text-align:center; }
</style>
<script type="text/javascript">
$(function() {
    // Tabs
    $('.tabs').tabs();
});
</script>
</head>
<body>
<table>
  <tr>
    <td width="100%">
    <div class="tabs">
      <!-- This is where the tab labels are defined
           221 = tab2 (on page) tab2(full output tab) tab1 -->
      <ul>
"""
        # Define tab labels for each graph
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                title = plotThese[graph[0]]
                scala_plot += ('        <li><a href="#tabs-22' + str(i) +
                               '">' + title + '</a></li>\n')
        scala_plot += '      </ul>\n'

        # Define title and x-axis label for each graph
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                scala_plot += '      <div id ="tabs-22' + str(i) + '">\n'
                scala_plot += '        <div class="title"><b>'
                scala_plot += graph[0] + '</b></div>\n'
                scala_plot += '        <div id="chart' + str(i) + '_div" style='
                scala_plot += '"width:800px;height:600px"></div>\n'
                scala_plot += '        <div class="x-label">'
                scala_plot += graph[1] + '</div>\n'
                scala_plot += '      </div>\n'

        scala_plot += """</div> <!-- End of Tabs -->
    </td>
  </tr>
</table>

<script id="source" language="javascript" type="text/javascript">
$(function () {

"""
         # varNames is a counter, such that the variables used for plotting
        # will simply be y+varName (i.e. y0, y1, y2, etc)
        # actual labels are stored transiently in varLabel, and added
        # as comments next to the variable when it is initialized
        varNum=0
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                varLabel = []
                data = []

                scala_plot += '    var '
                # graph[2] is the label for the y-values
                for ylabel in (graph[2]):
                    varLabel.append(ylabel)
                    var = 'y' + str(varNum)
                    varNum += 1
                    data.append(var)
                    if ylabel == graph[2][-1]:
                        scala_plot += var + '= [];\n'
                    else:
                        scala_plot += var + ' = [], '
                xcol = graph[3]
                for line in tables[graph[5]]:
                    for y,ycol in enumerate(graph[4]):
                        if line[ycol] != '-':
                            scala_plot += '         ' + data[y] + '.push(['
                            scala_plot += line[xcol] + ',' + line[ycol]
                            scala_plot += ']);\n'

                scala_plot += '    var plot' + str(i)
                scala_plot += ' = $.plot($("#chart' + str(i) + '_div"), [\n'
                for x in range(0,len(data),1):
                    scala_plot += '        {data: ' + data[x] + ', label:"'
                    scala_plot += varLabel[x] + '" },\n'
                scala_plot += '        ],\n'
                scala_plot += '        { lines: {show: true},\n'
                scala_plot += '          points: {show: false},\n'
                scala_plot += "          selection: { mode: 'xy' },\n"
                scala_plot += '          grid: {hoverable: true, '
                scala_plot += 'clickable: true },\n'
                if graph[1] == 'Dmin (A)':
                    scala_plot += '          xaxis: {ticks: [\n'
                    for line in tables[graph[5]]:
                        scala_plot += '                         ['
                        scala_plot += line[xcol] + ',"' + line[xcol+1]
                        scala_plot += '"],\n'
                    scala_plot += '                  ]},\n'
                scala_plot += '    });\n\n'

        scala_plot += """
    function showTooltip(x, y, contents) {
        $('<div id=tooltip>' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint = null;
"""
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                scala_plot += '    $("#chart' + str(i) + '_div").bind'
                scala_plot += """("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
"""
                if graph[1] == 'Dmin (A)':
                    scala_plot += '                    '
                    scala_plot += \
                    'var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),\n'
                else:
                    scala_plot += '                    '
                    scala_plot += 'var x = item.datapoint[0].toFixed(2),\n'
                scala_plot += \
"""                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
"""
        scala_plot += '\n});\n</script>\n </body>\n</html>'

        try:
            with open('scala_plot.html','w') as file:
                file.write(scala_plot)
            return('scala_plot.html')
        except IOError:
            self.logger.debug ('Could not create scala plot html file.')
            return ('Error')

    def parseResults(self, scalogf):
        """
        Parse the scala1.log and final pointless log for display to UI
        """

        self.logger.debug('parseResults %s' % scalogf)
        results = {}

        #scala_lines = open('scala1.log','r').readlines()
        scala_lines = open(scalogf,'r').readlines()
        table_start = 0

        for i,v in enumerate(scala_lines):
            if v.startswith('Summary data for'):
                table_start = i + 1
        for i,v in enumerate(scala_lines[table_start:]):
            vsplit = v.split()
            vstrip = v.strip()

            #bin resolution limits
            if vstrip.startswith('Low resolution limit'):
                results['bins_low'] = vsplit[3:6]
            elif vstrip.startswith('High resolution limit'):
                results['bins_high'] = vsplit[3:6]

            #Rmerge
            elif (vstrip.startswith('Rmerge      ')):
                results['rmerge'] = vsplit[1:4]
            elif (vstrip.startswith('Rmerge in top intensity bin')):
                results['rmerge_top'] = [vsplit[5]]

            #Rmeas
            elif (vstrip.startswith('Rmeas (within I+/I-)')):
                results['rmeas_anom'] = vsplit[3:6]
            elif (vstrip.startswith('Rmeas (all I+ & I-)')):
                results['rmeas_norm'] = vsplit[5:8]

            #Rpim
            elif (vstrip.startswith('Rpim (within I+/I-)')):
                results['rpim_anom'] = vsplit[3:6]
            elif (vstrip.startswith('Rpim (all I+ & I-)')):
                results['rpim_norm'] = vsplit[5:8]

            #Bias
            elif (vstrip.startswith('Fractional partial bias')):
                results['bias'] = vsplit[3:6]

            #Number of refections
            elif (vstrip.startswith('Total number of observations')):
                results['total_obs'] = vsplit[4:7]
            elif (vstrip.startswith('Total number unique')):
                results['unique_obs'] = vsplit[3:6]

            #I/sigI
            elif (vstrip.startswith('Mean((I)/sd(I))')):
                results['isigi'] = vsplit[1:4]

            #Completeness
            elif (vstrip.startswith('Completeness')):
                results['completeness'] = vsplit[1:4]
            elif (vstrip.startswith('Anomalous completeness')):
                results['anom_completeness'] = vsplit[2:5]

            #Multiplicity
            elif (vstrip.startswith('Multiplicity')):
                results['multiplicity'] = vsplit[1:4]
            elif (vstrip.startswith('Anomalous multiplicity')):
                results['anom_multiplicity'] = vsplit[2:5]

            #Anomalous indicators
            elif (vstrip.startswith('DelAnom correlation between half-sets')):
                results['anom_correlation'] = vsplit[4:7]
            elif (vstrip.startswith('Mid-Slope of Anom Normal Probability')):
                results['anom_slope'] = [vsplit[5]]

            #unit cell
            elif (vstrip.startswith('Average unit cell:')):
                results['scaling_unit_cell'] = vsplit[3:]

            #spacegroup
            elif (vstrip.startswith('Space group:')):
                results['scale_spacegroup'] = "".join(vsplit[2:])
                break

        #for k,v in results.iteritems():
            #print k,v

        #Start constructing the parsed results html file
        parseHTML = 'merge_results.php'

        with open(parseHTML, 'w') as file:
            """
            file.write('''<?php
            //prevents caching
            header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
            header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
            header("Cache-Control: post-check=0, pre-check=0",false);

            session_cache_limiter();
            session_start();

            require('/var/www/html/rapd/login/config.php');
            require('/var/www/html/rapd/login/functions.php');

            if(allow_user() != "yes")
            {
                if(allow_local_data($_SESSION[data]) != "yes")
                {
                    include ('/login/no_access.html');
                    exit();
                } else {
                    $local = 1;
                }
            } else {
                $local = 0;
            }
            ?>
            <head>
            <!-- Inline Stylesheet -->
            <style type="text/css"><!--
                body {font-size: 17px; }
                table.integrate td, th {border-style: solid;
                               border-width: 2px;
                               border-spacing: 0;
                               border-color: gray;
                               padding: 5px;
                               text-align: center;
                               height: 2r10px;
                               font-size: 15px; }
                table.integrate tr.alt {background-color: #EAF2D3; }
            --></style>
            </head>
            <body>
            <div id="container">\n<br>\n''')
            """
            file.write('''<?php
            //prevents caching
            header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
            header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
            header("Cache-Control: post-check=0, pre-check=0",false);

            session_cache_limiter();
            session_start();

            require('/var/www/html/rapd/login/config.php');
            require('/var/www/html/rapd/login/functions.php');

            if(allow_user() != "yes")
            {
                if(allow_local_data($_SESSION[data]) != "yes")
                {
                    include ('/login/no_access.html');
                    exit();
                }
            }
            ?>
            <head>
            <!-- Inline Stylesheet -->
            <style type="text/css"><!--
                body {font-size: 17px; }
                table.integrate td, th {border-style: solid;
                               border-width: 2px;
                               border-spacing: 0;
                               border-color: gray;
                               padding: 5px;
                               text-align: center;
                               height: 2r10px;
                               font-size: 15px; }
                table.integrate tr.alt {background-color: #EAF2D3; }
            --></style>
            </head>
            <body>
            <div id="container">\n<br>\n''')


            file.write('<div align="center">')
            file.write('<h3 class="green">Merging Results</h3>\n')
            spacegroupLine = ('<h2>Spacegroup: ' + ''
                               .join(results['scale_spacegroup']) + '</h2>\n\n')
            spacegroupLine += ('<h2>Unit Cell: ' + ' '
                               .join(results['scaling_unit_cell']) + '</h2>\n\n')
            file.write(spacegroupLine)

            file.write('<table class="integrate">\n')
            file.write('<tr><th></th><td>Overall</td><td>Inner Shell</td><td>Outer Shell</td></tr>\n')


            pairs1 = [('High resolution limit','bins_high'),
                      ('Low resolution limit','bins_low'),
                      ('Completeness','completeness'),
                      ('Multiplicity','multiplicity'),
                      ('I/sigma','isigi'),
                      ('Rmerge','rmerge'),
                      ('Rmeas(I)','rmeas_norm'),
                      ('Rmeas(I+/-)','rmeas_anom'),
                      ('Rpim(I)','rpim_norm'),
                      ('Rpim(I+/-)','rpim_anom'),
                      ('Partial bias','bias'),
                      ('Anomalous completeness','anom_completeness'),
                      ('Anomalous multiplicity','anom_multiplicity'),
                      ('Anomalous correlation','anom_correlation'),
                      ('Anomalous slope','anom_slope'),
                      ('Total observations','total_obs'),
                      ('Total unique','unique_obs')]

            count = 0
            for l,k in pairs1:
                if (count%2 == 0):
                    file.write('<tr><th>'+l+'</th>')
                else:
                    file.write('<tr class="alt"><th>'+l+'</th>')
                for v in results[k]:
                    file.write('<td>'+v.strip()+'</td>')
                if l == 'Anomalous slope':
                    file.write('<td>--</td><td>--</td>')
                file.write('</tr>\n')
                count += 1

            file.write('</table>\n</div><br>\n')

            # Now write an analysis of anomalous signal
            slope = float(results['anom_slope'][0])
            flag = False

            file.write('<div align="left">')
            file.write('<h3 class="green">Analysis for anomalous signal.</h3>\n')
            file.write('<pre>An anomalous slope > 1 may indicate the presence '
                       + 'of anomalous signal.\n')
            file.write('This data set has a anomalous slope of %s.\n'
                       % results['anom_slope'][0])
            if slope > 1.1:
                file.write('Analysis of this data set indicates the presence '
                           + 'of a significant anomalous signal.\n')
                flag = True
            elif slope > 1.0:
                file.write('Analysis of this data set indicates either a weak '
                           + 'or no anomalous signal.\n')
                flag = True
            else:
                file.write('Analysis of this data set indicates no detectable '
                           + 'anomalous signal.\n')

            file.write('</table>\n</div>\n')

            #now write the credits
            file.write('<div align="left"><pre>\n')
            file.write('RAPD used the following programs for merging datasets:\n')
            file.write('  pointless  -  Scaling and Assessment of Data Quality, Philip Evans, Acta Cryst D 62 72-82.\n')
            file.write('  rebatch  -  "The CCP4 Suite: Programs for Protein Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('  mtzutils  -  "The CCP4 Suite: Programs for Protein Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('  sortmtz  -  "The CCP4 Suite: Programs for Protein Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('  scala  -  Evans, P.R. (1997) Proceedings of CCP4 Study Weekend\n')
            file.write('  truncate  -  French G.S. and Wilson K.S. Acta. Cryst. (1978), A34, 517.\n')
            file.write('  freerflag  -  "The CCP4 Suite: Programs for Protein Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('  mtz2various  -  "The CCP4 Suite: Programs for Protein Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('\n')
            file.write('</pre></div></body>')

            return(parseHTML, results)

    def makeLongResults(self,logs):
        """
        Grab the contents of passed-in files and put them in a php file
        """
        self.logger.debug('makeLongResults %s' % str(logs))

        results = {}

        #Start constructing the parsed results html file
        longHTML = 'merge_long_results.php'

        with open(longHTML, 'w') as file:
            file.write('''<?php
//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);

session_cache_limiter();
session_start();

require('/var/www/html/rapd/login/config.php');
require('/var/www/html/rapd/login/functions.php');

if(allow_user() != "yes")
{
    if(allow_local_data($_SESSION[data]) != "yes")
    {
        include ('/login/no_access.html');
        exit();
    } else {
        $local = 1;
    }
} else {
    $local = 0;
}
?>
<head>
<!-- Inline Stylesheet -->
<style type="text/css"><!--
    body {font-size: 17px; }
    table.integrate td, th {border-style: solid;
                   border-width: 2px;
                   border-spacing: 0;
                   border-color: gray;
                   padding: 5px;
                   text-align: center;
                   height: 2r10px;
                   font-size: 15px; }
    table.integrate tr.alt {background-color: #EAF2D3; }
--></style>
</head>
<body>
<align="left"><pre>\n''')

            for log in logs:

                file.write(log)

                for in_line in open(log):
                    file.write(in_line)

                file.write('<br>\n')

            file.write('</pre></div></body>')

            return(longHTML)

    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data
        """

        self.logger.debug('SimpleMerge::postprocess')

        os.remove('info.log')
        self.results['status'] = 'SUCCESS'
        self.command.append(self.results)
        #send the results back to the Core
        self.sendBack2(self.command)


    def clean_fs(self, dir):
        '''
        Cleans up the filesystem and make the downloadable file
        '''
        self.logger.debug('clean_fs')
        label = ('smerge')
        try:
            os.mkdir('simplemerge_files')
        except:
            pass
        """
        try:
            os.system('mv *_prep.mtz %s_prep.mtz' % label)
        except:
            pass
        """
        os.system('mv sorted.mtz %s_sortedMergable.mtz' % label)
        os.system('mv freer.mtz %s_freer.mtz' % label)
        os.system('mv native.sca %s_native.sca' % label)
        os.system('mv anomalous.sca %s_anomalous.sca' % label)
        os.system('mv scaled.mtz %s_scaled.mtz' % label)
        os.system('mv scala1.log %s_scaled.log' % label)
        os.system('mv freer.log %s_freer.log' % label)
        os.system('tar -cjf %s.tar.bz2 *.sca *.mtz *.log' % label)
        work_dir = self.dirs['work']
        file_base = os.path.join(work_dir, label)
        int_files = {'reference' : file_base + '_prep.mtz',
                     'mergable' : file_base + '_sortedMergable.mtz',
                     'mtzfile' : file_base + '_freer.mtz',
                     'anomalous_sca' : file_base + '_anomalous.sca',
                     'native_sca' : file_base + '_native.sca',
                     'scala_log' : file_base + '_scala.log',
                     'downloadable' : file_base + '.tar.bz2'}
        return(int_files)

    def run_analysis (self, data, dir):
        """
        Runs xtriage and other anlyses on the integrated data.
        """
        self.logger.debug('SimpleMerge::run_analysis')
        analysis_dir = os.path.join(dir, 'analysis')
        if os.path.isdir(analysis_dir) == False:
            os.system('mkdir %s' % analysis_dir)
        try:
            pdb_input = []
            pdb_dict = {}
            pdb_dict['dir'] = analysis_dir
            pdb_dict['data'] = data
            pdb_dict['control'] = self.controller_address
            pdb_dict['process_id'] = self.process_id
            pdb_input.append(pdb_dict)

            self.logger.debug('SimpleMerge::run_analysis::pdb_input')
            self.logger.debug(pdb_input)
            try:
                T = AutoStats(pdb_input, self.logger)
            except:
                self.logger.debug('    Execution of AutoStats failed')
            #T = AutoStats(pdb_input,self.logger)
            #T.join()

        except:
            self.logger.exception('ERROR in run_analysis')
            #pass
        #return('SUCCESS')

class TestApplications(unittest.TestCase):

    #The following check for functioning of the given programs
    def test_pointless(self):
        output0 = subprocess.Popen('pointless', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        result = False
        for line in output0.stdout:
            if 'No HKLIN filename given' in line:
                result = True
                break
        self.assertTrue(result)

    def test_rebatch(self):
        output0 = subprocess.Popen('rebatch', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        result = False
        for line in output0.stdout:
            if 'REBATCH:  *** Failed to open HKLIN file ***' in line:
                result = True
                break
        self.assertTrue(result)

    def test_mtzutils(self):
        output0 = subprocess.Popen('mtzutils', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        time.sleep(1)
        output0.kill()
        result = False
        for line in output0.stdout:
            if 'MTZUTILS' in line:
                result = True
                break
        self.assertTrue(result)

    def test_sortmtz(self):
        output0 = subprocess.Popen('sortmtz', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        time.sleep(1)
        output0.kill()
        result = False
        for line in output0.stdout:
            if 'SORTMTZ' in line:
                result = True
                break
        self.assertTrue(result)

    def test_scala(self):
        output0 = subprocess.Popen('scala', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        result = False
        for line in output0.stdout:
            if 'Scala:  *** Failed to open HKLIN file ***' in line:
                result = True
                break
        self.assertTrue(result)

    def test_truncate(self):
        output0 = subprocess.Popen('truncate', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        time.sleep(1)
        output0.kill()
        result = False
        for line in output0.stdout:
            if 'TRUNCATE' in line:
                result = True
                break
        self.assertTrue(result)

    def test_freerflag(self):
        output0 = subprocess.Popen('freerflag', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        time.sleep(2)
        output0.kill()
        result = False
        for line in output0.stdout:
            if 'FREERFLAG' in line:
                result = True
                break
        self.assertTrue(result)

    def test_mtz2various(self):
        output0 = subprocess.Popen('mtz2various', shell = True, stdout = subprocess.PIPE,stderr = subprocess.STDOUT)
        time.sleep(1)
        output0.kill()
        result = False
        for line in output0.stdout:
            if 'MTZ2VARIOUS' in line:
                result = True
                break
        self.assertTrue(result)


class TestPipeline(unittest.TestCase):

    def setUp(self):
        #set up logging
        self.LOG_FILENAME = '/tmp/rapd_test_simplemerge.log'
        try:
            os.unlink(self.LOG_FILENAME)
        except:
            pass
        # Set up a specific logger with our desired output level
        logger = logging.getLogger('RAPDLogger')
        logger.setLevel(logging.DEBUG)
        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(
                  self.LOG_FILENAME, maxBytes=1000000, backupCount=5)
        #add a formatter
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        #Make it a class level variable
        self.logger = logger
        #Make and move to test directory
        try:
            os.mkdir("test_simplemerge")
        except:
            print "Exception making directory test_simplemerge."
        os.chdir("test_simplemerge")

    def test_pipeline(self):
        S = SimpleMerge(['SMERGE',{'work':'./'},{'original':{'merge_file':'../test_data/1_mergable.mtz'},'secondary':{'merge_file':'../test_data/2_mergable.mtz'},'repr':'test','process_id':0},None],self.logger)
        S.join()
        log = open(self.LOG_FILENAME,"r").readlines()
        result = False
        for line in log:
            if ("finishData in_file: scaled.mtz" in line):
                result = True
                break
        self.assertTrue(result)

    def tearDown(self):
        os.chdir("../")
        shutil.rmtree("./test_simplemerge/")


if __name__ == '__main__':

    """
    # Unit Tests
    #unittest.main()
    #TestSuite = unittest.TestSuite()
    #TestSuite.addTest(TestApplications('test_pointless'))
    #TestSuite.addTest(TestPipelines('test_pipeline'))
    suite = unittest.TestLoader().loadTestsFromTestCase(TestApplications)
    unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPipeline)
    unittest.TextTestRunner(verbosity=2).run(suite)
    """

    # Run on "real" data
    #set up logging
    LOG_FILENAME = '/tmp/rapd_merge.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    S = SimpleMerge(('SMERGE',{'work':'./'},{'original':{'merge_file':'Se_Rv1219c_177_mergable.mtz'},'secondary':{'merge_file':'Se_Rv1219c_179_mergable.mtz'},'repr':'test'},None),logger)

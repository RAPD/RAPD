'''
Created Oct. 8, 2009
By David Neau

Distributed under the terms of the GNU General Public License.

This file is part of RAPD

RAPD is a free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 3 of the license,
or (at your option) any later version.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''

import os
import os.path
import socket
import threading
import multiprocessing
from rapd_communicate import Communicate


class Xia(multiprocessing.Process,Communicate):
    """
    This is a class for RAPD's data integration module.
    It uses the programs mosflm, pointless, and scala

    __init__ is merely used to stow variables passed in,
    to initialize the process, and to start the process.

    run is used to orchestrate events
    """

    def __init__(self,input,logger,verbose=True):
        """
        Initialize the Integrate process

        input is whatever is passed in
        pipe is the communication back to the calling process
        verbose is to set the level of output
        """
        if verbose:
            print 'Xia::_init__'

        self.input = input
        self.verbose = verbose
        self.controller_address = self.input[-1]

        self.results = { 'status' : 'Error' }

        self.xiaSum = {}

        # Setup paths to programs
        self.xia2 = '/gpfs1/users/necat/rapd/programs/xia2/Applications/xia2'
        self.xdsstat = '/gpfs1/users/necat/rapd/programs/xdsstat'

        multiprocessing.Process.__init__(self,name='Xia')

        self.start()

    def run(self):
        if self.verbose:
            print 'Xia::run'

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the references for programs used
        """
        if self.verbose:
            print 'Xia::preprocess'
        
        # change directory to the one specified in the incoming dict
        os.makedirs(self.input[1]['work'])
        os.chdir(self.input[1]['work'])
        # initialize name of log file to be returned
        self.xiafiles = {'xia_log' : 'xia2.txt'}

    def process(self):
        """
        Things to do in the main process
        1. Check setting for beam_flip
        2. Run xia2 pipeline and check for success
        3. Parse the results of the xia2 pipeline
        4. Prepare the plots from the scala logfile
        5. Prepare the data to be sent back up the pipe
        """
        if self.verbose:
            print 'Xia::process'

        # expand the input tuple
        # command, dirs, data, settings, cluster = self.input
        command, dirs, data, settings, server = self.input

        # Check for beam_flip.
        # settings['beam_flip'] == 'True' means the x_beam and y_beam
        # are being reversed in the header, and thus need to be flipped
        # for the integration to run properly.
        if settings['beam_flip'] == 'True':
            x_beam = data['image_data']['beam_center_y']
            y_beam = data['image_data']['beam_center_x']
            data['image_data']['beam_center_y'] = y_beam
            data['image_data']['beam_center_x'] = x_beam


        # run xia2 pipeline then check for success
        scalaLog = self.xia(data['image_data'], data['run_data'], settings)
        if scalaLog != 'False':
            self.xiafiles.update({'scala_log' : scalaLog})
            xscale_log = scalaLog.replace('scala','XSCALE')
            self.xiafiles.update({'xscale_log' : xscale_log})
            parseHTML = self.parseResults()
            graphs,tables = self.parseScala(os.path.join('LogFiles',scalaLog))

            # return a mergable file
            # file_3d is the mergable file created by running the -3d pipeline
            # while file_2d is the mergable file created by running the -2d
            # pipeline.
            prefix = data['run_data']['image_prefix']
            file_3d = 'scale/SCALED_DATA_DATA.mtz'
            file_2d = 'scale/RAPD_' + prefix + '_sorted.mtz'
            mergable = 'DataFiles/' + prefix + '_mergable.mtz'
            merge_3d = os.path.join (dirs['work'], prefix, file_3d)
            merge_2d = os.path.join (dirs['work'], prefix, file_2d)

            if os.path.isfile(merge_3d):
                os.system('mv ' + merge_3d + ' ' + mergable)
                self.xiafiles.update({'mergable': prefix + '_mergable.mtz'})
            elif os.path.isfile(merge_2d):
                os.system('mv ' + merge_2d + ' ' + mergable)
                self.xiafiles.update({'mergable': prefix + '_mergable.mtz'})

	    # Pull Rd vs dose difference table if chef_1.log exists
            cheflog = 'LogFiles/' + prefix + '_chef_1.log'
            if os.path.isfile(cheflog):
                graphs,tables = self.rDvsDose(cheflog,graphs,tables)
            # Pull the plots out of the scala log file
            scalaHTML = self.scalaPlots(graphs,tables)
        else:
            parseHTML = self.parseFailure()
            self.xiafiles.update({'debug' : 'xia2-debug.txt'})
            self.xiafiles.update({'error' : 'xia2.error'})
            for key, value in self.xiafiles.iteritems():
                self.xiafiles.update({key : os.path.join(dirs['work'], value)})
            results = { 'parsed'  : parseHTML,
                        'files'   : self.xiafiles,
                        'status'  : 'Error' }
            self.results.update(results)
            return()

        if scalaHTML != 'Error':
            for key, value in self.xiafiles.iteritems():
                self.xiafiles.update({key : os.path.join(dirs['work'], value)})
            results = { 'parsed'  : parseHTML,
                        'plots'   : scalaHTML,
                        'files'   : self.xiafiles,
                        'summary' : self.xiaSum,
                        'status'  : 'SUCCESS' }
            self.results.update(results)

    def postprocess(self):
        """
        Things to do after the main process runs:
        1. Return the data through the pipe
        """
        if self.verbose:
            print 'Xia::postprocess'

        work_dir = self.input[1]['work']
        # clean up the file system
        if self.results['status'] == 'SUCCESS':
            self.clean_fs(work_dir, self.input[2]['run_data']['image_prefix'])
        # add the results to the input
        self.input.append(self.results)
        # send the data back down the pipe
        self.sendBack2(self.input)
        #self.pipe.send(self.input)

        os._exit(0)

    def PrintInfo(self):
        """
        Print the information regarding programs utilized by the process
        """
        print """RAPD Xia module developed using xia2-0.3.1.7"""

    def xia(self, image, run, settings):
        """
        controls xia2 pipeline
        """

        xinfo = run['image_prefix'] + '.xinfo'
        self.xiafiles.update({'xinfo' : xinfo})
        project = 'RAPD'
        crystal = run['image_prefix']

        # Construct the xinfo file
        content =  'BEGIN PROJECT ' + project + '\n'
        content += 'BEGIN CRYSTAL ' + crystal + '\n\n'
        # Anomalous flag always thrown
        content += 'BEGIN HA_INFO\n ATOM SE\n END HA_INFO\n\n'
        content += 'BEGIN WAVELENGTH DATA\n'
        content += 'WAVELENGTH ' + str(image['wavelength']) + '\n'
        content += 'END WAVELENGTH DATA\n'
        content += 'BEGIN SWEEP DATA\n'
        content += 'WAVELENGTH DATA\n'
        content += 'IMAGE ' + image['fullname'] + '\n'
        content += 'DIRECTORY ' + run['directory'] + '\n'
        if float(settings['x_beam']) != 0 and float(settings['y_beam']) != 0:
            content += 'BEAM ' + str(settings['x_beam']) + ' '
            content += str(settings['y_beam']) + '\n'
        else:
            content += 'BEAM ' + str(image['beam_center_x']) + ' '
            content += str(image['beam_center_y']) + '\n'
        content += 'DISTANCE ' + str(run['distance']) + '\n'
        content += 'END SWEEP DATA\n\n'
        content += 'END CRYSTAL ' + crystal + '\n'
        content += 'END PROJECT ' + project

        with open(xinfo, 'w') as file:
            file.write(content)

        # For running on cluster (gadolinium.nec.aps.anl.gov')
        host = socket.gethostname()
        if host == 'gadolinium.nec.aps.anl.gov' or 'compute-0' in host:
            run_command = 'xia2 -3dr -xparallel 16 -parallel 4 -xinfo '
        else:
            # For running on single machine with multiple processors
            run_command = 'xia2 -3dr -xparallel 4 -parallel 4 -xinfo '
        os.system(run_command + xinfo)

        # Check for indexing error, and if occurred, run 3dii mode
        last_line = open('xia2.txt','r').readlines()[-1]
        if 'error in indexing' in last_line or 'indexing failed' in last_line:
            if host == 'gadolinium.nec.aps.anl.gov' or 'compute-0' in host:
                run_command = 'xia2 -3diir -xparallel 16 -parallel 4 -xinfo '
            else:
                run_command = 'xia2 -3diir -xparallel 4 -parallel 4 -xinfo '
            os.system(run_command + xinfo)
            # Check last_line again
            last_line = open('xia2.txt','r').readlines()[-1]
        elif 'no observations run' in last_line:
            run_command = 'xia2 -2dr -parallel 4 -xinfo '
            os.system(run_command + xinfo)
            # Check last_line again
            last_line = open('xia2.txt','r').readlines()[-1]
         
        if last_line != 'Status: normal termination\n':
            print 'Xia2 failure, check logs.'
            return('False')
        else:
            # Define scala logfile for return to main process
            logfile = project + '_' + crystal + '_scala.log'
            return(logfile)

    def parseFailure (self):
        # Returns a faiure message to be displayed
        # on the summary tab of the RAPD gui

        parseHTML = 'xia_results.html'

        with open(parseHTML, 'w') as file:
            file.write("""<head>
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
<div id="container">
    <h2>Attempted data processing by XIA2.</h2>\n<br>
        <h3>Processing FAILED!</h3>
            <h4>Check "Detail" tab for more information.</h4>
</body>\n""")
        return(parseHTML)

    def parseResults (self):
        # Takes the pointless and scala logfiles
        # and creates the html file that will be passed
        # back as the parsed results

        # Read in the xia2 log file
        xia2_log = open('xia2.txt', 'r').readlines()

        # Pull out a summary of the scala results
        damage = 0
        for i,v in enumerate(xia2_log):
            if v.startswith('For'):
                table_start = i + 1
            if v.startswith('Assuming spacegroup'):
                self.xiaSum['spacegroup'] = v.split(':')[1].strip()
                startSG = i
            if 'radiation damage' in v:
                damage=i
                if v == 'Significant radiation damage detected:':
                    rD_analysis = xia2_log[i+1].split(':').strip()
                    self.xiaSum['rD_analysis'] = rD_analysis
                    if 'DOSE' in xia2_log[i+2]:
                        dose_cutoff = xia2_log[i+2].split('~').strip()
                        self.xiaSum['rD_conclusion'] = dose_cutoff
                    else:
                        self.xiaSum['rD_conclusion'] = 'ALL'
            if v.startswith('Insufficient measurements for analysis'):
                damage=i
            if v.startswith('Overall twinning score'):
                self.xiaSum['twinScore'] = v.split(':')[1].strip()
                txt1 = i+2
            if v.startswith('Unit cell'):
                unit_cell = xia2_log[i+1].strip()
                unit_cell += ' ' + xia2_log[i+2].strip()
                self.xiaSum['cell'] = unit_cell
                cell = i
            if v.startswith('mtz format'):
                tmp = xia2_log[i+1].split('/')
                mtzfile = tmp[-1].strip()
            if v.startswith('sca format'):
                tmp = xia2_log[i+1].split('/')
                scafile = tmp[-1].strip()
            if v.startswith('sca_unmerged format'):
                tmp = xia2_log[i+1].split('/')
                unmerged = tmp[-1].strip()
            if v.startswith('Processing took'):
                self.xiaSum['procTime'] = ' '.join(v.split()[2:5])

        xia2_SG = xia2_log[startSG:cell]
        xia2_summary = xia2_log[cell+9:len(xia2_log)]
        xia2_twin = xia2_log[damage:txt1]
        xia2_table = xia2_log[table_start: table_start+18]

        scaled_files = { 'mtzfile' : mtzfile,
                         'scafile' : scafile,
                         'unmerged' : unmerged }

        self.xiafiles.update(scaled_files)

        # extract summary table for returned dicts
        overall = {}
        innerShell = {}
        outerShell = {}

        tableKeys = ['high_res', 'low_res', 'completeness', 
                     'multiplicity', 'I/sigma', 'Rmerge',
                     'Rmeas(I)', 'Rmeas(I+/-)', 'Rpim(I)',
                     'Rpim(I+/-)', 'wilsonB', 'partialBias',
                     'anomComp', 'anomMult', 'anomCorr',
                     'anomSlope', 'totalObs', 'totalUnique']

        for i,v in enumerate(tableKeys):
            if v == 'wilsonB':
                overall[v] = xia2_table[i].split()[-1]
            else:
                overall[v] = xia2_table[i].split()[-3]
                innerShell[v] = xia2_table[i].split()[-2]
                outerShell[v] = xia2_table[i].split()[-1]

        self.xiaSum['overall'] = overall
        self.xiaSum['innerShell'] = innerShell
        self.xiaSum['outerShell'] = outerShell

        # Start constructing the parsed results html file
        parseHTML = 'xia_results.html'

        with open(parseHTML, 'w') as file:
            file.write("""<head>
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
<div id="container">
<h2>Data Processed by XIA2</h2>\n<br>\n""")

            spacegroupLine = '<div align="left"><pre>'
            for line in xia2_SG:
                spacegroupLine += line
            spacegroupLine += 'Unit Cell: ' + unit_cell + '\n\n'

            file.write(spacegroupLine)
            for line in xia2_twin:
                file.write(line)
            file.write('</pre></div>\n<div align="center">\n')
            file.write('<h3 class="green">Xia2 Results</h3><br>\n')
            file.write('<table class="integrate">\n')
            file.write('<tr><th></th><td>Overall</td>')
            file.write('<td>Inner Shell</td><td>Outer Shell</td></tr>\n')

            for i,line in enumerate(xia2_table):
                if ( i % 2) == 0:
                        file.write('<tr><th>')
                else:
                    file.write('<tr class="alt"><th>')
                for x, value in enumerate(line.split('\t')):
                    if x == 0:
                        file.write(value.strip() + '</th>')
                    else:
                        file.write('<td>' + value.strip() + '</td>')
                file.write('</tr>\n')

            file.write('</table>\n</div>\n<div align="left"><pre>\n')
            for line in xia2_summary:
                file.write(line)
            file.write('</pre>\n</div>\n</body>')

            return(parseHTML)
                
    def parseScala (self, logfile):
        """
        Parses the scala logfile in order
        to pull out data for graphs

        Returns a list of tuples called graphs
        and a nested list called tables:
        tuple in graphs contains:
            '<*graph title*>' , [data_labels], [table# , col#s]
            where:
                data_labels are the label for the X-axis and for any data
                table# gives a position for the table where the data is located
                col#s gives positions of the columns within the table that will
                    be plotted.

        tables contains all of the tables within the scala logfile
        such that table[n] is the nth table in the logfile
        and to read the data from table[n] you can loop as follows:
        (example would read out the 1st and 5th column of data)
        for line in table[n]:
            xValue = line[0]
            yValue = line[4]
        """

        log = open(logfile, 'r').readlines()

        # Initalize the variables that will be returned
        graphs = []
        tables = []

        # Initalize some variables to be used for parsing
        tableHeaders=[]
        label_start= ['N', 'Imax', 'l', 'h', 'k', 'Range']

        # Find and grab each table in the logfile
        for i,v in enumerate(log):
            if 'TABLE' in v:
                header = []
                data=[]
                while 'applet>' not in log[i]:
                    # Skip blank lines
                    if log[i] == '\n':
                        i+=1
                    # Pull out header information for table
                    elif 'GRAPHS' in log[i]:
                        while log[i] != '\n' and log[i].split()[0] != '$$':
                            header.append(log[i].strip())
                            i+=1
                    # If first character on line is a number, assume it's data.
                    elif log[i].strip()[0].isdigit():
                        data.append(log[i].split())
                        i+=1
                    else:
                        for start in label_start:
                            if log[i].strip().startswith(start):
                                header.append(log[i].strip())
                        i+=1
                tableHeaders.append(header)
                tables.append(data)

        # Parse the table headers to get titles, labels, and positions.
        for tableNum, head in enumerate(tableHeaders):
            collabels = head[-1].split()
            ycols=[]
            title=''
            for line in head:
                if ':' in line:
                    for i in line.split(':'):
                        if len(i) > 2 and 'GRAPHS' not in i and '$$' not in i:
                            if i[0].isdigit() and ',' in i:
                                tmp = i.split(',')
                                xcol = int(tmp[0])-1
                                for x in range (1, len(tmp), 1):
                                    ycols.append(int(tmp[x])-1)
                            else:
                                title = i.strip()
                        if title and ycols:
                            ylabels = []
                            xlabel = collabels[xcol]
                            # for plots vs resolution:
                            # change xlabel from 1/d^2 or 1/resol^2 to Dmin
                            if xlabel == '1/d^2' or xlabel == '1/resol^2':
                                xlabel = 'Dmin (A)'
                            for y in ycols:
                                ylabels.append(collabels[y])
                            graph = title, xlabel, ylabels, xcol, ycols, tableNum
                            # Reset the variable ycols and title
                            ycols =[]
                            title=''
                            graphs.append(graph)

        return(graphs, tables)

    def scalaPlots(self, graphs, tables):
        """
        generate plots html file from scala results
        """

        # plotThese contains a list of graph titles that you want plotted 
        # additional plots may be requested by adding the title (stripped
        # of leading and trailing whitespace) to plotThese.
        plotThese = {
                     # 'Mn(k) & 0k (at theta = 0) v range' : 'Scales',
                     # 'B  v range'                        : 'Bfactor',
                     'Rmerge v Batch for all runs'       : 'R vs frame',
                     'I/sigma, Mean Mn(I)/sd(Mn(I))'     : 'I/sigma',
                     'Rmerge v Resolution'               : 'R vs Res',
                     'Average I,sd and Sigma'            : 'I vs Res',
                     'Completeness v Resolution'         : '%Comp',
                     'Multiplicity v Resolution'         : 'Redundancy',
                     'Rpim (precision R) v Resolution'   : 'Rpim',
                     'Rmeas, Rsym & PCV v Resolution'    : 'Rmeas',
                     'Rd vs. Dose difference'            : 'Rd',
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
                scala_plot += '        <li><a href="#tabs-22' + str(i) + '">' + title + '</a></li>\n'
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
            print 'Could not create scala plot html file.'
            return ('Error')

    def rDvsDose(self, file, graphs, tables):
        """
        Attempts to read from chef logfile
        Pulls our Rd vs dose difference table
        """
        try:
            log = open(file, 'r').readlines()
        except IOError:
            return(graphs, tables)

        table = []
        table_start = 0
        for i,v in enumerate(log):
            if 'R vs. DOSE' in v:
                title = 'Rd vs. Dose difference'
                xlabel = 'Dose (s)'
                ylabel = ['Rd']
                x = 0
                y = [1]
                tableNum = len(tables)
                graph = title, xlabel, ylabel, x, y, tableNum
                graphs.append(graph)
                table_start = i+3
            if table_start != 0 and v.startswith('$$'):
                table_end = i-2
                break

        for line in log[table_start:table_end]:
            table.append(line.split())

        tables.append(table)

        return(graphs,tables)
        
    def clean_fs (self, work_dir, prefix):
        """
        Removes unnecessary files after running xia2.
        Puts files to keep in working directory.
        """
        os.system('mv xia2.txt DataFiles/')
        os.system('mv LogFiles/RAPD_' + prefix + '_scala.log DataFiles/')
        os.system('mv LogFiles/RAPD_' + prefix + '_XSCALE.log DataFiles/')
        os.system('rm -f *.txt')
        os.system('rm -f xia-citations.bib')
        os.system('rm -rf ' + prefix)
        os.system('rm -rf Harvest')
        os.system('rm -rf LogFiles')
        os.system('cp DataFiles/* ' + work_dir)
        os.system('rm -rf DataFiles')

        return()

class DataHandler(threading.Thread):
    """
    Handles the data that is received from the incoming clientsocket

    Creates a new process by instantiating a subclassed multiprocessing.Process
    instance which will act on the information which is passed to it upon
    instantiation.  That class will then send back results on the pipe
    which it is passed and Handler will send that up the clientsocket.
    """
    def __init__(self,input,verbose=True):
        if verbose:
            print 'DataHandler::__init__'

        threading.Thread.__init__(self)

        self.input = input
        self.verbose = verbose

        self.start()

    def run(self):
        # Create a pipe to allow interprocess communication.
        parent_pipe,child_pipe = multiprocessing.Pipe()
        # Instantiate the integration case
        tmp = Integrate(self.input,child_pipe,True)
        # Print out what would be sent back to the RAPD caller via the pipe
        print parent_pipe.recv()


if __name__ == '__main__':
    """ Fix this
    # Construct test input
    command = 'INTEGRATE'
    dirs = { 'images' : \
             '/gpfs2/users/necat/david/Yong_July09/process/rapd/html/images',
             'data_root_dir' : '/home/dneau/RAPD_testing/mosflm/images/',
             'work' : '/gpfs1/users/necat/fmurphy/rapd/runs/Y1_bot_1_001',
             'html' : '/gpfs2/users/necat/david/Yong_July09/process/rapd/html',
             'user' : '/home/dneau/RAPD_testing/test'}
    image_data = {'osc_start' : '0.00',
                  'ID' : 'Y1_bot_1',
                  'distance' : '400.00',
                  'beam_center_x' : '153.5',
                  'beam_center_y' : '164.6',
                  'wavelength' : '0.97918',
                  'twotheta' : '0.0',
                  'ccd_image_saturation' : '65535',
                  'directory' : '/home/dneau/RAPD_testing/mosflm/images/',
                  'fullname' : \
                  '/home/dneau/RAPD_testing/mosflm/images/Y1_bot_1_001.img'}
    run_data = {'distance' : '400.0',
                'image_prefix' : 'Y1_bot',
                'run_number' : 1,
                'start' : 1,
                'time' : 1.0,
                'directory' : '/home/dneau/RAPD_testing/mosflm/images/',
                'total' : 60}
    data = {'image_data' : image_data,
            'run_data' : run_data}
    settings = {'spacegroup' : 'P3',
                'work_directory' : '/home/dneau/RAPD_testing/test/mosflm_test',
                'work_dir_override' : 'True',
                'anomalous' : 'False'}
    input = [command, dirs, data, settings]
     # Call the handler.
    T = DataHandler(input)
    """
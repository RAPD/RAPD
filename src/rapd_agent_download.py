"""
This file is part of RAPD

Copyright (C) 2010-2016, Cornell University
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

__created__ = "2010-01-20"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

"""
rapd_test_case gives an example of wrapping a very simple activity so that
one can see roughly how to structure and activity class as a new process
using the multiprocessing module and how to send the resulting data back
"""

import threading
import multiprocessing
import os
import sys
from rapd_communicate import Communicate

class Download(multiprocessing.Process,Communicate):
    """
    Module for file organization and compression to be
    used by rapd_cluster

    __init__ is merely used to stow variables passed in,
    to initialize the process, and to start the process

    run is used to orchestrate events
    """

    def __init__(self,input,logger):
        """
        Initialize.

        input - whatever is passed in
        logger - the logger
        """

        logger.info('Download::__init__')
        logger.debug(input)

        self.input   = input
        self.logger  = logger

        multiprocessing.Process.__init__(self,name='Download')

        #starts the new process
        self.start()

    def run(self):
        self.logger.debug('Download::run')

        self.preprocess()
        self.process()
        self.postprocess()


    def preprocess(self):
        """
        Things to do before the main process runs.
        """

        self.logger.debug('Download::preprocess')
        self.logger.debug(self.input)

        self.command    = self.input[0]
        self.input_dict = self.input[1]
        self.controller_address = self.input[-1]

        #download the processed data and log files
        if self.input_dict['request_type'] == 'downproc':
            #save type
            self.type = 'downproc'
            #target diectory - files here will be compressed as well
            #for the new-style integrations
            if self.input_dict['download_file']:
                self.download_file = self.input_dict['download_file']
                self.input[1]['archive'] = self.input_dict['download_file']
            #old-style XIA2
            else:
                #the source directories and files
                self.source_dirs  =  self.input_dict['source_dir']
                self.source_files =  self.input_dict['image_files']
                #target diectory - files here will be compressed as well
                self.target_dir    = self.input_dict['work_dir']
                #the target files - starting and final
                self.start_file   = os.path.join(self.target_dir,'data_'+str(self.input_dict['repr'])+'.tar')
                self.target_file  = os.path.join(self.target_dir,'data_'+str(self.input_dict['repr'])+'.tar.bz2')
                #save the target file location for return
                self.input[1]['archive'] = self.target_file

        elif (self.input_dict['request_type'] == 'downsad'):
            #save type
            self.type = 'downsad'
            self.download_file = self.input_dict['download_file']
            self.input[1]['archive'] = self.input_dict['download_file']

        elif (self.input_dict['request_type'] == 'downshelx'):
            #save type
            self.type = 'downshelx'
            self.download_file = self.input_dict['download_file']
            self.input[1]['archive'] = self.input_dict['download_file']

        elif (self.input_dict['request_type'] == 'downmad'):
            #save type
            self.type = 'downmad'
            self.download_file = self.input_dict['download_file']
            self.input[1]['archive'] = self.input_dict['download_file']

        elif (self.input_dict['request_type'] == 'downmadshelx'):
            #save type
            self.type = 'downmadshelx'
            self.download_file = self.input_dict['download_file']
            self.input[1]['archive'] = self.input_dict['download_file']

        elif (self.input_dict['request_type'] == 'download_mr'):
            #save type
            self.type = 'download_mr'
            self.download_file = self.input_dict['download_file']
            self.input[1]['archive'] = self.input_dict['download_file']

        elif (self.input_dict['request_type'] == 'downsadcell'):
            #save type
            self.type = 'downsadcell'
            self.download_file = self.input_dict['download_file']
            self.input[1]['archive'] = self.input_dict['download_file']

        elif (self.input_dict['request_type'] == 'download_int'):
            #save type
            self.type = 'download_int'
            self.download_file = self.input_dict['download_file']
            self.input[1]['archive'] = self.input_dict['download_file']


    def process(self):
        """
        Setup extra parameters for Labelit.
        """
        if self.type == 'downproc':
            #new-style
            if (self.download_file):
                pass
            #old-syle XIA2 pipeline results
            else:
                #archive the files one by one
                counter = 0
                for dir,file in zip(self.source_dirs,self.source_files):
                    if counter == 0:
                        command = 'tar -C '+dir+' -cf '+self.start_file+' '+file
                        counter += 1
                    else:
                        command = 'tar -C '+dir+' -rf '+self.start_file+' '+file
                    self.logger.debug(command)
                    os.system(command)
                #now bzip the tar file
                command = 'bzip2 -qf '+self.start_file
                self.logger.debug(command)
                os.system(command)


    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data through the pipe
        """
        self.logger.debug('Download::postprocess')

        try:
            self.sendBack2(self.input)
        except:
            self.logger.debug('Could not send results to RAPD core.')
        sys.exit()

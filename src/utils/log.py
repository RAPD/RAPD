'''
This file is part of RAPD

Copyright (C) 2016-2023 Cornell University
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
'''

__created__ = '2016-01-28'
__maintainer__ = 'Frank Murphy'
__email__ = 'fmurphy@anl.gov'
__status__ = 'Development'

import functools
import logging, logging.handlers
import os
import sys
from typing import Any, Callable, Union

# RAPD imports
import utils.text as text

# str || int type
def str_int(arg:Union[int, str]) -> None:
    print(arg)


def verbose_print(arg: Any,
                  level: str_int = 3,
                  color: str ='default',
                  verbosity: int = 3,
                  no_color: bool = False,
                  progress: bool = False,
                  progress_fd: int = 1,
                  newline: bool = True,
                  close: bool = True) -> None:
    '''Print to terminal window screened by verbosity setting

    Keyword arguments:
    arg -- object to be printed (default None)
    level -- the importance of the printing job (default 2)
    verbosity -- the value level must be less than or equal to to print (default 2)
    no_color
    progrss
    progreess_fd
    newline
    close

    levels:
    10 - silent: only print JSON at the end if in json run mode (outside terminal printer system)
    5 - alert
    4 - error
    3 - warning
    2 - info
    1 - debug
    progress - this will print the accompanying number to the terminal if progress was passed in as
               true when setting up the terminal printer
    '''

    # Have progress
    if level == 'progress':

        # Make sure we are writing a number
        if not isinstance(arg, int):
            raise TypeError('a number is required')

        # To terminal
        if progress:
            sys.stdout.write('%DONE={}\n'.format(arg))
            sys.stdout.flush()

        # To fd
        if progress_fd:
            progress_fd.write('%DONE={}\n'.format(arg))
            progress_fd.flush()
        
        # Finished
        return True

    # Cast everything to a string
    if not isinstance(arg, str):
        arg = str(arg)

    if level >= verbosity:
        if no_color:
            color = False
        if newline:
            if color:
                if close:
                    print(text.color(color) + arg + text.stop)
                else:
                    print(text.color(color) + arg)
            else:
                print(arg)
        else:
            if color:
                if close:
                    sys.stdout.write(text.color(color) + arg + text.stop)
                else:
                    sys.stdout.write(text.color(color) + arg)
            else:
                sys.stdout.write(arg)
            sys.stdout.flush()

def get_terminal_printer(verbosity: int = 3,
                         no_color: bool = False, 
                         progress: bool = False,
                         progress_fd: int = False) -> Callable:
    '''Returns a terminal printer

    Keyword arguments:
    verbosity   -- threshold to print (default 3)
    progress    -- enable progress printing
    progress_fd -- enable progress printing and write to an fd
    '''

    if progress_fd:
        progress_fd = os.fdopen(int(progress_fd), 'w')

    terminal_print = functools.partial(verbose_print,
                                       verbosity=verbosity,
                                       no_color=no_color,
                                       progress=progress,
                                       progress_fd=progress_fd)
    return terminal_print


def get_logger(logfile_dir: str = '/var/log',
               logfile_id: str = 'rapd',
               level: int = 3,
               console: bool = False) -> logging.Logger:
    '''Returns a logger instance

    Keyword arguments:
    logfile_dir -- Directory in which log will be written (default '/var/log')
    logfile_id -- Tag for the logfile to be written (default 'rapd' >> rapd.log)
    level -- Logging level CRITICAL=50, DEBUG=10 (default 10)
    console -- If True, create a console printing too
    '''

    # print 'get_logger logfile_dir:%s logfile_id:%s level:%d' % (logfile_dir, logfile_id, level)

    # Make sure the logfile_dir exists
    if not os.path.exists(logfile_dir):
        os.makedirs(logfile_dir)

    # Set up file name
    log_filename = os.path.join(logfile_dir, logfile_id+'.log')
    # print 'Log file: %s' % log_filename

    # Add the log message handler to the logger
    file_handler = logging.handlers.RotatingFileHandler(log_filename,
                                                        maxBytes=5000000,
                                                        backupCount=5)

    # create console handler and set level to debug
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

    # add a formatter
    formatter = logging.Formatter('%(asctime)s %(filename)s.%(funcName)s %(lineno)s - %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    if console:
        console_handler.setFormatter(formatter)

    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(level)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    if console:
        logger.addHandler(console_handler)

    logger.debug('Logging started to %s' % log_filename)

    return logger

if __name__ == '__main__':

    print('--------------------')
    print(' rapd2 utils/log.py ')
    print('--------------------')

    print('Test console printeres of varying verbosities')
    for verbosity in (1,2,3,4,5,10):
        print(f'Creating printer with verbosity {verbosity}')
        PRINTER = get_terminal_printer(verbosity=verbosity)
        for level in (1,2,3,4,5,10):
            PRINTER(f'  Testing level {level}', level=level)


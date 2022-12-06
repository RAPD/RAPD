'''Helpers for printing out credits for software use'''

'''
This file is part of RAPD

Copyright (C) 2017-2023, Cornell University
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

__created__ = '2017-04-24'
__maintainer__ = 'Frank Murphy'
__email__ = 'fmurphy@anl.gov'
__status__ = 'Development'

# Standard imports
import sys
from typing import Iterable

HEADER = '\nRAPD depends on the work of others'

AIMLESS = [
    'Aimless',
    'Reference: Evans PR (2006) Acta Cryst. D62:72-82.',
    'Website: http://www.mrc-lmb.cam.ac.uk/harry/pre/aimless.html\n'
]

BEST = [
    'BEST',
    'Reference: Bourenkov GP and Popov AN (2006) Acta Cryst. D62:58-64',
    'Website: http://www.embl-hamburg.de/BEST/\n'
]

CCP4 = [
    'CCP4',
    'Reference: Acta Cryst. D50:760-763',
    'Website: http://www.ccp4.ac.uk\n'
]

CCTBX = [
    'CCTBX - Computational Crystallography Toolbox',
    'Reference: Grosse-Kunstleve et al (2002) J. Appl. Cryst. 35:126-136',
    'Website: https://cctbx.github.io/\n'
]

MOLREP = [
    'Molrep',
    'Reference: Vagin A and Teplyakov A (1997) J. Appl. Cryst. 30:1022-1025',
    'Website: http://www.ccp4.ac.uk/html/molrep.html\n'
]

MOSFLM = [
    'Mosflm',
    'Reference: Leslie AGW (1992) Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No.\
 26',
    'Website: http://www.mrc-lmb.cam.ac.uk/harry/mosflm/\n'
]

PHASER = [
    'Phaser',
    'Reference: McCoy AJ, et al. (2007) J. Appl. Cryst. 40:658-674',
    'Website: http://www.phenix-online.org/documentation/phaser.htm\n'
]

PHENIX = [
    'Phenix',
    'Reference: Sauter NK, et al. (2004) J. Appl. Cryst. 37:399-409',
    'Website:   http://adder.lbl.gov/labelit/\n'
]

POINTLESS = [
    'Pointless',
    'Reference: Evans PR (2006) Acta Cryst. D62:72-82.',
    'Website: http://www.mrc-lmb.cam.ac.uk/harry/pre/pointless.html\n'
]

XDS = [
    'XDS',
    'Reference: Kabsch W (2010) Acta Cryst. D66:125-132',
    'Website: http://xds.mpimf-heidelberg.mpg.de/\n'
]

POINTLESS = [
    'Pointless',
    'Reference: Evans PR (2006) Acta Cryst. D62:72-82.',
    'Website: http://www.mrc-lmb.cam.ac.uk/harry/pre/pointless.html\n'
]

RADDOSE = [
    'Raddose',
    'Reference: Paithankar, et al. (2009) J. Synch. Rad. 16:152-162',
    'Website:   http://biop.ox.ac.uk/www/garman/lab_tools.html/\n',
]

XDS = [
    'XDS',
    'Reference: Kabsch W (2010) Acta Cryst. D66:125-132',
    'Website: http://xds.mpimf-heidelberg.mpg.de/\n'
]

MAIN_MODULE = sys.modules[__name__]

def get_credit(requested_program: str = 'PHENIX'):
    '''Return credit lines for requested program'''
    return getattr(MAIN_MODULE, requested_program.upper())

def get_credits_text(programs: Iterable = (), indent: str = ''):
    '''Return text for printing out credits'''
    return_text = ''
    for program in programs:
        raw_lines = get_credit(program.upper())
        for line in raw_lines:
            return_text += (indent + line + '\n')
    return return_text

if __name__ == '__main__':

    print('------------------------')
    print(' rapd2 utils/credits.py ')
    print('------------------------')

    print(get_credits_text(('xds',)))
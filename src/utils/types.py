'''
This file is part of RAPD

Copyright (C) 2022-2023 Cornell University
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

__created__ = '2022-12-07'
__maintainer__ = 'Frank Murphy'
__email__ = 'fmurphy@anl.gov'
__status__ = 'Development'

from collections import OrderedDict
import json as system_json
from logging import Logger
from pprint import pprint
import sys
from typing import Callable, Union

from bson import json_util
from bson.objectid import ObjectId

# Definitions for type hints
# bool || Callable type
def bool_callable(arg:Union[bool, Callable]) -> None:
    print(arg)

# bool || dict type
def bool_dict(arg:Union[bool, dict]) -> None:
    print(arg)

# bool || int type
def bool_int(arg:Union[bool, int]) -> None:
    print(arg)

# bool || logger type
def bool_logger(arg:Union[bool, Logger]) -> None:
    print(arg)


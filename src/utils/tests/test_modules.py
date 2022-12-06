import utils.modules as modules

import pytest

def test_load_module_empty() -> None:
    '''Test calling load_module with no arguments'''
    with pytest.raises(TypeError) as exc_info:
        modules.load_module()  


def test_load_module() -> None:
    '''Test calling load_module with simple module'''

    credit_module_1 = modules.load_module(seek_module='credits', directories='utils')
    assert credit_module_1.XDS[0] == 'XDS'

    credit_module_2 = modules.load_module(seek_module='credits', directories=('utils',))
    assert credit_module_2.XDS[0] == 'XDS'
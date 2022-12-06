import utils.xutils as xutils

IMAGE_FILE = 'e_3_PAIR_0_0002.cbf'
MTZ_FILE = 'thaum1_01s-01d_1_mergable.mtz'

def test_get_mtz_info() -> None:
    '''Test get_mtz_info function'''
    assert xutils.get_mtz_info(MTZ_FILE) == ('P 41 21 2', [57.887, 57.887, 150.307, 90.0, 90.0, 90.0], 503664.484)

# def test_dumps() -> None:
#     '''Test the dumps function'''
#     obj = {'1':True}
#     assert text.json.dumps(obj) == '{"1": true}'

# def test_loads() -> None:
#     '''Test the loads function'''
#     assert text.json.loads('{"1": true}') == {'1':True}
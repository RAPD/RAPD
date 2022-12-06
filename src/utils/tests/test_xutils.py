
import utils.xutils as xutils


IMAGE_FILE = 'e_3_PAIR_0_0002.cbf'
MTZ_FILE = 'thaum1_01s-01d_1_mergable.mtz'

def test_get_mtz_info() -> None:
    '''Test get_mtz_info function'''
    assert xutils.get_mtz_info(MTZ_FILE) == ('P 41 21 2', [57.887, 57.887, 150.307, 90.0, 90.0, 90.0], 503664.484)

def test_date_adsc_to_sql() -> None:
    '''Test date_adsc_to_sql'''
    assert xutils.date_adsc_to_sql('Tue Dec 6 00:00:00 2022') == '2022-12-06T00:00:00'

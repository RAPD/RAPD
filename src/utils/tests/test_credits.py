import utils.credits as credits

def test_header() -> None:
    '''Test header value'''
    assert credits.HEADER == '\nRAPD depends on the work of others'

def test_get_credit() -> None:
    '''Test get_credit function'''
    x = credits.get_credit('xds')
    assert x[0] == 'XDS'

def test_get_credits_text() -> None:
    '''Test get_credits_text function'''
    x = credits.get_credits_text(programs=('xds',), indent=' ')
    assert x.startswith(' XDS')
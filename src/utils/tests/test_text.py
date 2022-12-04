import utils.text as text

def test_color() -> None:
    '''Test color return'''
    assert text.color() == '\033[39m'
    assert text.color('red') == '\033[31m'

def test_dumps() -> None:
    '''Test the dumps function'''
    obj = {'1':True}
    assert text.json.dumps(obj) == '{"1": true}'

def test_loads() -> None:
    '''Test the loads function'''
    assert text.json.loads('{"1": true}') == {'1':True}
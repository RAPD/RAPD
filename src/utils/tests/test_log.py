import utils.log as log

def test_terminal_printer(capsys) -> None:
    '''Test the terminal_printer at varying verbosity and level'''
    
    for verbosity in (1,2,3,4,5,10):
        PRINTER = log.get_terminal_printer(verbosity=verbosity)
        for level in (1,2,3,4,5,10):
            PRINTER(f'  Testing level {level}', level=level)
            captured = capsys.readouterr()
            if level >= verbosity:
                assert captured.out == f'\x1b[39m  Testing level {level}\x1b[0m\n'
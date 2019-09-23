import pep8 as _pep8

def pep8(line, cell):
    lines = cell.splitlines(True)
    lines[-1] += '\n'
    fchecker = _pep8.Checker(lines=lines,
                             show_source=True)
    report = fchecker.check_all()

def load_ipython_extension(ipython):
    ipython.register_magic_function(pep8, magic_kind='cell')
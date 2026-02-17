#class for printer access
from escpos.printer import Dummy

def testPrinter():
    p = Dummy()
    p.text("printer test 1\n")
    p.text("printer test 2\n")
    p.text("printer test 3\n")
    print(p.output)

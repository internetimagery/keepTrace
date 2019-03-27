
import unittest
import traceback

from keepTrace.utils import parse_tracebacks

def stack():
    trace()
def trace():
    leads()
def leads():
    here()
def here():
    error()
def error(msg=""):
    raise RuntimeError(msg)

class TestParse(unittest.TestCase):

    def assertParse(self):
        real_error = traceback.format_exc()
        for mangled in [ # Mangle traceback in common ways
            ("# "+l for l in real_error.split("\n")), # Commented traceback
            (l.strip() for l in real_error.split("\n"))]: # Indent stripped traceback
            parsed_error = "".join(traceback.format_exception(*list(parse_tracebacks(mangled))[0]))
            self.assertEqual(real_error, parsed_error)

    def test_simple(self):
        try:
            stack()
        except RuntimeError:
            self.assertParse()


if __name__ == '__main__':
    unittest.main()

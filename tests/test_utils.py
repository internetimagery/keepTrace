
import sys
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
def recurse():
    recurse()
def syntax():
    exec("error in")

class TestParse(unittest.TestCase):

    def assertParse(self):
        real_error = traceback.format_exc().strip()
        for i, mangled in enumerate([ # Mangle traceback in common ways
            (l for l in real_error.split("\n")), # Normal!
            ("# "+l for l in real_error.split("\n")), # Commented traceback
            (l.strip() for l in real_error.split("\n")), # Indent stripped traceback
            ]):
            parsed_error = "".join(traceback.format_exception(*list(parse_tracebacks(mangled))[0])).strip()
            if sys.exc_info()[0] == SyntaxError and i == 2:
                continue # Stripped syntax error is impossible to fully parse, as information is lost from carret whitespace
            self.assertEqual(real_error, parsed_error)

    def test_simple(self):
        try:
            stack()
        except RuntimeError:
            self.assertParse()

    def test_recurse(self):
        try:
            recurse()
        except Exception:
            self.assertParse()

    def test_syntax(self):
        try:
            syntax()
        except Exception:
            self.assertParse()

    # Now for some edge cases!!

    def test_variable(self):
        try: # This line resembles "Exception" when traceback is stripped of indentation
            i_do_not_exist
        except NameError:
            self.assertParse()

    def test_dict(self):
        try: # This line resembles "Exception: value" when traceback is stripped of indentation
            {
                NameError: error()
            }
        except RuntimeError:
            self.assertParse()


if __name__ == '__main__':
    unittest.main()

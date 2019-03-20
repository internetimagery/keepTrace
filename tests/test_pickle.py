import os
import sys
import os.path
import unittest
import traceback
try:
    import cPickle as pickle
except ImportError:
    import pickle

import keepTrace

root = __file__
if root[-1] == "c": # pyc file
    root = root[:-1]
abs_root = os.path.abspath(root)

def error():
    raise RuntimeError()

def recurse(num):
    if num > 0:
        recurse(num-1)

def syntax():
    eval("for this is")

def bad_restore(data):
    raise RuntimeError("Oh no!")

class BadBefore(object):
    def __reduce__(self):
        return I_do_not_exist, (some_missing_data, )

class BadAfter(object):
    def __reduce__(self):
        return bad_restore, (123,)

class TestPickle(unittest.TestCase):

    def assertTrace(self, exc):
        data = pickle.dumps(exc)
        restored = pickle.loads(data)
        source_trace = "".join(traceback.format_exception(*exc)).replace(root, abs_root)
        expect_trace = "".join(traceback.format_exception(*restored))
        self.assertEqual(source_trace, expect_trace)

    def test_roundtrip(self):
        keepTrace.init()
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_infinite_depth(self):
        keepTrace.init(depth=-1)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_pickler(self):
        keepTrace.init(pickler=pickle.dumps)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_full(self):
        keepTrace.init(pickle, -1)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_no_source(self):
        keepTrace.init(include_source=False)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_recursion(self):
        keepTrace.init()
        sys.setrecursionlimit(200)
        try:
            recurse(sys.getrecursionlimit()*2)
        except Exception:
            pickle.loads(pickle.dumps(sys.exc_info()))

    def test_fake_recursion(self):
        keepTrace.init()
        try:
            recurse(sys.getrecursionlimit()/2)
        except Exception:
            self.assertTrace(sys.exc_info())

    def test_syntax(self):
        keepTrace.init()
        try:
            syntax()
        except SyntaxError:
            self.assertTrace(sys.exc_info())

    def test_bad_object(self):
        keepTrace.init(pickler=pickle.dumps)
        try:
            bb = BadBefore()
            ba = BadAfter()
            error()
        except Exception:
            self.assertTrace(sys.exc_info())


if __name__ == '__main__':
    unittest.main()

# MIT License
#
# Copyright (c) 2019 Jason Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import types
import logging
try:
    import __builtin__ as builtins
except ImportError:
    import builtins

LOG = logging.getLogger(__name__)

def parse_tracebacks(reader):
    """
    Attempt to grab all tracebacks from file-like object. Possibly a log file etc.
    Build a usable error tuple object out of it (obviously the traceback will be lacking local variables etc).
    Passing the object to traceback.format_exception should result in the same output as the initial exception.

    Args:
        reader (typing.TextIO): Reader/line-iterator.

    Returns:
        types.TracebackType: Actually a mock traceback. Still usable in traceback formatting and in debuggers.
    """
    # Mock object to become our traceback objects
    mock = type("mock", (object,), {
        "__init__":  lambda s, **d: s.__dict__.update(d),
        "__class__": property(lambda s: s._class),
        "__repr__": lambda s: s._repr})
    # The lines we care about
    # TODO: Put all into one regex? Faster?
    reg_file = re.compile(r"(  )?File \"(?P<filename>[^\"]+)\", line (?P<lineno>\d+)(, in (?P<name>.+))?")
    reg_err = re.compile(r"(?P<error>[<>\w\.]+)(: (?P<value>.+))?$")
    reg_repeat = re.compile(r"(  )?\[Previous line repeated (?P<repeats>\d+) more times\]")
    # TODO: support recursion error traceback python3
    frames = offset = syntax_pack = None # Special treatment for syntax errors
    while True: # Allow modification of reader on the fly. Regular "for var in reader" doesn't allow that.
        line = next(reader)
        header = line.find("Traceback (most recent call last):")
        if header != -1: # We have started a traceback.
            frames, offset = [], header
        elif frames is not None: # We are currently handling a traceback
            line = line[offset:] # Keep all lines at the same indent
            err_line = reg_err.match(line)
            file_line = reg_file.match(line)
            repeat_line = reg_repeat.match(line)
            if file_line: # File "path", line 123, in name
                if not file_line.group("name"): # We have a SyntaxError
                    # msg, (filename, lineno, offset, badline) = value.args
                    bad_line = next(reader)[offset:]
                    bad_offset = next(reader)[offset:].find("^") + 1
                    if bad_offset == 1: # If carret has been stripped of whitespace, offset information is lost (but it could be legit still)
                        LOG.warning("SyntaxError traceback may have lost its offset information.")
                    syntax_pack = (
                        file_line.group("filename"),
                        int(file_line.group("lineno")),
                        bad_offset, bad_line)
                    continue

                frame = mock(
                    _repr = "<parsed Frame>",
                    _class = types.FrameType,
                    f_back = None,
                    f_lineno = int(file_line.group("lineno")),
                    f_code = mock(
                        _repr = "<parsed Code>",
                        _class = types.CodeType,
                        co_name = file_line.group("name").strip(),
                        co_filename = file_line.group("filename").strip()
                    ),
                    f_builtins = {}, f_locals = {}, f_globals = {})
                if frames:
                    frames[-1].f_back = frame
                frames.append(frame)

            elif repeat_line:
                # Got a repeat concatenated message. Unravel it!
                for _ in range(int(repeat_line.group("repeats")) + 1):
                    frame = mock(**frames[-1].__dict__) # Copy frame
                    frames[-1].f_back = frame
                    frames.append(frame)

            elif err_line:
                if frames:
                    # Time to catch some false positive edge cases.
                    try:
                        peek = next(reader) # Peek at the next line
                        reader = (b for a in ([peek], reader) for b in a)
                        peek_err = reg_err.match(peek[offset:])
                        if peek_err and peek_err.group("error") == "NameError": # False positive!
                            continue
                        if reg_file.match(peek[offset:]): # If next line includes File format, we're still going.
                            continue
                    except StopIteration:
                        pass

                    tb = [] # Format traceback
                    for frame in reversed(frames):
                        tb.append(mock(
                            _repr = "<parsed Traceback>",
                            _class = types.TracebackType,
                            tb_frame = frame,
                            tb_lineno = frame.f_lineno,
                            tb_next = tb[-1] if tb else None))

                    # Find and assign errors
                    error = err_line.group("error")
                    type_ = builtins.__dict__.get(error)
                    if not type_:
                        try:
                            module, name = error.rsplit(".", 1)
                            type_ = getattr(__import__(module, fromlist=[""]), name, None)
                        except (ValueError, ImportError):
                            pass

                    message = (err_line.group("value") or "").strip()
                    value = (type_ or Exception)(message)

                    # TODO: Python 3 wants value type to include these. We need to mock these for
                    # error types we cannot load
                    # stype = self.exc_type.__qualname__
                    # smod = self.exc_type.__module__

                    if syntax_pack: # Special care for SyntaxErrors
                        # Python 2
                        value.message = ""
                        value.args += (syntax_pack,)
                        # Python 3
                        value.msg = message
                        value.filename, value.lineno, value.offset, value.text = syntax_pack

                    yield (type_ or error, value, tb[-1])
                frames = offset = syntax_pack = None

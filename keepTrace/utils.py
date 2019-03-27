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
    reg_file = re.compile(r"(  )?File \"(?P<path>[^\"]+)\", line (?P<line>\d+), in (?P<name>.+)")
    reg_err = re.compile(r"(?P<error>[\w\.]+)(: (?P<value>.+))?$")
    # TODO: support recursion error traceback python3
    frames = offset = None
    for line in reader:
        header = line.find("Traceback (most recent call last):")
        if header != -1: # We have started a traceback.
            frames, offset = [], header
        elif frames is not None: # We are currently handling a traceback
            line = line[offset:] # Keep all lines at the same indent
            err_line = reg_err.match(line)
            file_line = reg_file.match(line)
            if file_line: # File "path", line 123, in name
                frame = mock(
                    _repr = "<parsed Frame>",
                    _class = types.FrameType,
                    f_back = None,
                    f_lineno = int(file_line.group("line")),
                    f_code = mock(
                        _repr = "<parsed Code>",
                        _class = types.CodeType,
                        co_name = file_line.group("name").strip(),
                        co_filename = file_line.group("path").strip()
                    ),
                    f_builtins = {}, f_locals = {}, f_globals = {})
                if frames:
                    frames[-1].f_back = frame
                frames.append(frame)
            elif err_line:
                error = err_line.group("error")
                value = (err_line.group("value") or "").strip()
                if frames:
                    tb = []
                    for frame in reversed(frames):
                        tb.append(mock(
                            _repr = "<parsed Traceback>",
                            _class = types.TracebackType,
                            tb_frame = frame,
                            tb_lineno = frame.f_lineno,
                            tb_next = tb[-1] if tb else None))
                    yield (error, value, tb[-1])
                frames = None

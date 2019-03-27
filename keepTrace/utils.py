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
    # Establish the lines we care about
    reg_file = compile(r"(  )?File \"(?P<path>[^\"]+)\", line (?P<line>\d+), in (?P<name>.+)")


    # TODO: support recursion error traceback python3
    trace = None
    for line in reader:
        if trace is not None:
            file_line = file_line_reg.match(line)
            if file_line:
                trace.append(Frame(
                    f_back=trace[-1] if trace else None,
                    f_lineno = int(file_line.group(2)),
                    f_code = Code(
                        co_name = file_line.group(3).strip(),
                        co_filename = file_line.group(1).strip()
                    ),
                    f_builtins = {}, f_locals = {}, f_globals = {}
                ))
            elif line[0] == " ":
                continue
            else:
                tb = []
                for frame in reversed(trace):
                    tb.append(Traceback(
                        tb_frame = frame,
                        tb_lineno = frame.f_lineno,
                        tb_next = tb[-1] if tb else None
                    ))
                message = line.split(":",1)
                if len(message) == 2:
                    yield (message[0], message[1].strip(), tb[-1])
                trace = None
        elif line.startswith("Traceback (most recent call last):"):
            trace = []

if __name__ == '__main__':
    import traceback
    from pprint import pprint

    def error():
        raise RuntimeError("what an error that was")
    def warm():
        error()
    def cool():
        warm()

    try:
        cool()
    except RuntimeError:
        tbs = list(tracebacks(traceback.format_exc().split("\n")))
        traceback.print_exception(*tbs[0])
        assert traceback.format_exc() == "".join(traceback.format_exception(*tbs[0]))

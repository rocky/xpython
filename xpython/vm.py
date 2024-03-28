"""A pure-Python Python bytecode interpreter."""
# Based on:
# pyvm2 by Paul Swartz (z3p), from http://www.twistedmatrix.com/users/z3p/
import linecache
import logging
import sys

import six
from six.moves import reprlib
from xdis import (CO_NEWLOCALS, IS_PYPY, PYTHON3, PYTHON_VERSION_TRIPLE,
                  code2num, next_offset, op_has_argument)
from xdis.cross_types import UnicodeForPython3
from xdis.op_imports import get_opcode_module
from xdis.opcodes.opcode_311 import _nb_ops

from xpython.byteop import get_byteop
from xpython.pyobj import Block, Frame, Traceback, traceback_from_frame

PY2 = not PYTHON3
log = logging.getLogger(__name__)

if PYTHON3:

    def byteint(b):
        return b

else:
    byteint = ord

LINE_NUMBER_WIDTH = 4
LINE_NUMBER_WIDTH_FMT = "L. %%-%dd@" % LINE_NUMBER_WIDTH
LINE_NUMBER_SPACES = " " * (LINE_NUMBER_WIDTH + len("L. ")) + "@"

# Create a repr that won't overflow.
repr_obj = reprlib.Repr()
repr_obj.maxother = 120
repper = repr_obj.repr


class PyVMError(Exception):
    """For raising errors in the operation of the VM."""

    pass


class PyVMRuntimeError(Exception):
    """RuntimeError in operation of PyVM."""

    pass


class PyVMUncaughtException(Exception):
    """Uncaught RuntimeError in operation of PyVM."""

    def __init__(self, name, args, traceback=None):
        self.__name__ = name
        self.traceback = traceback
        self.args = args

    def __getattr__(self, name):
        if name == "__traceback__":
            return self.traceback
        else:
            return super().__getattr__(name)

    def __getitem__(self, i):
        assert 0 <= i <= 2, "Exception index should be in range 0..2 was %d" % i
        if i == 0:
            return self.__name__
        elif i == 1:
            return self.args
        else:
            return self.traceback

    @classmethod
    def from_tuple(cls, exception):
        assert (
            len(exception) == 3
        ), "Expecting exception tuple to have 3 args: type, args, traceback"
        return cls(*exception)

    pass


def format_instruction(
    frame,
    opc,
    bytecode_name,
    int_arg,
    arguments,
    offset,
    line_number,
    extra_debug,
    vm=None,
):
    """Formats an instruction. What's a little different here is that in
    contrast to Python's `dis`, or a colorized version of that, used in
    `trepan3k` we may have access to the frame eval stack and therefore
    can show operands in a nicer way.

    But we also make use of xdis' nicer argument formatting as well. These appear
    for example in MAKE_FUNCTION, and CALL_FUNCTION.
    """
    code = frame.f_code if frame else None
    byte_code = opc.opmap.get(bytecode_name, 0)

    if vm and bytecode_name in vm.byteop.stack_fmt:
        stack_args = vm.byteop.stack_fmt[bytecode_name](vm, int_arg, repr)
    else:
        stack_args = ""

    if hasattr(opc, "opcode_arg_fmt") and bytecode_name in opc.opcode_arg_fmt:
        argrepr = opc.opcode_arg_fmt[bytecode_name](int_arg)
    elif int_arg is None:
        argrepr = ""
    elif byte_code in opc.COMPARE_OPS:
        argrepr = opc.cmp_op[int_arg]
    elif isinstance(arguments, list) and arguments:
        argrepr = arguments[0]
    else:
        argrepr = arguments

    line_str = (
        LINE_NUMBER_SPACES
        if line_number is None
        else LINE_NUMBER_WIDTH_FMT % line_number
    )
    mess = "%s%3d: %s%s %s" % (line_str, offset, bytecode_name, stack_args, argrepr)
    if extra_debug and frame:
        mess += " %s in %s:%s" % (code.co_name, code.co_filename, frame.f_lineno)
    return mess


class PyVM(object):
    def __init__(
        self,
        python_version=PYTHON_VERSION_TRIPLE,
        is_pypy=IS_PYPY,
        vmtest_testing=False,
        format_instruction_func=format_instruction,
    ):
        # The call stack of frames.
        self.frames = []
        # The current frame.
        self.frame = None
        self.return_value = None
        self.last_exception = None
        self.last_traceback_limit = None
        self.last_traceback = None
        self.version = python_version
        self.is_pypy = is_pypy
        self.format_instruction = format_instruction_func

        # FIXME: until we figure out how to fix up test/vmtest.el
        # This changes how we report a VMRuntime error.
        self.vmtest_testing = vmtest_testing

        # Like sys.exc_info() tuple
        self.last_exception = None

        # Sometimes we need a native function (e.g. for method lookup), but
        # most of the time we want a VM function defined in pyobj.
        # This maps between the two.
        self.fn2native = {}

        self.in_exception_processing = False

        # This is somewhat hokey:
        # Give byteop routines a way to raise an error, without having
        # to import this file. We import from from byteops.
        # Alternatively, VMError could be
        # pulled out of this file
        self.PyVMError = PyVMError

        variant = "pypy" if is_pypy else None

        if is_pypy:
            python_version = tuple(python_version[:2])

        self.opc = get_opcode_module(python_version, variant)
        self.byteop = get_byteop(self, python_version, is_pypy)

    ##############################################
    # Frame operations. First the frame stack....
    ##############################################
    def access(self, i=0):
        """return object at position i.
        Default to the top of the stack, but `i` can be a count from the top
        instead.
        """
        return self.frame.stack[-1 - i]

    def peek(self, n):
        if n <= 0:
            raise PyVMError("Peek value must be greater than 0")
        try:
            return self.frame.stack[-n]
        except Exception:
            return 0

    def pop(self, i=0):
        """Pop a value from the stack.

        Default to the top of the stack, but `i` can be a count from the top
        instead.

        """
        return self.frame.stack.pop(-1 - i)

    def popn(self, n):
        """Pop a number of values from the value stack.

        A list of `n` values is returned, the deepest value first.

        """
        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n:] = []
            return ret
        else:
            return []

    def push(self, *vals):
        """Push values onto the value stack."""
        self.frame.stack.extend(vals)

    def set(self, i: int, value):
        """Set a value at stack position i."""
        self.frame.stack[-i] = value

    def top(self):
        """Return the value at the top of the stack, with no changes."""
        return self.frame.stack[-1]

    # end of frame stack operations
    # onto frame block operations..

    def pop_block(self):
        return self.frame.block_stack.pop()

    def push_block(self, type, handler=None, level=None):
        if level is None:
            level = len(self.frame.stack)
        self.frame.block_stack.append(Block(type, handler, level))

    def top_block(self):
        return self.frame.block_stack[-1]

    def jump(self, jump):
        """Move the bytecode pointer to `jump`, so it will execute next,
        However we subtract one from the offset, because fetching the
        next instruction adds one before fetching.
        """
        # The previous pyvm2.py code *always* had self.frame.f_lasti
        # represent the *next* instruction rather than the *last* or
        # current instruction currently under execution. While this
        # was easier to code, consisitent and worked, IT DID NOT
        # REPRESENT PYTHON's semantics. It became unbearable when I
        # added a debugger for x-python that relies on
        # self.frame.f_last_i being correct.
        self.frame.f_lasti = jump
        self.frame.fallthrough = False

    def jump_relative(self, delta: int):
        """Adjust the bytecode pointer by `deleta`, so it will execute next,
        However we subtract one from the offset, because fetching the
        next instruction adds one before fetching.
        """
        self.frame.f_lasti += delta
        self.frame.fallthrough = False

    def make_frame(
        self, code, callargs={}, f_globals=None, f_locals=None, closure=None
    ):
        # The callargs default is safe because we never modify the dict.
        # pylint: disable=dangerous-default-value

        log.debug(
            "make_frame: code=%r, callargs=%s, f_globals=%r, f_locals=%r",
            code,
            repper(callargs),
            (type(f_globals), id(f_globals)),
            (type(f_locals), id(f_locals)),
        )
        if f_globals is not None:
            f_globals = f_globals
            if f_locals is None:
                f_locals = f_globals
        elif self.frames:
            f_globals = self.frame.f_globals
            if f_locals is None:
                f_locals = {}
        else:
            # TODO(ampere): __name__, __doc__, __package__ below are not correct
            f_globals = f_locals = {
                "__builtins__": __builtins__,
                "__name__": "__main__",
                "__doc__": None,
                "__package__": None,
            }

        # Implement NEWLOCALS flag. See Objects/frameobject.c in CPython.
        if code.co_flags & CO_NEWLOCALS:
            f_locals = {"__locals__": {}}

        f_locals.update(callargs)
        frame = Frame(
            f_code=code,
            f_globals=f_globals,
            f_locals=f_locals,
            f_back=self.frame,
            version=self.version,
            closure=closure,
        )

        # THINK ABOUT: should this go into making the frame?
        frame.linestarts = dict(self.opc.findlinestarts(code, dup_lines=True))

        log.debug("%r", frame)
        return frame

    def push_frame(self, frame):
        self.frames.append(frame)
        self.frame = frame

    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None

    def print_frames(self):
        """Print the call stack for debugging. Note that the
        format exactly the same as in traceback.print_tb()
        """
        for f in self.frames:
            filename = f.f_code.co_filename
            lineno = f.line_number()
            print('  File "%s", line %d, in %s' % (filename, lineno, f.f_code.co_name))
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, f.f_globals)
            if line:
                print("    " + line.strip())

    def resume_frame(self, frame):
        frame.f_back = self.frame
        log.debug("resume_frame: %r", frame)

        # Make sure we advance to the next instruction after where we left off.
        if frame.f_lasti == -1:
            # We are just starting out. Set offset to the first
            # instruction, and signal that we should not increment
            # this before fetching next instruction.
            frame.fallthrough = False
            frame.f_lasti = 0
        else:
            frame.fallthrough = True

        val = self.eval_frame(frame)
        frame.f_back = None
        return val

    ##############################################
    # End Frame operations.
    ##############################################

    # This is the main entry point
    def run_code(self, code, f_globals=None, f_locals=None, toplevel=True):
        """run code using f_globals and f_locals in our VM"""
        frame = self.make_frame(code, f_globals=f_globals, f_locals=f_locals)
        try:
            val = self.eval_frame(frame)
        except Exception:
            # Until we get test/vmtest.py under control:
            if self.vmtest_testing:
                raise
            if self.last_traceback:
                self.last_traceback.print_tb()
                print("%s" % self.last_exception[0].__name__, end="")
                le1 = self.last_exception[1]
                tail = ""
                if le1:
                    tail = "\n".join(le1.args)
                print(tail)
            raise

        # Frame ran to normal completion... check some invariants
        if toplevel:
            if self.frames:  # pragma: no cover
                raise PyVMError("Frames left over!")
            if self.frame and self.frame.stack:  # pragma: no cover
                raise PyVMError("Data left on stack! %r" % self.frame.stack)

        return val

    def unwind_block(self, block):
        if block.type == "except-handler":
            offset = 3
        else:
            offset = 0

        while len(self.frame.stack) > block.level + offset:
            self.pop()

        if block.type == "except-handler":
            tb, value, exctype = self.popn(3)
            self.last_exception = exctype, value, tb

    def parse_byte_and_args(self, byte_code, replay=False):
        """Parse 1 - 3 bytes of bytecode into
        an instruction and optionally arguments.

        Argument replay is used to handle breakpoints.
        """

        f = self.frame
        f_code = f.f_code
        co_code = f_code.co_code
        extended_arg = 0

        # Note: There is never more than one argument.
        # The list size is used to indicate whether an argument
        # exists or not.
        # FIMXE: remove and use int_arg as a indicator of whether
        # the argument exists.
        arguments = []
        int_arg = None

        while True:
            if f.fallthrough:
                if not replay:
                    f.f_lasti = next_offset(byte_code, self.opc, f.f_lasti)
            else:
                # Jump instructions must set this False.
                f.fallthrough = True
            offset = f.f_lasti
            line_number = self.frame.linestarts.get(offset, None)
            if line_number is not None:
                f.f_lineno = line_number
            if not replay:
                byte_code = byteint(co_code[offset])
            bytecode_name = self.opc.opname[byte_code]
            arg_offset = offset + 1
            arg = None

            if op_has_argument(byte_code, self.opc):
                if self.version >= (3, 6):
                    int_arg = code2num(co_code, arg_offset) | extended_arg
                    # Note: Python 3.6.0a1 is 2, for 3.6.a3 and beyond we have 1
                    arg_offset += 1
                    if byte_code == self.opc.EXTENDED_ARG:
                        extended_arg = int_arg << 8
                        continue
                    else:
                        extended_arg = 0
                else:
                    int_arg = (
                        code2num(co_code, arg_offset)
                        + code2num(co_code, arg_offset + 1) * 256
                        + extended_arg
                    )
                    arg_offset += 2
                    if byte_code == self.opc.EXTENDED_ARG:
                        extended_arg = int_arg * 65536
                        continue
                    else:
                        extended_arg = 0

                if byte_code in self.opc.CONST_OPS:
                    arg = f_code.co_consts[int_arg]
                    if isinstance(arg, UnicodeForPython3):
                        arg = str(arg)
                elif byte_code in self.opc.FREE_OPS:
                    if int_arg < len(f_code.co_cellvars):
                        arg = f_code.co_cellvars[int_arg]
                    else:
                        var_idx = int_arg - len(f.f_code.co_cellvars)
                        arg = f_code.co_freevars[var_idx]
                elif byte_code in self.opc.NAME_OPS:
                    arg = f_code.co_names[int_arg]
                    if isinstance(arg, UnicodeForPython3):
                        arg = str(arg)
                elif byte_code in self.opc.JREL_OPS:
                    # Many relative jumps are conditional,
                    # so setting f.fallthrough is wrong.
                    if self.version >= (3, 10, 0):
                        int_arg += int_arg
                    arg = arg_offset + int_arg
                elif byte_code in self.opc.JABS_OPS:
                    # We probably could set fallthough, since many (all?)
                    # of these are unconditional, but we'll make the jump do
                    # the work of setting.
                    if self.version >= (3, 10, 0):
                        int_arg += int_arg
                    arg = int_arg
                elif byte_code in self.opc.LOCAL_OPS:
                    arg = f_code.co_varnames[int_arg]
                    if isinstance(arg, UnicodeForPython3):
                        arg = str(arg)
                else:
                    arg = int_arg
                arguments = [arg]
            break

        return bytecode_name, byte_code, int_arg, arguments, offset, line_number

    def log(self, bytecode_name, int_arg, arguments, offset, line_number):
        """Log arguments, block stack, and data stack for each opcode."""
        op = self.format_instruction(
            self.frame,
            self.opc,
            bytecode_name,
            int_arg,
            arguments,
            offset,
            line_number,
            log.isEnabledFor(logging.DEBUG),
            vm=self,
        )
        indent = "    " * (len(self.frames) - 1)
        stack_rep = repper(self.frame.stack)
        block_stack_rep = repper(self.frame.block_stack)

        log.debug("  %sframe.stack: %s" % (indent, stack_rep))
        log.debug("  %sblocks     : %s" % (indent, block_stack_rep))
        log.info("%s%s" % (indent, op))

    def dispatch(self, bytecode_name, int_arg, arguments, offset, line_number):
        """Dispatch by bytecode_name to the corresponding methods.
        Exceptions are caught and set on the virtual machine."""

        why = None
        self.in_exception_processing = False
        byteop = self.byteop
        try:
            if bytecode_name.startswith("UNARY_"):
                byteop.unaryOperator(bytecode_name[6:])
            elif bytecode_name.startswith("BINARY_"):
                if self.version < (3, 11):
                    byteop.binaryOperator(bytecode_name[7:])
                else:
                    byteop.binaryOperator(_nb_ops[int_arg][0][3:])

            elif bytecode_name.startswith("INPLACE_"):
                byteop.inplaceOperator(bytecode_name[8:])
            elif "SLICE+" in bytecode_name:
                self.sliceOperator(bytecode_name)
            else:
                # dispatch
                if hasattr(byteop, bytecode_name):
                    bytecode_fn = getattr(byteop, bytecode_name, None)
                else:
                    bytecode_fn = None
                if not bytecode_fn:  # pragma: no cover
                    raise PyVMError(
                        "Unknown bytecode type: %s\n\t%s"
                        % (
                            self.format_instruction(
                                self.frame,
                                self.opc,
                                bytecode_name,
                                int_arg,
                                arguments,
                                offset,
                                line_number,
                                False,
                            ),
                            bytecode_name,
                        )
                    )
                why = bytecode_fn(*arguments)

        except Exception:
            # Deal with exceptions encountered while executing the op.
            self.last_exception = sys.exc_info()

            # FIXME: dry code
            if not self.in_exception_processing:
                if self.last_exception[0] != SystemExit:
                    log.info(
                        (
                            "exception in the execution of "
                            "instruction:\n\t%s"
                            % self.format_instruction(
                                self.frame,
                                self.opc,
                                bytecode_name,
                                int_arg,
                                arguments,
                                offset,
                                line_number,
                                False,
                            )
                        )
                    )
                if not self.last_traceback:
                    self.last_traceback = traceback_from_frame(self.frame)
                self.in_exception_processing = True

            why = "exception"

        return why

    def manage_block_stack(self, why):
        """Manage a frame's block stack.
        Manipulate the block stack and data stack for looping,
        exception handling, or returning."""
        assert why != "yield"

        block = self.frame.block_stack[-1]
        if block.type == "loop" and why == "continue":
            self.jump(self.return_value)
            why = None
            return why

        if not (block.type == "except-handler" and why == "silenced"):
            self.pop_block()
            self.unwind_block(block)

        if block.type == "loop" and why == "break":
            why = None
            self.jump(block.handler)
            return why

        if self.version < (3, 0):
            if (
                block.type == "finally"
                or (block.type == "setup-except" and why == "exception")
                or block.type == "with"
            ):
                if why == "exception":
                    exctype, value, tb = self.last_exception
                    self.push(tb, value, exctype)
                else:
                    if why in ("return", "continue"):
                        self.push(self.return_value)
                    self.push(why)

                why = None
                self.jump(block.handler)
                return why

        else:
            if why == "exception" and block.type in ["setup-except", "finally"]:
                self.push_block("except-handler")
                exctype, value, tb = self.last_exception
                self.push(tb, value, exctype)
                # PyErr_Normalize_Exception goes here
                self.push(tb, value, exctype)
                why = None
                self.jump(block.handler)
                return why

            elif block.type == "finally":
                if why in ("return", "continue"):
                    self.push(self.return_value)
                self.push(why)

                why = None
                self.jump(block.handler)
                return why
            elif block.type == "except-handler" and why == "silenced":
                # 3.5+ WITH_CLEANUP_FINISH
                # Nothing needs to be done here.
                return None
            elif why == "return":
                # 3.8+ END_FINALLY
                pass

        return why

    # Interpreter main loop
    # This is analogous to CPython's _PyEval_EvalFramDefault() (in 3.x newer Python)
    # or eval_frame() in older 2.x code.
    def eval_frame(self, frame):
        """Run a frame until it returns (somehow).

        Exceptions are raised, the return value is returned.

        """
        self.f_code = frame.f_code
        if frame.f_lasti == -1:
            # We were started new, not yielded back from.
            frame.f_lasti = 0
            # Don't increment before fetching next instruction.
            frame.fallthrough = False
            byte_code = None
        else:
            byte_code = byteint(self.f_code.co_code[frame.f_lasti])
            # byte_code == opcode["YIELD_VALUE"]?

        self.push_frame(frame)
        offset = 0
        while True:
            (
                bytecode_name,
                byte_code,
                int_arg,
                arguments,
                offset,
                line_number,
            ) = self.parse_byte_and_args(byte_code)
            if log.isEnabledFor(logging.INFO):
                self.log(bytecode_name, int_arg, arguments, offset, line_number)

            # When unwinding the block stack, we need to keep track of why we
            # are doing it.
            why = self.dispatch(bytecode_name, int_arg, arguments, offset, line_number)
            if why == "exception":
                # TODO: ceval calls PyTraceBack_Here, not sure what that does.

                # Deal with exceptions encountered while executing the op.
                if not self.in_exception_processing:
                    # FIXME: DRY code
                    if self.last_exception[0] != SystemExit:
                        log.info(
                            (
                                "exception in the execution of "
                                "instruction:\n\t%s"
                                % self.format_instruction(
                                    frame,
                                    self.opc,
                                    bytecode_name,
                                    int_arg,
                                    arguments,
                                    offset,
                                    line_number,
                                    False,
                                )
                            )
                        )
                    if self.last_traceback is None:
                        self.last_traceback = traceback_from_frame(frame)
                    self.in_exception_processing = True

            elif why == "reraise":
                why = "exception"

            if why != "yield":
                while why and frame.block_stack:
                    # Deal with any block management we need to do.
                    why = self.manage_block_stack(why)

            if why:
                break

        # TODO: handle generator exception state

        self.pop_frame()

        if why == "exception":
            last_exception = self.last_exception
            if last_exception and last_exception[0]:
                if isinstance(last_exception[2], Traceback):
                    if not self.frame:
                        if isinstance(last_exception, tuple):
                            self.last_exception = PyVMUncaughtException.from_tuple(
                                last_exception
                            )
                        raise self.last_exception
                else:
                    six.reraise(*self.last_exception)
            else:
                raise PyVMError("Borked exception recording")
            # if self.exception and .... ?
            # log.error("Haven't finished traceback handling, nulling traceback "
            #            "information for now")
            # six.reraise(self.last_exception[0], None)

        self.in_exception_processing = False
        return self.return_value

    # Operators

    def sliceOperator(self, op):
        start = 0
        end = None  # we will take this to mean end
        op, count = op[:-2], int(op[-1])
        if count == 1:
            start = self.pop()
        elif count == 2:
            end = self.pop()
        elif count == 3:
            end = self.pop()
            start = self.pop()
        slice_len = self.pop()
        if end is None:
            end = len(slice_len)
        if op.startswith("STORE_"):
            slice_len[start:end] = self.pop()
        elif op.startswith("DELETE_"):
            del slice_len[start:end]
        else:
            self.push(slice_len[start:end])


if __name__ == "__main__":
    # Simplest of tests
    def five():
        return 5

    # Test with a conditional in it
    a, b = 10, 3

    def mymax():
        return a if a > b else b

    logging.basicConfig(level=logging.DEBUG)
    vm = PyVM()
    vm.make_frame(five.__code__)
    print(vm.run_code(five.__code__))
    print(vm.run_code(mymax.__code__, f_globals=globals(), f_locals=locals()))
    a, b = 7, 20
    print(vm.run_code(mymax.__code__, f_globals=globals(), f_locals=locals()))

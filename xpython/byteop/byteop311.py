# -*- coding: utf-8 -*-
# Copyright (C) 2023-2024 Rocky Bernstein
# This program comes with ABSOLUTELY NO WARRANTY.
# This is free software, and you are welcome to redistribute it
# under certain conditions.
# See the documentation for the full license.
"""Bytecode Interpreter operations for Python 3.11
"""

import inspect
from typing import Any

from xdis.version_info import PYTHON_VERSION_TRIPLE

from xpython.byteop.byteop24 import Version_info
from xpython.byteop.byteop36 import (
    COMPREHENSION_FN_NAMES,
    MAKE_FUNCTION_SLOT_NAMES,
    MAKE_FUNCTION_SLOTS,
)
from xpython.byteop.byteop310 import ByteOp310
from xpython.pyobj import Function, traceback_from_frame


def fmt_make_function(vm, arg=None, repr_fn=repr) -> str:
    """
    returns the name of the function from the code object in the stack
    """
    fn_item = vm.top()
    name = fn_item.co_name
    return f" ({name})"


class ByteOp311(ByteOp310):
    def __init__(self, vm):
        super(ByteOp310, self).__init__(vm)
        self.stack_fmt["MAKE_FUNCTION"] = fmt_make_function
        self.hexversion = 0x30A00F0
        self.version = "3.11.0 (default, Oct 27 1955, 00:00:00)\n[x-python]"
        self.version_info = Version_info(3, 11, 0, "final", 0)

    def call_function38(self, argc: int) -> Any:
        func = self.vm.peek(argc + 1)
        named_args = self.vm.pop()
        pos_args = self.vm.popn(argc - 1)

        func = self.vm.pop()
        return self.call_function_with_args_resolved(func, pos_args, named_args)

    # Changed in 3.11...

    # New in 3.11.  Note: below, when the parameter is "delta", the
    # value has been adjusted from a relative number into and absolute
    # one.
    def CACHE(self):
        """
        Rather than being an actual instruction, this opcode is
        used to mark extra space for the interpreter to cache useful
        data directly in the bytecode itself. It is automatically
        hidden by all dis utilities, but can be viewed with
        show_caches=True.
        """
        return

    # This is handled by the caller.
    # def BINARY_OP(self, op: int):
    #     """
    #       Implements the binary and in-place operators (depending on the value of op):

    #       rhs = STACK.pop()
    #       lhs = STACK.pop()
    #       STACK.append(lhs op rhs)

    #       New in version 3.11.
    #       TOS is a tuple of mapping keys, and TOS1 is the match
    #       subject. Replace TOS with a dict formed from the items of TOS1, but
    #       without any of the keys in TOS.
    #     """
    #     rhs = self.vm.pop()
    #     lhs = self.vm.pop()
    #     self.vm.push(len(self.vm.pop()))
    #     raise self.vm.PyVMError("MATCH_COPY_DICT_WITHOUT_KEYS not implemented")

    def CALL(self, argc: int):
        """Calls a callable object with the number of arguments
        specified by argc, including the named arguments specified by
        the preceding KW_NAMES, if any. On the stack are (in ascending
        order), either:

        * NULL
        * The callable
        * The positional arguments
        * The named arguments

        or:

        * The callable
        * self
        * The remaining positional arguments
        * The named arguments

        argc is the total of the positional and named arguments,
        excluding self when a NULL is not present.

        CALL pops all arguments and the callable object off the stack,
        calls the callable object with those arguments, and pushes the
        return value returned by the callable object.

        Replaces CALL_FUNCTION

        """
        try:
            return self.call_function38(argc)
        except TypeError as exc:
            tb = self.vm.last_traceback = traceback_from_frame(self.vm.frame)
            self.vm.last_exception = (TypeError, exc, tb)
            return "exception"

    def KW_NAMES(self, consti: int):
        """
        Prefixes CALL. Stores a reference to co_consts[consti] into an internal variable
        for use by CALL. co_consts[consti] must be a tuple of strings.

        Replaces CALL_FUNCTION_KW
        """
        # FIXME
        raise self.vm.PyVMError("KW_NAMES not implemented")

    # Changed in 3.11...
    def MAKE_FUNCTION(self, argc: int):
        """
        Pushes a new function object on the stack. From bottom to top,
        the consumed stack must consist of values if the argument
        carries a specified flag value

        * 0x01 a tuple of default values for positional-only and positional-or-keyword
          parameters in positional order
        * 0x02 a dictionary of the default values for the keyword-only parameters
               the key is the parameter name and the value is the default value
        * 0x04 a tuple of strings containing parameters  annotations
        * 0x08 a tuple containing cells for free variables, making a closure
          the code associated with the function (at TOS1)

        Changed from version 3.10: Qualified name at STACK[-1] was removed.
        """
        code = self.vm.pop()

        slot = {
            "defaults": tuple(),
            "kwdefaults": {},
            "annotations": tuple(),
            "closure": tuple(),
        }
        assert 0 <= argc < (1 << MAKE_FUNCTION_SLOTS)
        have_param = list(
            reversed([True if 1 << i & argc else False for i in range(4)])
        )
        for i in range(MAKE_FUNCTION_SLOTS):
            if have_param[i]:
                slot[MAKE_FUNCTION_SLOT_NAMES[i]] = self.vm.pop()

        # FIXME: DRY with code in byteop3{2,4,6}.py

        globs = self.vm.frame.f_globals

        if (
            not inspect.iscode(code)
            and hasattr(code, "to_native")
            and self.version_info[:2] == PYTHON_VERSION_TRIPLE[:2]
        ):
            code = code.to_native()

        # Convert annotations tuple into dictionary
        annotations = {}
        annotations_tup = slot["annotations"]
        for i in range(0, len(annotations_tup), 2):
            annotations[annotations_tup[i]] = annotations_tup[i + 1]

        fn_vm = Function(
            name=code.co_name,
            code=code,
            globs=globs,
            argdefs=slot["defaults"],
            closure=slot["closure"],
            vm=self.vm,
            qualname=code.co_qualname,
            kwdefaults=slot["kwdefaults"],
            annotations=annotations,
        )

        if argc == 0 and code.co_name in COMPREHENSION_FN_NAMES:
            fn_vm.has_dot_zero = True

        if fn_vm._func:
            self.vm.fn2native[fn_vm] = fn_vm._func

        self.vm.push(fn_vm)

    def PRECALL(self, argc: int):
        """
         `meth` is NULL when LOAD_METHOD thinks that it's not
         a method call.

         Stack layout:

                ... | NULL | callable | arg1 | ... | argN
                                                     ^- TOP()
                                        ^- (-oparg)
                             ^- (-oparg-1)
                      ^- (-oparg-2)

        `callable` will be popped by ``call_function``.
         NULL will will be popped manually later.
         If `meth` isn't NULL, it's a method call.  Stack layout:

              ... | method | self | arg1 | ... | argN
                                                 ^- TOP()
                                    ^- (-oparg)
                             ^- (-oparg-1)
                    ^- (-oparg-2)

        `self` and `method` will be popped by ``call_function``.
         We'll be passing `oparg + 1` to call_function, to
         make it accept the `self` as a first argument.

        """
        raise self.vm.PyVMError("PRECALL not implemented")

    def PUSH_NULL(self):
        """Pushes a NULL to the stack. Used in the call sequence to
        match the NULL pushed by LOAD_METHOD for non-method calls.

        """
        self.vm.push(None)

    def COPY(self, i: int):
        """
        Push the i-th item to the top of the stack. The item is not removed from its
        original location.
        """
        stack_i = self.vm.peek(i)
        self.vm.push(stack_i)

    def SWAP(self, i: int):
        """
        Swap TOS with the item at position i.
        """
        tos = self.vm.top()
        stack_i = self.vm.peek(i)
        self.vm.set(i, tos)
        self.vm.set(0, stack_i)

    def CHECK_EXC_MATCH(self):
        """
        To be continued...
        """
        # FIXME
        raise self.vm.PyVMError("KW_NAMES not implemented")

    def JUMP_BACKWARD(self, delta: int):
        """
        Decrements bytecode counter by delta. Checks for interrupts.
        """
        # FIXME: check for interrupts.
        self.vm.jump(-delta)

    def POP_JUMP_BACKWARD_NO_INTERRUPT(self, delta: int):
        """
        Decrements bytecode counter by delta. Does not check for interrupts.
        """
        self.vm.jump(-delta)

    def POP_JUMP_FORWARD_IF_TRUE(self, delta: int):
        """
        If TOS is true, increments the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val == True:  # noqa
            self.vm.jump(delta)

    def POP_JUMP_BACKWARD_IF_TRUE(self, delta: int):
        """
        If TOS is true, decrements the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val == True:  # noqa
            self.vm.jump(-delta)

    def POP_JUMP_FORWARD_IF_FALSE(self, delta: int):
        """
        If TOS is false, increments the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val == False:  # noqa
            self.vm.jump(delta)

    def POP_JUMP_BACKWARD_IF_FALSE(self, delta: int):
        """
        If TOS is false, decrements the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val == False:  # noqa
            self.vm.jump(-delta)

    def POP_JUMP_FORWARD_IF_NOT_NONE(self, delta: int):
        """
        If TOS is not None, increments the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val is not None:
            self.vm.jump(delta)

    def POP_JUMP_BACKWARD_IF_NOT_NONE(self, delta: int):
        """
        If TOS is not None, decrements the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val is not None:
            self.vm.jump(-delta)

    def POP_JUMP_FORWARD_IF_NONE(self, delta: int):
        """
        If TOS is not None, increments the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val is None:
            self.vm.jump(delta)

    def POP_JUMP_BACKWARD_IF_NONE(self, delta: int):
        """
        If TOS is not None, decrements the bytecode counter by delta. TOS is popped.
        """
        val = self.vm.pop()
        if val is None:
            self.vm.jump(-delta)

    def JUMP_IF_TRUE_OR_POP(self, delta: int):
        """
        If TOS is true, increments the bytecode counter by delta
        and leaves TOS on the stack. Otherwise (TOS is false), TOS is
        popped.


        The oparg is now a relative delta rather than an absolute target.
        """
        val = self.vm.top()
        if val == True:  # noqa
            self.vm.jump(delta)
        self.vm.pop()

    def RESUME(self, where: int):
        """
        A no-op. Performs internal tracing, debugging and optimization checks.

        The where operand marks where the RESUME occurs:

          0 The start of a function
          1 After a yield expression
          2 After a yield from expression
          3 After an await expression        To be continued...
        """
        return

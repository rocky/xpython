# -*- coding: utf-8 -*-
# Copyright (C) 2023 Rocky Bernstein
# This program comes with ABSOLUTELY NO WARRANTY.
# This is free software, and you are welcome to redistribute it
# under certain conditions.
# See the documentation for the full license.
"""Bytecode Interpreter operations for Python 3.11
"""

from xpython.byteop.byteop24 import Version_info
from xpython.byteop.byteop310 import ByteOp310


class ByteOp311(ByteOp310):
    def __init__(self, vm):
        super(ByteOp310, self).__init__(vm)
        self.hexversion = 0x30A00F0
        self.version = "3.11.0 (default, Oct 27 1955, 00:00:00)\n[x-python]"
        self.version_info = Version_info(3, 11, 0, "final", 0)

    # Changed in 3.11...

    # New in 3.11.
    # Note: below, when the parameter is "delta", the value has been adjusted from a relative number
    # into and absolute one.
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

    def CALL(self):
        """
        To be continued...
        """
        # FIXME
        raise self.vm.PyVMError("CALL not implemented")

    def KW_NAMES(self):
        """
        To be continued...
        """
        # FIXME
        raise self.vm.PyVMError("KW_NAMES not implemented")

    def PRECALL(self):
        """
        To be continued...
        """
        # FIXME
        raise self.vm.PyVMError("KW_NAMES not implemented")

    def PUSH_NULL(self):
        """
        Pushes a NULL to the stack. Used in the call sequence to match the NULL pushed by
        LOAD_METHOD for non-method calls.
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

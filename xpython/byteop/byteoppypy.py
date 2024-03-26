"""Bytecode Interpreter operations for PyPy in general (all versions)

Specific PyPy versions i.e. PyPy 2.7, 3.2, 3.5-3.7 inherit this.
"""
import inspect


class ByteOpPyPy(object):
    def BUILD_LIST_FROM_ARG(self, count: int):
        """Builds a list containing TOS.
        Is equivalint to BUILD_LIST(0) followed by ROT_TWO
        """
        self.BUILD_LIST(count)
        self.ROT_TWO()

    def JUMP_IF_NOT_DEBUG(self, jump_offset):
        """
        For now, same as JUMP_ABSOLUTE.
        """
        self.vm.jump(jump_offset)

    # For Python 3.7+ this is not correct
    def LOOKUP_METHOD(self, name):
        """From
        https://doc.pypy.org/en/latest/interpreter-optimizations.html#lookup-method-call-method
        LOOKUP_METHOD contains exactly the same attribute lookup logic
        as LOAD_ATTR - thus fully preserving semantics - but pushes
        two values onto the stack instead of one. These two values are
        an “inlined” version of the bound method object: the im_func
        and im_self, i.e. respectively the underlying Python function
        object and a reference to obj. This is only possible when the
        attribute actually refers to a function object from the class;
        when this is not the case, LOOKUP_METHOD still pushes two
        values, but one (im_func) is simply the regular result that
        LOAD_ATTR would have returned, and the other (im_self) is an
        interpreter-level None placeholder.

        For now, we'll assume this is the same as LOAD_ATTR:

        Replaces TOS with getattr(TOS, co_names[namei]).
        Note: name = co_names[namei] set in parse_byte_and_args()
        """
        obj = self.vm.pop()
        val = getattr(obj, name)
        self.vm.push(val)
        if self.version_info[:2] >= (3, 7):
            if inspect.isfunction(val) or inspect.isbuiltin(val):
                self.vm.push("LOAD_METHOD lookup success")
            else:
                self.vm.push("fill in attribute method lookup")

    def CALL_METHOD(self, argc):
        """
        For now, we'll assume this is like CALL_FUNCTION:

        Calls a callable object.
        The low byte of argc indicates the number of positional
        arguments, the high byte the number of keyword arguments.
        ...
        """
        return self.call_function(argc, [], {})

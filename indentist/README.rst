#########
indentist
#########

Unlike a dentist, **indentist** is a painless Python code generator.

====
TODO
====

* Add current indentation to context. Pass context through everything. So that formatters can use that info
  to wrap docstrings which are safe to wrap.


================
Obsolete Example
================


.. code-block:: python

    from indentist import CodeBlock as C

    m = C.module("example.py").add(
        C.class_(
            imports=["dataclasses"],
            decorators=[
                "@dataclasses.dataclass",
            ],
            name="Operation",
            bases=["object"],
            doc="Represents an operation",
        ).of(
            code.func("execute", params=["self"], doc="Executes the thing")
        )),
    )

    print(m.to_code())


The above generates:

.. code-block:: python

    import dataclasses


    @dataclasses.dataclass
    class Operation(object):
        """
        Represents an operation
        """
        def execute(self):
            """
            Executes the thing
            """
            pass

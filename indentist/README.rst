#########
indentist
#########

Unlike a dentist, **indentist** is painless. It does not heal, but it generates and indents code.


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
            code.def_("execute", params=["self"], doc="Executes the thing")
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



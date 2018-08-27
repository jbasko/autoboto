import typing
from typing import List

import dataclasses

from indentist import CodeBlock as C


def test_generic_block():
    assert C().to_code() == ""

    assert C(indented=True).to_code() == "    pass"

    assert C("print(42)").to_code() == "print(42)"

    assert C("for x in range(42):", indented=True).to_code() == "for x in range(42):\n    pass"

    assert C("for x in range(42):", indented=True).of(
        "print(x)"
    ).to_code() == "for x in range(42):\n    print(x)"

    assert C("for x in range(42):", indented=True).of(
        C.dict("params", literal_items={"x": "x"})
    ).to_code() == "for x in range(42):\n    params = {\n        'x': x,\n    }"


def test_none_subblocks_are_skipped():
    c = C().block(
        None,
        "import logging",
        "",
        None,
        "",
        "log = logging.getLogger(__name__)",
    )
    assert c.to_code() == (
        "import logging\n"
        "\n"
        "\n"
        "log = logging.getLogger(__name__)"
    )

    assert C().add(
        "",
        "import logging",
        None,
        None,
        "log = None"
    ).to_code() == (
        "\n"
        "import logging\n"
        "log = None"
    )


def test_generates_dictionary():
    assert C.dict("params").indented

    assert C.dict("params").to_code() == "params = {}"

    d1 = {"a": 1, "b": 2, "c": "3"}
    assert C.dict("params", items=d1).exec()["params"] == d1


def test_generates_class():
    c = C.class_("Operation")
    assert c.indented
    assert c.to_code() == "class Operation:\n    pass"

    d = C.class_("Operation", bases=[str, "object"], doc="Represents an operation").of(
        C.def_("__init__", params=["self"], doc="Create this"),
    )

    # print(d.to_code())
    d_expected = (
        'class Operation(str, object):\n'
        '    """\n'
        '    Represents an operation\n'
        '    """\n'
        '    def __init__(self):\n'
        '        """\n'
        '        Create this\n'
        '        """\n'
        '        pass'
    )
    # print(d_expected)
    assert d_expected == d.to_code()

    op_cls = d.exec()["Operation"]
    assert op_cls.__name__ == "Operation"


def test_generates_dataclass_field():
    f1 = C.dataclass_field("name", type_=str)
    assert f1.to_code() == "name: str"

    f2 = C.dataclass_field("is_enabled", type_=bool, doc="True if is enabled")
    # print(f2.to_code())
    assert f2.to_code() == (
        "\n"
        "# True if is enabled\n"
        "is_enabled: bool"
    )


def test_generates_dataclass():
    c = C.dataclass("Operation").of(
        C.dataclass_field("name", type_=str),
        C.dataclass_field("params", type_=List[dict], default_factory=list),
    )

    # print(c.to_code())
    assert c.to_code() == (
        "@dataclasses.dataclass\n"
        "class Operation:\n"
        "    name: str\n"
        "    params: typing.List[dict] = dataclasses.field(\n"
        "        default_factory=list,\n"
        "    )"
    )
    op_cls = c.exec(globals={"dataclasses": dataclasses, "typing": typing})["Operation"]
    assert len(dataclasses.fields(op_cls)) == 2


def test_generates_module():
    m = C.module("example.py").add(
        C.dataclass("Operation"),
        "", "",
        C.def_("get_logger", imports=["import logging"]).of(
            "return logging.getLogger(__name__)"
        )
    )
    assert m.to_code().startswith("import dataclasses\nimport logging\n\n@dataclasses.dataclass")

import inspect
import typing
from typing import List

import dataclasses

from indentist import CodeBlock as C, generate_dataclass_factory_delegate, Parameter, Constants, Literal, LiteralString


def test_constants():
    assert str(Constants.VALUE_NOT_SET) == "Constants.VALUE_NOT_SET"
    assert not Constants.VALUE_NOT_SET

    assert str(Constants.DEFAULT_NOT_SET) == "Constants.DEFAULT_NOT_SET"
    assert not Constants.DEFAULT_NOT_SET


def test_literal_string():
    x = LiteralString("x")
    assert repr(x) == "'x'"
    assert str(x) == "x"


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

    f3 = C.dataclass_field("Something", metadata={"some_cls": Literal("C")})
    # print(f3.to_code())
    assert f3.to_code() == (
        "Something: typing.Any = dataclasses.field(\n"
        "    metadata={\n"
        "        'some_cls': C,\n"
        "    },\n"
        ")"
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
    assert m.to_code().startswith("import dataclasses\nimport logging\n\n\n@dataclasses.dataclass")


def test_block_of():
    c = C.block("if False:").of(
        "yield None"
    )
    assert c.to_code() == "if False:\n    yield None"


def test_generates_list():
    assert C.block("[").name == "["
    assert C.block("[", closing="]").of().to_code() == "[]"
    assert C.block("[", closing="]").of("1,", "2,").to_code() == (
        "[\n"
        "    1,\n"
        "    2,\n"
        "]"
    )


def test_add_adds_indented_for_indented_block():
    func = C.def_("do_something")
    func.add("print(42)")
    func.add("", "return False")
    # print(func.to_code())
    assert func.to_code() == (
        "def do_something():\n"
        "    print(42)\n"
        "\n"
        "    return False"
    )


def test_decorator_on_def():
    func = C.def_("do_something", params=["x"]).of("print(x)")
    func.add_to_decorators("@staticmethod")
    func.add_to_decorators("@staticmethod")
    assert func.decorators == ["@staticmethod"]
    # print(func.to_code())
    assert func.to_code() == "@staticmethod\ndef do_something(x):\n    print(x)"


def test_return_type_on_def():
    expected_code = (
        "def random_int() -> int:\n"
        "    return 42"
    )
    assert expected_code == C.def_("random_int", return_type=int).of("return 42").to_code()
    assert expected_code == C.def_("random_int", return_type="int").of("return 42").to_code()


def test_generates_dataclass_factory():
    @dataclasses.dataclass
    class X:
        id: int = None
        is_enabled: bool = False

    factory_code = generate_dataclass_factory_delegate(X, name="create_x")
    assert isinstance(factory_code, C)
    # print(factory_code.to_code())

    factory = factory_code.exec(globals={"dataclasses": dataclasses, "X": X, "Constants": Constants})["create_x"]
    assert callable(factory)

    sig = inspect.signature(factory)
    assert sig.parameters["id"].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters["is_enabled"].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    assert isinstance(factory(), X)


def test_generates_dict_from_specified_locals():
    c = C.dict_from_locals("kwargs", params=[Parameter("name", str), Parameter("is_enabled", bool)])
    assert c.to_code() == (
        "kwargs = {}\n"
        "if name is not Constants.VALUE_NOT_SET:\n"
        "    kwargs['name'] = name\n"
        "if is_enabled is not Constants.VALUE_NOT_SET:\n"
        "    kwargs['is_enabled'] = is_enabled"
    )


def test_parameter():
    assert Parameter.SELF.to_sig_part() == "self"
    assert Parameter("id", int).to_sig_part() == "id: int"
    assert Parameter("id", "int").to_sig_part() == "id: int"
    assert Parameter("id", "int", default=Constants.DEFAULT_NOT_SET).to_sig_part() == "id: int"
    assert Parameter("id", "int", default=dataclasses.MISSING).to_sig_part() == "id: int"
    assert Parameter("id", "int", default=5).to_sig_part() == "id: int=5"
    assert Parameter("id", "int", default="5").to_sig_part() == "id: int='5'"
    assert Parameter("id").to_sig_part() == "id: typing.Any"

    # required overrides presence of default value
    assert Parameter("id", int, required=True, default=5).to_sig_part() == "id: int"


def test_def_respects_parameter_requiredness():
    func = C.def_("get_by_id", params=[
        Parameter.SELF,
        Parameter("id", int, required=True, default=5),
        Parameter("no_cache", bool, default=False),
    ])
    assert func.to_code() == (
        "def get_by_id(self, id: int, no_cache: bool=False):\n"
        "    pass"
    )

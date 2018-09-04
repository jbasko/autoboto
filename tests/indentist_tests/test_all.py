import typing
from typing import List

import dataclasses

from autoboto.indentist import CodeGenerator, Constants, Literal, LiteralString, Parameter

code = CodeGenerator()


def test_constants():
    assert str(Constants.VALUE_NOT_SET) == "Constants.VALUE_NOT_SET"
    assert not Constants.VALUE_NOT_SET

    assert str(Constants.DEFAULT_NOT_SET) == "Constants.DEFAULT_NOT_SET"
    assert not Constants.DEFAULT_NOT_SET


def test_literal_string():
    x = LiteralString("x")
    assert repr(x) == "'x'"
    assert str(x) == "x"


def test_empty_def():
    d = code.func("empty")
    assert d.expects_body_or_pass
    assert d.to_code() == "\ndef empty():\n    pass"


def test_empty_def_with_params_as_strings():
    d = code.func("do_nothing", params=["self", "x"])
    assert d.expects_body_or_pass
    assert d.to_code() == "\ndef do_nothing(self, x):\n    pass"


def test_non_empty_def_with_params_as_strings():
    d = code.func("do_something", params=["self", "x"]).of("print(x)")
    assert d.to_code() == (
        "\ndef do_something(self, x):\n"
        "    print(x)"
    )


def test_def_with_doc_string():
    d = code.func("get_complicated", params=["self", "x"], doc="Gets complicated which is a complex number")
    # print(d.to_code())
    assert d.to_code() == (
        '\ndef get_complicated(self, x):\n'
        '    """\n'
        '    Gets complicated which is a complex number\n'
        '    """\n'
        '    pass'
    )


def test_empty_unnamed_dictionary():
    assert code.dict().to_code() == "{}"


def test_empty_named_dictionary():
    params = code.dict("params")
    assert params.to_code() == "params = {}"


def test_non_empty_unnamed_dictionary():
    # "of" allows writing literal code into a dictionary body
    assert code.dict().of("'x': '1'").to_code() == (
        "{\n"
        "    'x': '1'\n"
        "}"
    )


def test_non_empty_named_dictionary():
    d = code.dict("params").of("'x': '1'")
    assert d.to_code() == (
        "params = {\n"
        "    'x': '1'\n"
        "}"
    )
    assert d.exec()["params"] == {'x': '1'}


def test_dictionary_with_items():
    d = code.dict("params", items={"x": "1"})
    assert d.to_code() == (
        "params = {\n"
        "    'x': '1',\n"
        "}"
    )


def test_dictionary_with_literal_items():
    d = code.dict("params", literal_items={"x": "1"})
    assert d.to_code() == (
        "params = {\n"
        "    x: 1,\n"
        "}"
    )


def test_dictionary_and_list_as_kwargs():
    c = code.block("get(", closed_by=")").of(
        code.dict("keys_and_values", as_kwarg=True).comma(),
        code.list("items", as_kwarg=True, items=[1, 2]).comma(),
    )
    # print(c.to_code())
    assert c.to_code() == (
        "get(\n"
        "    keys_and_values={},\n"
        "    items=[\n"
        "        1,\n"
        "        2,\n"
        "    ],\n"
        ")"
    )


def test_generates_empty_class():
    assert code.class_("Op").to_code() == "\n\nclass Op:\n    pass"


def test_generates_class_with_bases_and_doc_string():
    c = code.class_("Op", bases=[str, "object"], doc="Does nothing")
    # print(c.to_code())
    assert c.to_code() == (
        '\n\nclass Op(str, object):\n'
        '    """\n'
        '    Does nothing\n'
        '    """\n'
        '    pass'
    )


def test_decorator_on_class():
    c = code.class_("Op", decorators=["@dataclasses.dataclass"])
    assert c.to_code() == (
        "\n\n@dataclasses.dataclass\n"
        "class Op:\n"
        "    pass"
    )


def test_generates_class():
    c = code.class_("Operation")
    assert c.name == "Operation"
    assert c.expects_body_or_pass

    assert c.to_code() == "\n\nclass Operation:\n    pass"

    d = code.class_("Operation", bases=[str, "object"], doc="Represents an operation").of(
        code.func("__init__", params=["self"], doc="Create this"),
    )
    assert d.doc == "Represents an operation"

    # print(d.to_code())
    d_expected = (
        '\n\nclass Operation(str, object):\n'
        '    """\n'
        '    Represents an operation\n'
        '    """\n\n'
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
    f1 = code.dataclass_field("name", type_=str)
    assert f1.to_code() == "name: str"

    f2 = code.dataclass_field("is_enabled", type_=bool, doc="True if is enabled")
    # print(f2.to_code())
    assert f2.to_code() == (
        "\n\n# True if is enabled\n"
        "is_enabled: bool"
    )

    f3 = code.dataclass_field("Something", metadata={"some_cls": Literal("code")})
    assert f3.metadata == {"some_cls": Literal("code")}
    assert f3.to_code() == (
        "Something: typing.Any = dataclasses.field(\n"
        "    metadata={\n"
        "        'some_cls': code,\n"
        "    },\n"
        ")"
    )


def test_generates_dataclass():
    c = code.dataclass("Operation").of(
        code.dataclass_field("name", type_=str),
        code.dataclass_field("params", type_=List[dict], default_factory=list),
    )

    # print(c.to_code())
    assert c.to_code() == (
        "\n\n@dataclasses.dataclass\n"
        "class Operation:\n"
        "    name: str\n"
        "    params: typing.List[dict] = dataclasses.field(\n"
        "        default_factory=list,\n"
        "    )"
    )
    op_cls = c.exec(globals={"dataclasses": dataclasses, "typing": typing})["Operation"]
    assert len(dataclasses.fields(op_cls)) == 2


def test_generates_module():
    m = code.module("example.py").add(
        code.dataclass("Operation"),
        "", "",
        code.func("get_logger", imports=["import logging"]).of(
            "return logging.getLogger(__name__)"
        )
    )
    assert m.to_code().startswith("import dataclasses\nimport logging\n\n\n\n\n@dataclasses.dataclass")


def test_generates_list():
    assert code.list().to_code() == "[]"
    assert code.list().of().to_code() == "[]"
    assert code.list("items").of().to_code() == "items = []"
    assert code.list().of("1,", "2,").to_code() == (
        "[\n"
        "    1,\n"
        "    2,\n"
        "]"
    )
    assert code.list("items").of("1,", "2,").to_code() == (
        "items = [\n"
        "    1,\n"
        "    2,\n"
        "]"
    )
    assert code.list("items", items=[1, 2]).exec()["items"] == [1, 2]
    assert code.list("items", items=["1", "2"]).exec()["items"] == ["1", "2"]
    assert code.list("items", literal_items=["1", "2"]).exec()["items"] == [1, 2]
    assert code.list("items", literal_items=[1, 2]).exec()["items"] == [1, 2]


def test_decorator_on_function():
    func = code.func("do_something", params=["x"]).of("print(x)")
    func.add_to_decorators("@staticmethod")
    func.add_to_decorators("@staticmethod")
    assert func.decorators == ["@staticmethod"]
    # print(func.to_code())
    assert func.to_code() == "\n@staticmethod\ndef do_something(x):\n    print(x)"


def test_return_type_on_function():
    expected_code = (
        "\ndef random_int() -> int:\n"
        "    return 42"
    )
    assert expected_code == code.func("random_int", return_type=int).of("return 42").to_code()
    assert expected_code == code.func("random_int", return_type="int").of("return 42").to_code()


def test_generates_dict_from_specified_locals():
    c = code.dict_from_locals("kwargs", params=[Parameter("name", str), Parameter("is_enabled", bool)])
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
    func = code.func("get_by_id", params=[
        Parameter.SELF,
        Parameter("id", int, required=True, default=5),
        Parameter("no_cache", bool, default=False),
    ])
    assert func.to_code() == (
        "\ndef get_by_id(self, id: int, no_cache: bool=False):\n"
        "    pass"
    )


def test_comment_block():
    assert code.doc_block_comment("Do not change the value of this").to_code() == (
        "\n# Do not change the value of this"
    )
    assert code.doc_block_comment(
        "This is a long paragraph that may need to be split depending on where it is used and how."
    ).to_code() == (
        "\n# This is a long paragraph that may need to be split depending on where it is\n"
        "# used and how."
    )

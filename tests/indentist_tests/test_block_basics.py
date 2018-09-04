import pytest

from autoboto.indentist import BlockBase, CodeGenerator


@pytest.fixture()
def code():
    # New generator for each test case for clarity
    return CodeGenerator()


def test_block_base_class(code):
    block = BlockBase(code=code)
    assert block.code is code


def test_generic_block(code):
    assert code.block().to_code() == ""
    assert code.block("").to_code() == ""
    assert code.block("", "").to_code() == "\n"
    assert code.block("", "", "").to_code() == "\n\n"
    assert code.block("", None, "").to_code() == "\n"
    assert code.block("x = 1", "y = 2").to_code() == "x = 1\ny = 2"
    assert code.block("x = 1", None, "y = 2", None, None).to_code() == "x = 1\ny = 2"


def test_of_indents_code(code):
    b = code.block("if True:").of("pass")
    assert b.expects_body_or_pass
    assert b.to_code() == (
        "if True:\n"
        "    pass"
    )

    b2 = code.block("if True:").of(
        code.block("if False:").of(
            code.block("for x in range(42):").of("print(x)"),
        ),
        code.block("else:").of("pass"),
    )
    assert b2.to_code() == (
        "if True:\n"
        "    if False:\n"
        "        for x in range(42):\n"
        "            print(x)\n"
        "    else:\n"
        "        pass"
    )


def test_empty_block_of_with_closed_by_is_on_one_line(code):
    d = code.block("{", closed_by="}").of()
    assert not d.expects_body_or_pass
    assert d.to_code() == "{}"


def test_non_empty_block_with_closed_by(code):
    d = code.block("{", closed_by="}").of("1,", "2,")
    assert not d.expects_body_or_pass
    assert d.to_code() == (
        "{\n"
        "    1,\n"
        "    2,\n"
        "}"
    )


def test_empty_block_of_with_no_closed_by_adds_pass(code):
    d = code.block("if False:").of()
    assert d.expects_body_or_pass
    assert d.to_code() == (
        "if False:\n"
        "    pass"
    )

from typing import Dict, List, Tuple

from hypothesis import given
from hypothesis.strategies import booleans, dictionaries, floats, integers, lists, text, tuples

from botogen.autoboto_template import from_boto, to_boto


@given(int_value=integers(), float_value=floats(allow_nan=False), bool_value=booleans(), str_value=text())
def test_handles_primitives(int_value, float_value, bool_value, str_value):
    assert to_boto(int, int_value) == int_value == from_boto(int, int_value)
    assert to_boto(float, float_value) == float_value == from_boto(float, float_value)
    assert to_boto(bool, bool_value) == bool_value == from_boto(bool, bool_value)
    assert to_boto(str, str_value) == str_value == from_boto(str, str_value)


@given(list_of_ints=lists(integers()), tuple_of_ints=tuples(integers()))
def test_handles_sequences_of_primitives(list_of_ints, tuple_of_ints):
    assert to_boto(List[int], list_of_ints) == list_of_ints == from_boto(List[int], list_of_ints)
    assert to_boto(Tuple[int], tuple_of_ints) == tuple_of_ints == from_boto(Tuple[int], tuple_of_ints)


@given(dct=dictionaries(text(), text()))
def test_handles_dict_of_primitives(dct):
    assert to_boto(Dict[str, str], dct) == dct == from_boto(Dict[str, str], dct)

from typing import Any, Dict, List, Tuple, Union

from botogen.autoboto_template import TypeInfo


def test_generic_types_are_recognised():
    assert TypeInfo(List[str]).is_sequence
    assert TypeInfo(Tuple[str]).is_sequence
    assert not TypeInfo(str).is_sequence
    assert not TypeInfo(Dict[str, str]).is_sequence


def test_union_of_str_and_extended_str_is_still_a_primitive():
    class S(str):
        pass

    assert TypeInfo(Union[str, S]).is_primitive
    assert TypeInfo(Union[S, str]).is_primitive


def test_is_dict():
    assert TypeInfo(dict).is_dict
    assert TypeInfo(Dict).is_dict
    assert TypeInfo(Dict[str, str]).is_dict
    assert TypeInfo(Dict[str, Any]).is_dict

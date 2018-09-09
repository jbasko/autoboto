from typing import Dict, List, Tuple

from botogen.autoboto_template import TypeInfo, issubtype


def test_issubtype():
    assert issubtype(List[str], List[str])
    assert issubtype(List[str], List)
    assert issubtype(List[int], List[int])
    assert not issubtype(List[int], List[str])


def test_generic_types_are_recognised():
    assert TypeInfo(List[str]).is_sequence
    assert TypeInfo(Tuple[str]).is_sequence
    assert not TypeInfo(str).is_sequence
    assert not TypeInfo(Dict[str, str]).is_sequence

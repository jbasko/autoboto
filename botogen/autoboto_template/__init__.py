__version__ = "0.3.0"

from typing import Tuple

from .core import ClientBase, OutputShapeBase, ShapeBase, TypeInfo, deserialise_from_boto, issubtype, serialize_to_boto

botocore_version: Tuple[int, int, int] = None
try:
    from .versions import botocore_version  # noqa
except ImportError:
    pass

__all__ = [
    "ClientBase",
    "OutputShapeBase",
    "ShapeBase",
    "TypeInfo",
    "deserialise_from_boto",
    "issubtype",
    "serialize_to_boto",
    "botocore_version",
]

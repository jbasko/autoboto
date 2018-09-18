__version__ = "0.4.3"

from typing import Tuple

from .core import ClientBase, OutputShapeBase, ShapeBase, TypeInfo, from_boto, issubtype, to_boto

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
    "from_boto",
    "issubtype",
    "to_boto",
    "botocore_version",
]

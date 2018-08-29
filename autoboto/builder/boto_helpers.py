import collections
from typing import Generator

import botocore.model
import dataclasses
from botocore.loaders import Loader

from autoboto.permanent.falsey import NOT_SET, NOT_SPECIFIED
from indentist.constants import Literal, LiteralString

loader = Loader()


@dataclasses.dataclass
class Member:
    name: str
    shape: botocore.model.Shape = None
    is_required: bool = None

    @property
    def default(self):
        type_name = self.shape.type_name
        if type_name == "list":
            return NOT_SPECIFIED
        else:
            return NOT_SET

    @property
    def default_factory(self):
        type_name = self.shape.type_name
        if type_name == "list":
            return "list"
        else:
            return NOT_SPECIFIED

    @property
    def metadata(self):
        if isinstance(self.shape, botocore.model.ListShape):
            return {
                "shape_type": Literal("list"),
                "shape_item_cls_name": LiteralString(self.shape.member.name),
            }
        elif isinstance(self.shape, botocore.model.StructureShape):
            return {
                "shape_type": Literal("dict"),
                "shape_item_cls_name": LiteralString(self.shape.name),
            }
        return NOT_SPECIFIED

    @property
    def documentation(self):
        return self.shape.documentation

    @property
    def type_annotation(self):
        type_name = self.shape.type_name
        if type_name in ("integer", "long"):
            return "int"
        elif type_name == "string":
            return "str"
        elif type_name == "timestamp":
            return "datetime.datetime"
        elif type_name == "structure":
            return f'"{self.shape.name}"'
        elif type_name == "list":
            return f"typing.List[\"{self.shape.member.name}\"]"
        elif type_name == "boolean":
            return "bool"
        elif type_name == "map":
            return "dict"
        elif type_name == "blob":
            return "typing.Any"
        else:
            raise ValueError(type_name)


def iter_sorted_members(shape: botocore.model.Shape) -> Generator[Member, None, None]:
    """
    Iterate over sorted members of shape in such an order
    that required members are yielded first and optional members are yielded afterwards.
    """

    if shape is None:
        return

    if isinstance(shape, botocore.model.StructureShape):
        members = collections.OrderedDict()
        required_names = shape.metadata.get("required", ())
        for name, shape in shape.members.items():
            members[name] = Member(name, shape=shape, is_required=name in required_names)
        yield from sorted(members.values(), key=lambda m: not m.is_required)
    else:
        raise TypeError(f"No idea how to iterate over members of {shape}")


class ServiceModel(botocore.model.ServiceModel):
    def __init__(self, service_name):
        super().__init__(
            service_description=loader.load_service_model(service_name, "service-2"),
            service_name=service_name,
        )

    def operation_model(self, operation_name) -> botocore.model.OperationModel:
        return super().operation_model(operation_name)

    def iter_operations(self) -> Generator[botocore.model.OperationModel, None, None]:
        for operation_name in self.operation_names:
            yield self.operation_model(operation_name)

    def iter_shapes(self) -> Generator[botocore.model.Shape, None, None]:
        for shape_name in self.shape_names:
            yield self.shape_for(shape_name)

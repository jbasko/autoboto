"""
This module contains classes that override botocore.model classes in order to inject some helpers.
"""
import collections
import datetime
from typing import Iterator

import botocore.loaders
import botocore.model


class AbShapeMixin(botocore.model.Shape):
    PRIMITIVE_TYPES = {
        "string": str,
        "timestamp": datetime.datetime,
        "boolean": bool,
        "integer": int,
        "long": int,
        "double": float,
        "float": float,
    }

    @property
    def is_primitive(self):
        return self.type_name in self.PRIMITIVE_TYPES

    @property
    def is_enum(self):
        return self.type_name == "string" and self.enum

    @property
    def member(self) -> "AbShape":
        return super().member

    @property
    def sorted_members(self) -> Iterator["AbShape"]:
        raise NotImplementedError()


class AbShape(AbShapeMixin, botocore.model.Shape):
    pass


class AbShapeMember(AbShape):
    def __init__(self, name: str, shape: AbShape, is_required: bool):
        self.name = name
        self.shape = shape
        self.is_required = is_required

    def __getattribute__(self, item):
        if item in ("name", "shape", "is_required"):
            return object.__getattribute__(self, item)
        else:
            return getattr(self.shape, item)


class AbStructureShape(AbShapeMixin, botocore.model.StructureShape):
    @property
    def sorted_members(self):
        """
        Iterate over sorted members of shape in such an order
        that required members are yielded first and optional members are yielded afterwards.
        """
        members = collections.OrderedDict()
        required_names = self.metadata.get("required", ())
        for name, shape in self.members.items():
            members[name] = AbShapeMember(name=name, shape=shape, is_required=name in required_names)
        yield from sorted(members.values(), key=lambda m: not m.is_required)


class AbListShape(AbShapeMixin, botocore.model.ListShape):
    pass


class AbMapShape(AbShapeMixin, botocore.model.MapShape):
    pass


class AbStringShape(AbShapeMixin, botocore.model.StringShape):
    pass


class AbShapeResolver(botocore.model.ShapeResolver):
    # Any type not in this mapping will default to the Shape class.
    SHAPE_CLASSES = {
        'structure': AbStructureShape,
        'list': AbListShape,
        'map': AbMapShape,
        'string': AbStringShape
    }

    def get_shape_by_name(self, shape_name, member_traits=None):
        try:
            shape_model = self._shape_map[shape_name]
        except KeyError:
            raise botocore.model.NoShapeFoundError(shape_name)
        try:
            shape_cls = self.SHAPE_CLASSES.get(shape_model['type'], AbShape)
        except KeyError:
            raise botocore.model.InvalidShapeError("Shape is missing required key 'type': %s" % shape_model)
        if member_traits:
            shape_model = shape_model.copy()
            shape_model.update(member_traits)
        result = shape_cls(shape_name, shape_model, self)
        return result


class AbOperationModel(botocore.model.OperationModel):
    pass


class AbServiceModel(botocore.model.ServiceModel):
    loader = botocore.loaders.Loader()

    def __init__(self, service_name):
        super().__init__(
            self.loader.load_service_model(service_name, "service-2"),
            service_name,
        )
        self._shape_resolver = AbShapeResolver(self._service_description.get('shapes', {}))

    def operation_model(self, operation_name):
        try:
            model = self._service_description['operations'][operation_name]
        except KeyError:
            raise botocore.model.OperationNotFoundError(operation_name)
        return AbOperationModel(model, self, operation_name)

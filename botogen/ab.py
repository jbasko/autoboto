"""
This module contains classes that override botocore.model classes in order to inject some helpers.
"""
import collections
import datetime
from typing import ClassVar, Dict, Iterator, Optional

import botocore.loaders
import botocore.model
import botocore.paginate
from cached_property import cached_property


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

    @cached_property
    def is_output_shape(self):
        for operation in self._shape_resolver._operations_map.values():
            if "output" in operation:
                if operation["output"]["shape"] == self.name:
                    return True
        return False

    @cached_property
    def is_input_shape(self):
        for operation in self._shape_resolver._operations_map.values():
            if "input" in operation:
                if operation["input"]["shape"] == self.name:
                    return True
        return False

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
        Iterate over sorted members of shape in the same order in which
        the members are declared except yielding the required members before
        any optional members.
        """
        members = collections.OrderedDict()
        required_names = self.metadata.get("required", ())
        for name, shape in self.members.items():
            members[name] = AbShapeMember(name=name, shape=shape, is_required=name in required_names)

        if self.is_output_shape:
            # ResponseMetadata is the first member for all output shapes.
            yield AbShapeMember(
                name="ResponseMetadata",
                shape=self._shape_resolver.get_shape_by_name("ResponseMetadata"),
                is_required=True,
            )

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

    def __init__(self, shape_map, operations_map):
        self._operations_map = operations_map
        super().__init__(shape_map=shape_map)

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

    def get_paginator(self) -> Optional[Dict]:
        if self._service_model.paginator_model:
            try:
                return self._service_model.paginator_model.get_paginator(self.name)
            except ValueError:
                return None
        return None


class AbPaginatorModel(botocore.paginate.PaginatorModel):
    pass


class AbServiceModel(botocore.model.ServiceModel):
    loader: ClassVar = botocore.loaders.Loader()
    services_with_paginators: ClassVar = loader.list_available_services("paginators-1")
    autoboto_shape_map_additions: ClassVar = {
        "ResponseMetadataKey": {
            "type": "string",
        },
        "ResponseMetadataValue": {
            "type": "string",
        },
        "ResponseMetadata": {
            "type": "map",
            "key": {
                "shape": "ResponseMetadataKey"
            },
            "value": {
                "shape": "ResponseMetadataValue"
            },
        },
    }

    paginator_model: Optional[AbPaginatorModel] = None

    def __init__(self, service_name):
        super().__init__(
            self.loader.load_service_model(service_name, "service-2"),
            service_name,
        )
        if service_name in self.services_with_paginators:
            self.paginator_model = AbPaginatorModel(self.loader.load_service_model(service_name, "paginators-1"))
        self._shape_resolver = AbShapeResolver(
            shape_map=self._service_description.get('shapes', {}),
            operations_map=self._service_description.get('operations', {}),
        )
        self._shape_resolver._shape_map.update(self.autoboto_shape_map_additions)

    def operation_model(self, operation_name):
        try:
            model = self._service_description['operations'][operation_name]
        except KeyError:
            raise botocore.model.OperationNotFoundError(operation_name)
        return AbOperationModel(model, self, operation_name)

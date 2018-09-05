import collections
import datetime
import enum
import typing

import dataclasses


@dataclasses.dataclass
class TypeInfo:
    type: typing.Union[typing.Type, typing.GenericMeta]

    def __post_init__(self):

        # This is to handle NewType()
        if hasattr(self.type, "__supertype__"):
            self.type = self.type.__supertype__

    @property
    def is_primitive(self):
        return self.type in (int, bool, float, str, datetime.datetime)

    @property
    def is_sequence(self):
        return (
            isinstance(self.type, type) and
            issubclass(self.type, collections.Sequence) and
            not issubclass(self.type, str)
        )

    @property
    def is_dict(self):
        return isinstance(self.type, type) and issubclass(self.type, dict)

    @property
    def is_dataclass(self):
        return dataclasses.is_dataclass(self.type)

    @property
    def is_enum(self):
        return isinstance(self.type, type) and issubclass(self.type, enum.Enum)

    @property
    def is_any(self):
        return self.type is typing.Any

    @property
    def list_item_type(self):
        if isinstance(self.type, typing.GenericMeta):
            if self.type.__args__:
                return self.type.__args__[0]
        return typing.Any

    @property
    def dict_value_type(self):
        if isinstance(self.type, typing.GenericMeta):
            return self.type.__args__[1]
        else:
            return typing.Any

    @property
    def name(self):
        return self.type.__name__

    def __call__(self, *args, **kwargs):
        if isinstance(self.type, typing.GenericMeta):
            # Instances of type like typing.Tuple cannot be initialised.
            # Relying on __extra__ to have "tuple" set as value in these cases.
            return self.type.__extra__(*args, **kwargs)
        else:
            return self.type(*args, **kwargs)


def deserialise_from_boto(type_info: TypeInfo, payload: typing.Any) -> typing.Any:
    if payload is None:
        return payload

    if not isinstance(type_info, TypeInfo):
        type_info = TypeInfo(type_info)

    if type_info.is_any:
        return payload

    elif type_info.is_primitive:
        return payload

    elif type_info.is_enum:
        return type_info.type[payload]

    elif type_info.is_sequence:
        new_value = []
        for item in payload:
            new_value.append(deserialise_from_boto(type_info.list_item_type, item))
        return type_info(new_value)

    elif type_info.is_dict:
        new_value = {}
        for k, v in payload.items():
            new_value[k] = deserialise_from_boto(type_info.dict_value_type, v)
        return type_info(new_value)

    elif type_info.is_dataclass:
        payload = dict(payload)
        attrs = {}

        for attr_name, boto_name, attr_type in type_info.type._get_boto_mapping():
            if boto_name not in payload:
                continue

            attr_value = payload.pop(boto_name)
            if attr_value is ShapeBase.NOT_SET:
                continue
            else:
                attrs[attr_name] = deserialise_from_boto(attr_type, attr_value)

        if payload:
            raise ValueError(
                f"Unexpected fields found in payload for {type_info.name}: {', '.join(payload.keys())}"
            )

        return type_info(**attrs)

    raise TypeError((type_info, payload))


def serialize_to_boto(type_info: TypeInfo, payload: typing.Any) -> typing.Any:
    if payload is None:
        return payload

    if not isinstance(type_info, TypeInfo):
        type_info = TypeInfo(type_info)

    if type_info.is_any:
        return payload

    elif type_info.is_primitive:
        return payload

    elif type_info.is_enum:
        return payload.value

    elif type_info.is_sequence:
        new_value = []
        for item in payload:
            new_value.append(serialize_to_boto(type_info.list_item_type, item))
        return type_info(new_value)

    elif type_info.is_dict:
        new_value = {}
        for k, v in payload.items():
            new_value[k] = serialize_to_boto(type_info.dict_value_type, v)
        return type_info(new_value)

    elif type_info.is_dataclass:
        boto_dict = {}

        for attr_name, boto_name, attr_type in type_info.type._get_boto_mapping():
            attr_value = getattr(payload, attr_name)
            if attr_value is ShapeBase.NOT_SET:
                continue
            else:
                boto_dict[boto_name] = serialize_to_boto(attr_type, attr_value)

        return boto_dict

    raise TypeError((type_info, payload))


class ShapeBase:
    class _Falsey:
        def __init__(self, name):
            assert name
            self._name = name

        def __bool__(self):
            return False

        def __repr__(self):
            return self._name

        def __str__(self):
            return self._name

    NOT_SET = _Falsey("NOT_SET")

    @classmethod
    def _get_boto_mapping(cls) -> typing.List[typing.Tuple[str, str, TypeInfo]]:
        raise NotImplementedError()

    def to_boto_dict(self):
        return serialize_to_boto(TypeInfo(self), self)

    @classmethod
    def from_boto_dict(cls, d) -> "ShapeBase":
        return deserialise_from_boto(TypeInfo(cls), d)


@dataclasses.dataclass
class OutputShapeBase(ShapeBase):
    """
    Base class for all response shapes.
    """

    response_metadata: typing.Dict = dataclasses.field(default_factory=dict)

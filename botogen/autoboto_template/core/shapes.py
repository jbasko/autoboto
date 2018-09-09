import typing

import dataclasses

from .type_info import TypeInfo


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


class _BotoFields:
    def __get__(self, instance: "ShapeBase", owner: typing.Type["ShapeBase"]):
        return [name for _, name, _ in owner._get_boto_mapping()]


class _AutobotoFields:
    def __get__(self, instance: "ShapeBase", owner: typing.Type["ShapeBase"]):
        return [name for name, _, _ in owner._get_boto_mapping()]


class ShapeBase:
    """
    Base class for all shapes.
    A shape in boto is effectively a type with rich metadata.
    """

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

    def to_boto_dict(self) -> typing.Dict:
        """
        Returns a dictionary representing this shape with keys as expected by boto.
        """
        return serialize_to_boto(TypeInfo(self), self)

    @classmethod
    def from_boto_dict(cls, d) -> "ShapeBase":
        """
        Given a dictionary with keys originating in boto, creates a shape of this class.
        """
        return deserialise_from_boto(TypeInfo(cls), d)

    boto_fields: typing.List[str] = _BotoFields()
    autoboto_fields: typing.List[str] = _AutobotoFields()


@dataclasses.dataclass
class OutputShapeBase(ShapeBase):
    """
    Base class for all response shapes.
    """

    response_metadata: typing.Dict = dataclasses.field(default_factory=dict)

import typing

import dataclasses

from .type_info import TypeInfo


def from_boto(type_info: TypeInfo, payload: typing.Any) -> typing.Any:
    if payload is None:
        return payload

    if not isinstance(type_info, TypeInfo):
        type_info = TypeInfo(type_info)

    if type_info.is_any:
        return payload

    elif type_info.is_primitive:
        return payload

    elif type_info.is_enum:
        try:
            return type_info.type(payload)
        except ValueError:
            # Return raw value for unexpected values because it looks
            # like the lists aren't complete.
            return payload

    elif type_info.is_sequence:
        new_value = []
        for item in payload:
            new_value.append(from_boto(type_info.list_item_type, item))
        return type_info(new_value)

    elif type_info.is_dict:
        new_value = {}
        for k, v in payload.items():
            new_value[k] = from_boto(type_info.dict_value_type, v)
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
                attrs[attr_name] = from_boto(attr_type, attr_value)

        if payload:
            raise ValueError(
                f"Unexpected fields found in payload for {type_info.name}: {', '.join(payload.keys())}"
            )

        return type_info(**attrs)

    raise TypeError((type_info, payload))


def to_boto(type_info: TypeInfo, payload: typing.Any) -> typing.Any:
    if payload is None:
        return payload

    if not isinstance(type_info, TypeInfo):
        type_info = TypeInfo(type_info)

    if type_info.is_any:
        return payload

    elif type_info.is_primitive:
        return payload

    elif type_info.is_enum:
        return payload

    elif type_info.is_sequence:
        new_value = []
        for item in payload:
            new_value.append(to_boto(type_info.list_item_type, item))
        return type_info(new_value)

    elif type_info.is_dict:
        new_value = {}
        for k, v in payload.items():
            new_value[k] = to_boto(type_info.dict_value_type, v)
        return type_info(new_value)

    elif type_info.is_dataclass:
        boto_dict = {}
        for attr_name, boto_name, attr_type in type_info.type._get_boto_mapping():
            attr_value = getattr(payload, attr_name)
            if attr_value is ShapeBase.NOT_SET:
                continue
            else:
                boto_dict[boto_name] = to_boto(attr_type, attr_value)
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

    def __post_init__(self):
        self._page_iterator = None

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

    def to_boto(self) -> typing.Dict:
        """
        Returns a dictionary representing this shape with keys as expected by boto.
        """
        return to_boto(TypeInfo(self), self)

    @classmethod
    def from_boto(cls, d) -> "ShapeBase":
        """
        Given a dictionary with keys originating in boto, creates a shape of this class.
        """
        return from_boto(TypeInfo(cls), d)

    boto_fields: typing.ClassVar[typing.List[str]] = _BotoFields()
    autoboto_fields: typing.ClassVar[typing.List[str]] = _AutobotoFields()


@dataclasses.dataclass
class OutputShapeBase(ShapeBase):
    """
    Base class for all response shapes.
    """

    response_metadata: typing.Dict = dataclasses.field(default_factory=dict)

    def _paginate(self) -> typing.Generator["OutputShapeBase", None, None]:
        yield self
        for page in self._page_iterator:
            yield self.from_boto(page)

import collections.abc
import datetime
import sys
import typing

import dataclasses
import typing_inspect


@dataclasses.dataclass
class TypeInfo:
    type: typing.Any

    @property
    def is_primitive(self):
        if self.type in (int, bool, float, str, datetime.datetime):
            return True

        if typing_inspect.get_origin(self.type) is typing.Union:
            if all(issubclass(a, str) for a in typing_inspect.get_args(self.type)):
                return True

        return False

    @property
    def is_sequence(self):
        return (
            isinstance(self.type, type) and
            issubclass(self.type, collections.abc.Sequence) and
            not issubclass(self.type, str)
        ) or (
            typing_inspect.is_generic_type(self.type) and typing_inspect.get_origin(self.type) in (list, typing.List)
        ) or (
            typing_inspect.is_tuple_type(self.type) and typing_inspect.get_origin(self.type) in (tuple, typing.Tuple)
        )

    @property
    def is_dict(self):
        return (
            isinstance(self.type, type) and issubclass(self.type, collections.abc.Mapping)
        ) or (
            typing_inspect.is_generic_type(self.type) and typing_inspect.get_origin(self.type) in (dict, typing.Dict)
        )

    @property
    def is_dataclass(self):
        return dataclasses.is_dataclass(self.type)

    @property
    def is_enum(self):
        return isinstance(self.type, type) and issubclass(self.type, str) and self.type != str

    @property
    def is_any(self):
        return self.type is typing.Any

    @property
    def list_item_type(self):
        if getattr(self.type, "__args__", None):
            return self.type.__args__[0]
        return typing.Any

    @property
    def dict_value_type(self):
        if getattr(self.type, "__args__", None):
            return self.type.__args__[1]
        else:
            return typing.Any

    @property
    def name(self):
        return self.type.__name__

    def __call__(self, *args, **kwargs):
        """
        Create a new instance of the type.
        """

        # Type annotations like typing.Tuple and typing.List are not instantiatable.
        # Have to find out the real type.
        if sys.version_info >= (3, 7) and hasattr(self.type, "__origin__"):
            return self.type.__origin__(*args, **kwargs)
        elif hasattr(self.type, "__extra__"):
            return self.type.__extra__(*args, **kwargs)
        else:
            return self.type(*args, **kwargs)

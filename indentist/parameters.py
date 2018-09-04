import typing

import dataclasses

from .constants import Constants


def type_to_sig_part(type_):
    if type_ is typing.Any or isinstance(type_, typing.GenericMeta):
        return str(type_)
    elif isinstance(type_, type):
        return type_.__name__
    elif isinstance(type_, str):
        return type_
    elif type_ is None:
        return None
    else:
        raise ValueError(type_)


@dataclasses.dataclass
class Parameter:
    name: str
    type_: typing.Union[typing.Type, str] = typing.Any
    required: bool = False
    default: typing.Any = Constants.DEFAULT_NOT_SET
    documentation: str = None

    # Special parameter, initialised below
    SELF = None  # type: Parameter

    def to_sig_part(self):
        if self is Parameter.SELF:
            return f"{self.name}"

        if self.required or self.default in (dataclasses.MISSING, Constants.DEFAULT_NOT_SET):
            default = ""
        else:
            default = f"={self.default!r}"

        return f"{self.name}: {type_to_sig_part(self.type_)}{default}"


Parameter.SELF = Parameter("self", type_=object)

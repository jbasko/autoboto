class Literal:
    def __init__(self, value: str, is_falsey=False):
        self.value = value
        self.is_falsey = is_falsey

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, Literal) and (self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self == other

    def __bool__(self):
        return not self.is_falsey


class LiteralString(Literal):
    def __repr__(self):
        return f"{self.value!r}"


class Constants:
    # Used as a special default value of function arguments to distinguish
    # arguments for which user has not supplied value.
    VALUE_NOT_SET = Literal("Constants.VALUE_NOT_SET", is_falsey=True)

    # Used as a special default value which tells that the parameter
    # or attribute is required (as it has no proper default set).
    DEFAULT_NOT_SET = Literal("Constants.DEFAULT_NOT_SET", is_falsey=True)

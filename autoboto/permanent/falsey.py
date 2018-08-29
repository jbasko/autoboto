class _Falsey:
    # TODO Looks like must use equality because "not is NOT_SET" doesn't work. Maybe due to messy imports?

    def __init__(self, repr):
        self._not_set_repr = repr

    def __bool__(self):
        return False

    def __repr__(self):
        return self._not_set_repr

    def __eq__(self, other):
        return isinstance(other, _Falsey) and other._not_set_repr == self._not_set_repr

    def __ne__(self, other):
        return not (self == other)


NOT_SPECIFIED = _Falsey("NOT_SPECIFIED")
NOT_SET = _Falsey("NOT_SET")

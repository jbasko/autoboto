import dataclasses


def field_is_required(field: dataclasses.Field):
    return field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING

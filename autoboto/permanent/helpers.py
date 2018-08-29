import typing

import dataclasses


def transform_response(response, operation_cls, shapes):
    """
    Given a dictionary returned by a service operation, this recursively transforms
    it into an instance of the documented shape.
    """
    assert isinstance(response, dict), response
    response.pop("ResponseMetadata", None)

    fields = {f.name: f for f in dataclasses.fields(operation_cls)}

    parsed = {}

    for k, v in response.items():
        f = fields[k]  # type: dataclasses.Field
        if f.type and isinstance(f.type, type) and issubclass(f.type, typing.List):
            list_item_shape_name = f.type.__args__[0].__forward_arg__
            shape_cls = getattr(shapes, list_item_shape_name)
            parsed[k] = [transform_response(item, shape_cls, shapes) for item in v]
        else:
            parsed[k] = v

    return operation_cls(**parsed)

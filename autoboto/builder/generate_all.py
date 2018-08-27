import os
import typing
from pathlib import Path
from typing import List

from botocore import xform_name
from botocore.model import StructureShape
from html2text import html2text

from indentist import CodeBlock as C, DEFAULT_NOT_SET

from .boto_helpers import ServiceModel, iter_sorted_members
from .core import build_dir, generate_dataclass_v2
from .log import log


def main():
    generate_service_package("s3")
    generate_service_shapes("s3")
    generate_service_operations("s3")


_service_models = {}


def get_service_model(service_name) -> ServiceModel:
    if service_name not in _service_models:
        _service_models[service_name] = ServiceModel(service_name)
    return _service_models[service_name]


def prepare_build_sub_dir(sub_dir: Path, delete_files: List[str]):
    assert build_dir in sub_dir.parents

    if not build_dir.exists():
        os.makedirs(build_dir)
        log.info(f"Created build directory {build_dir}")

    if not sub_dir.exists():
        os.makedirs(sub_dir)
        log.info(f"Created build sub-directory {sub_dir}")

    (sub_dir / "__init__.py").touch()

    for f in delete_files:
        fp = (sub_dir / f).resolve()
        assert sub_dir in fp.parents
        if fp.exists():
            fp.unlink()
            log.info(f"Deleted {fp}")


def generate_service_package(service_name, generated_package="autoboto"):
    target_dir = build_dir / "services" / service_name
    prepare_build_sub_dir(target_dir, delete_files=["__init__.py"])

    client_module = C.module(
        name="client",
        imports=[
            "import boto3",
            "from autoboto.permanent.falsey import NOT_SET",
        ],
    )

    client_class = C.class_(
        name="Client",
    ).of(
        C.def_("__init__", params=["self", "*args", "**kwargs"]).of(
            f"self._service_client = boto3.client({service_name!r}, *args, **kwargs)",
        ),
        "",
    )

    for operation in get_service_model(service_name).iter_operations():
        params = ["self"]
        for member in iter_sorted_members(operation.input_shape):
            params.append(f"{member.name}{'' if member.is_required else '=NOT_SET'}")

        documentation = html2text(operation.documentation) if operation.documentation else None
        client_class.add(
            C.def_(xform_name(operation.name), params=params, doc=documentation).of(
                f"return self._service_client.{xform_name(operation.name)}()",
            ),
            "",
        )

    client_module.add(client_class)
    client_module.write_to(target_dir / "client.py")

    init_module = C.module(
        name="__init__",
        imports=[
            "from .client import Client",
        ],
    ).add(
        C.block("__all__ = [", closing="]").of(
            '"Client",',
        ),
    )
    init_module.write_to(target_dir / "__init__.py")


def generate_service_shapes(service_name, generated_package="autoboto"):
    shapes_module = C.module(
        name="shapes",
        imports=[
            "import datetime",
            "import dataclasses",
            "from autoboto.permanent.falsey import NOT_SET",
        ],
    )

    for shape in get_service_model(service_name).iter_shapes():
        if not isinstance(shape, StructureShape):
            log.debug(f"Skipping non-StructureShape {shape}")
            continue

        shape_dataclass = generate_dataclass_v2(
            name=shape.name,
            documentation=shape.documentation,
            fields=iter_sorted_members(shape),
        )

        shapes_module.add(shape_dataclass)

    target_dir = build_dir / "services" / service_name
    prepare_build_sub_dir(target_dir, delete_files=["shapes.py"])

    module_path = target_dir / "shapes.py"
    shapes_module.write_to(module_path)
    log.info(f"Output written to {module_path}")

    return module_path, f"{generated_package}.services.{service_name}.shapes"


def generate_service_operations(service_name, generated_package="autoboto"):
    operations_module = C.module(
        name="operations",
        # TODO add imports where necessary and let indentist calculate the imports required for the module
        imports=[
            "import datetime",
            "import typing",
            "from autoboto.permanent import helpers",
            "from autoboto.permanent.falsey import NOT_SET",
            f"from {generated_package}.services.{service_name} import shapes",
        ],
    )

    operations_module.add(
        C.dataclass("Operation").of(
            "_service_method_name = None",
            "",
            C.def_("execute", params=["self", "client=None"], return_type=typing.Dict).of(
                "params = {k: v for k, v in dataclasses.asdict(self).items() if v != NOT_SET}",
                "return getattr(client, self._service_method_name)(**params)",
            ),
            "",
            "",
        ),
    )

    for operation in get_service_model(service_name).iter_operations():
        return_type_for_execute = DEFAULT_NOT_SET
        if operation.output_shape:
            return_type_for_execute = f"shapes.{operation.output_shape.name}"

        operation_dataclass = generate_dataclass_v2(
            name=operation.name,
            documentation=operation.documentation,
            bases=["Operation"],
            before_fields=[
                C.block(
                    f"_service_method_name = {xform_name(operation.name)!r}",
                ),
            ],
            fields=iter_sorted_members(operation.input_shape),
            after_fields=[
                "",
                C.def_(name="execute", params=["self", "client=None"], return_type=return_type_for_execute).of(
                    "response = super().execute(client=client)",
                    (
                        f"return helpers.transform_response(response, shapes.{operation.output_shape.name}, shapes)"
                        if operation.output_shape
                        else None
                    ),
                ),
            ],
        )
        operations_module.add(
            operation_dataclass,
            "",
            "",
        )

    target_dir = build_dir / "services" / service_name
    prepare_build_sub_dir(target_dir, delete_files=["operations.py"])

    module_path = target_dir / "operations.py"
    operations_module.write_to(module_path)
    log.info(f"Output written to {module_path}")

    return module_path, f"{generated_package}.services.{service_name}.operations"


if __name__ == "__main__":
    main()

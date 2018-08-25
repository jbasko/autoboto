import os
from pathlib import Path
from typing import List

from botocore import xform_name
from botocore.model import Shape

from .boto_helpers import ServiceModel
from .core import build_dir, GeneratedDataclass, generate_dataclass, CodeBlock, GeneratedMethod
from .log import log


def prepare_build_sub_dir(sub_dir: Path, delete_files: List[str]):
    assert build_dir in sub_dir.parents

    if not build_dir.exists():
        os.makedirs(build_dir)
        log.info(f"Created build directory {build_dir}")

    if not sub_dir.exists():
        os.makedirs(sub_dir)
        log.info(f"Created build sub-directory {sub_dir}")

    sub_dir.touch("__init__.py")

    for f in delete_files:
        fp = (sub_dir / f).resolve()
        assert sub_dir in fp.parents
        if fp.exists():
            fp.unlink()
            log.info(f"Deleted {fp}")


def generate_service_shapes(service_name, generated_package="autoboto"):
    shapes_module = CodeBlock(
        "import datetime",
        "from typing import Any, List",
        "",
        "import dataclasses",
        "from autoboto.permanent.falsey import NOT_SET",
        "",
        "",
    )

    service_model = ServiceModel(service_name)
    for shape_name in service_model.shape_names:
        shape = service_model.shape_for(shape_name)

        if type(shape) is Shape:
            log.debug(f"Skipping primitive shape {shape}")
            continue

        dc_def = GeneratedDataclass(
            name=shape_name,
            documentation=shape.documentation,
        )

        dc_def.generate_fields_from_shape(shape)

        shapes_module.add(generate_dataclass(dc_def))
        shapes_module.add("")
        shapes_module.add("")

    target_dir = build_dir / "services" / service_name
    prepare_build_sub_dir(target_dir, delete_files=["shapes.py"])

    module_path = target_dir / "shapes.py"
    with open(module_path, "w", encoding="utf-8") as f:
        code = str(shapes_module).rstrip()
        f.write(code)
        f.write("\n")

    log.info(f"Output ({len(code)} characters) written to {module_path}")

    return module_path, f"{generated_package}.services.{service_name}.shapes"


def generate_service_operations(service_name, generated_package="autoboto"):
    operations_module = CodeBlock(
        "import datetime",
        "from typing import Any",
        "",
        "import boto3",
        "import dataclasses",
        "from autoboto.permanent import helpers",
        "from autoboto.permanent.falsey import NOT_SET",
        "",

        # Needed to pass shapes to transform_response
        f"import {generated_package}.services.{service_name}.shapes as shapes",
        
        # The alternative -- "from . import shapes" -- requires conditional code in return type annotations
        # to prefix shape class references with "shapes." when outside the shapes module.
        f"from {generated_package}.services.{service_name}.shapes import *",

        "",
        "",
    )

    # TODO Actually, Operations class can be in a permanent module because there is nothing dynamic about it.
    # TODO except the client but that is a bad design anyway as users should have a chance to customise the client.
    operations_module.add(
        "@dataclasses.dataclass",
        CodeBlock("class Operation:").consisting_of(
            f"_service_client = boto3.client(\"{service_name}\")",
            "_service_method_name = None",
            "",
            CodeBlock("def execute(self):").consisting_of(
                "params = {k: v for k, v in dataclasses.asdict(self).items() if v != NOT_SET}",
                CodeBlock("return getattr(self._service_client, self._service_method_name)(**params)"),
            ),
        ),
        "",
        "",
    )

    service_model = ServiceModel(service_name)
    for name in service_model.operation_names:
        operation = service_model.operation_model(name)

        dc_def = GeneratedDataclass(
            name=operation.name,
            documentation=operation.documentation,
            bases=["Operation"],
        )

        dc_def.before_fields.add(f"_service_method_name = {xform_name(operation.name)!r}")
        dc_def.before_fields.add("")

        dc_def.generate_fields_from_shape(operation.input_shape)

        # Custom execute() method is needed only if the service operation actually returns something
        if operation.output_shape:
            dc_def.after_fields.add("")
            dc_def.after_fields.add(CodeBlock(f"def execute(self) -> {operation.output_shape.name}:").consisting_of(
                "response = super().execute()",
                f"return helpers.transform_response(response, {operation.output_shape.name}, shapes)",  # noqa
            ))

        operations_module.add(generate_dataclass(dc_def))
        operations_module.add("")
        operations_module.add("")

    target_dir = build_dir / "services" / service_name
    prepare_build_sub_dir(target_dir, delete_files=["operations.py"])

    module_path = target_dir / "operations.py"
    with open(module_path, "w", encoding="utf-8") as f:
        code = str(operations_module).rstrip()
        f.write(code)
        f.write("\n")

    log.info(f"Output ({len(code)} characters) written to {module_path}")

    return module_path, f"{generated_package}.services.{service_name}.operations"


if __name__ == "__main__":
    generate_service_shapes("s3")
    generate_service_operations("s3")

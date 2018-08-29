import typing
from pathlib import Path

from botocore import xform_name
from botocore.model import StructureShape

from autoboto.permanent.falsey import NOT_SPECIFIED
from indentist import CodeGenerator, Constants, Parameter

from .boto_helpers import ServiceModel, iter_sorted_members
from .log import log


class Autoboto(CodeGenerator):

    build_dir = Path(__file__).resolve().parents[2] / "build"  # type: Path

    def __init__(self, generated_package="autoboto"):
        super().__init__()
        self.generated_package = generated_package
        self._service_models = {}

    def generate_service(self, service_name):
        self.generate_service_package(service_name)
        self.generate_service_shapes(service_name)
        self.generate_service_client(service_name)

    def get_service_model(self, service_name) -> ServiceModel:
        if service_name not in self._service_models:
            self._service_models[service_name] = ServiceModel(service_name)
        return self._service_models[service_name]

    def generate_service_client(self, service_name):
        client_module = self.module(
            name="client",
            imports=[
                "import datetime",
                "import typing",
                "import boto3",
                "from indentist import Constants",  # TODO temporary
                "from . import shapes",
            ],
        )

        client_class = self.class_(
            name="Client",
        ).add(
            self.func("__init__", params=["self", "*args", "**kwargs"]).of(
                f"self._service_client = boto3.client({service_name!r}, *args, **kwargs)",
            ),
            "",
            indentation=1,
        )

        for operation in self.get_service_model(service_name).iter_operations():

            # Generate a method which takes keyword arguments with:
            # 1) required arguments not having any defaults set
            # 2) optional arguments having default value set to Constants.VALUE_NOT_SET

            params = [Parameter.SELF]
            for member in iter_sorted_members(operation.input_shape):
                params.append(Parameter(
                    name=member.name,
                    type_=member.type_annotation,
                    default=Constants.DEFAULT_NOT_SET if member.is_required else Constants.VALUE_NOT_SET,
                    required=member.is_required,
                    documentation=member.documentation,
                ))

            documentation = self.block().add(
                self.html_string(operation.documentation),
                *(
                    self.block(f":param {p.name}:").add(
                        p.documentation,
                        indentation=1,
                    ).add(
                        f":type {p.name}: {p.to_sig_part()}",
                    )
                    for p in params
                    if p.documentation
                )
            )
            client_class.add(
                self.func(xform_name(operation.name), params=params, doc=documentation).of(
                    self.dict_from_locals(
                        name="method_params",
                        params=params[1:],  # exclude self
                    ),
                    f"response = self._service_client.{xform_name(operation.name)}(**method_params)",
                    (
                        f"return shapes.{operation.output_shape.name}.from_dict(response)"
                        if operation.output_shape else
                        "return response"
                    )
                ),
                "",
                indentation=1,
            )

        client_module.add(client_class)

        target_dir = self.build_dir / "services" / service_name
        self.prepare_build_sub_dir(target_dir, delete_files=["client.py"])

        module_path = target_dir / "client.py"
        client_module.write_to(module_path)

        return module_path, f"{self.generated_package}.services.{service_name}.client"

    def generate_service_package(self, service_name):
        target_dir = self.build_dir / "services" / service_name
        self.prepare_build_sub_dir(target_dir, delete_files=["__init__.py"])

        init_module = self.module(
            name="__init__",
            imports=[
                "from .client import Client",
            ],
        ).add(
            self.block("__all__ = [", closed_by="]").of(
                '"Client",',
            ),
        )
        init_module.write_to(target_dir / "__init__.py")

    def generate_service_shapes(self, service_name):
        shapes_module = self.module(
            name="shapes",
            imports=[
                "import datetime",
                "import sys",
                "import dataclasses",
                "from autoboto.permanent.falsey import NOT_SET",
            ],
        )

        shapes_module.add(
            """\
            @dataclasses.dataclass
            class _Shape:
                @classmethod
                def from_dict(cls, payload) -> "_Shape":
                    payload = payload or {}
                    parsed = {}
                    for f in dataclasses.fields(cls):
                        if f.name in payload:
                            shape_type = f.metadata.get("shape_type", None)
                            if shape_type and payload[f.name] is not None:
                                item_cls_name = f.metadata.get("shape_item_cls_name", None)
                                item_cls = getattr(sys.modules[__name__], item_cls_name)
                                if shape_type is list:
                                    parsed[f.name] = [item_cls.from_dict(item) for item in payload[f.name]]
                                else:
                                    parsed[f.name] = item_cls.from_dict(payload[f.name])
                            else:
                                parsed[f.name] = payload[f.name]
                    return cls(**parsed)
            """
        )

        for shape in self.get_service_model(service_name).iter_shapes():
            if not isinstance(shape, StructureShape):
                log.debug(f"Skipping non-StructureShape {shape}")
                continue

            shape_dataclass = self.generate_dataclass_v2(
                name=shape.name,
                bases=["_Shape"],
                documentation=shape.documentation,
                fields=iter_sorted_members(shape),
            )

            shape_dataclass.add(
                f"""\
                @classmethod
                def from_dict(cls, payload) -> "{shape.name}":
                    return super().from_dict(payload)
                """,
                indentation=1,
            )

            shapes_module.add(shape_dataclass)

        target_dir = self.build_dir / "services" / service_name
        self.prepare_build_sub_dir(target_dir, delete_files=["shapes.py"])

        module_path = target_dir / "shapes.py"
        shapes_module.write_to(module_path)
        log.info(f"Output written to {module_path}")

        return module_path, f"{self.generated_package}.services.{service_name}.shapes"

    def generate_service_operations(self, service_name):
        operations_module = self.module(
            name="operations",
            # TODO add imports where necessary and let indentist calculate the imports required for the module
            imports=[
                "import datetime",
                "import typing",
                "from autoboto.permanent import helpers",
                "from autoboto.permanent.falsey import NOT_SET",
                f"from {self.generated_package}.services.{service_name} import shapes",
            ],
        )

        operations_module.add(
            self.dataclass("Operation").of(
                "_service_method_name = None",
                "",
                self.func("execute", params=["self", "client=None"], return_type=typing.Dict).of(
                    "params = {k: v for k, v in dataclasses.asdict(self).items() if v != NOT_SET}",
                    "return getattr(client, self._service_method_name)(**params)",
                ),
                "",
                "",
            ),
        )

        for operation in self.get_service_model(service_name).iter_operations():
            return_type_for_execute = Constants.DEFAULT_NOT_SET
            if operation.output_shape:
                return_type_for_execute = f"shapes.{operation.output_shape.name}"

            operation_dataclass = self.generate_dataclass_v2(
                name=operation.name,
                documentation=operation.documentation,
                bases=["Operation"],
                before_fields=[
                    self.block(
                        f"_service_method_name = {xform_name(operation.name)!r}",
                    ),
                ],
                fields=iter_sorted_members(operation.input_shape),
                after_fields=[
                    "",
                    self.func(name="execute", params=["self", "client=None"], return_type=return_type_for_execute).of(
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

        target_dir = self.build_dir / "services" / service_name
        self.prepare_build_sub_dir(target_dir, delete_files=["operations.py"])

        module_path = target_dir / "operations.py"
        operations_module.write_to(module_path)
        log.info(f"Output written to {module_path}")

        return module_path, f"{self.generated_package}.services.{service_name}.operations"

    def generate_dataclass_v2(
        self,
        name,
        bases=None,
        documentation=None,
        fields=None,
        before_fields=None,
        after_fields=None,
    ):
        return self.dataclass(
            name=name,
            bases=bases,
            doc=documentation,
        ).add(
            *(before_fields if before_fields else ()),
            *(
                self.dataclass_field(
                    name=field.name,
                    type_=field.type_annotation,
                    default=field.default,
                    default_factory=field.default_factory,
                    doc=field.documentation,
                    metadata=field.metadata,
                    not_set_values=[NOT_SPECIFIED],
                )
                for field in fields or ()
            ),
            *(after_fields if after_fields else ()),
            indentation=1,
        )

import collections
import datetime
import keyword
import os
import re
from pathlib import Path
from typing import Dict

from botocore import xform_name

from botogen.indentist import CodeGenerator, Literal, Parameter

from .ab import AbOperationModel, AbServiceModel, AbShape
from .config import BotogenConfig
from .log import log


def identity_func(s):
    return s


def prepare_numeric_enum_value_name(value):
    value = re.sub(r"[^a-zA-Z\d_]", "_", value)
    return f"VALUE_OF_{value}"


class ServiceGenerator(CodeGenerator):

    def __init__(self, service_name: str, botogen):
        super().__init__()

        self.documention_input_is_html = True

        from .botogen import Botogen
        self.botogen: Botogen = botogen

        self.service_name: str = service_name
        self.service_model = AbServiceModel(service_name)
        self.shapes: Dict[str, AbShape] = collections.OrderedDict()
        self.operations: Dict[str, AbOperationModel] = collections.OrderedDict()
        self.paginated_output_shapes = set()

        self.load_service_definition()

    @property
    def config(self) -> BotogenConfig:
        return self.botogen.config

    def run(self):
        log.info(f"generating service {self.service_name}")

        service_package_init = self.module(
            name="__init__",
            imports=[
                "from .client import Client",
                "from . import shapes",
            ],
        )
        service_package_init.add(f"""\
            __all__ = [
                \"Client\",
                \"shapes\",
            ]
        """)
        service_package_init.write_to(self.service_build_dir / "__init__.py")

        shapes_module = self.generate_shapes_module()
        shapes_path = self.service_build_dir / "shapes.py"
        shapes_module.write_to(shapes_path, format=self.config.yapf_style)

        client_module = self.generate_client_module()
        client_path = self.service_build_dir / "client.py"
        client_module.write_to(client_path, format=self.botogen.config.yapf_style)

    def generate_shapes_module(self):
        module = self.module(
            name="shapes",
            imports=[
                "import datetime",
                "import typing",
                f"from {self.botogen.target_autoboto_package_name} import ShapeBase, OutputShapeBase, TypeInfo",
            ]
        )

        for shape in self.shapes.values():

            if shape.is_enum:
                enum_cls = module.class_(
                    name=shape.name,
                    bases=["str"],
                    doc=shape.documentation,
                )

                if any(keyword.iskeyword(value) for value in shape.enum):
                    transform = str.upper
                elif any(re.match(r"^\d.+", value) for value in shape.enum):
                    transform = prepare_numeric_enum_value_name
                else:
                    transform = identity_func

                for value in shape.enum:
                    # Some enum values have dashes.
                    # s3.Event enum has values like "s3:ObjectCreated:*"
                    safe_value = transform(value).replace("*", "Wildcard")
                    safe_value = re.sub(r"[^a-zA-Z0-9_]", "_", safe_value)
                    enum_cls.add(
                        f"{safe_value} = \"{value}\"",
                        indentation=1,
                    )

            elif shape.is_primitive:
                continue

            elif shape.type_name == "list":
                continue

            elif shape.type_name == "map":
                continue

            elif shape.type_name == "structure":
                if shape.is_output_shape:
                    shape_bases = ["OutputShapeBase"]
                else:
                    shape_bases = ["ShapeBase"]

                cls = module.dataclass(
                    name=shape.name,
                    doc=shape.documentation,
                    bases=shape_bases,
                )

                cls.func("_get_boto_mapping", decorators=["@classmethod"], params=["cls"]).of(
                    self.block("return [", closed_by="]").of(*(
                        (
                            f"("
                            f"\"{self.make_shape_attribute_name(member.name)}\", "
                            f"\"{member.name}\", "
                            f"TypeInfo({self.type_annotation_for_shape(member.shape.name, quoted=False)}),"
                            f"),"
                        )
                        for member in shape.sorted_members
                    )),
                )

                for member in shape.sorted_members:
                    field_defaults = {
                        "default": "ShapeBase.NOT_SET",
                    }
                    cls.field(
                        name=self.make_shape_attribute_name(member.name),
                        type_=self.type_annotation_for_shape(member.shape.name),
                        doc=member.documentation,
                        **field_defaults,
                    )

                if shape.name in self.paginated_output_shapes:
                    cls.func(
                        name="paginate",
                        params=["self"],
                        return_type=f"typing.Generator[\"{shape.name}\", None, None]",
                    ).of(
                        "yield from super()._paginate()"
                    )

            elif shape.type_name == "blob":
                module.add_to_imports("import botocore.response")
                module.class_(
                    name=shape.name,
                    bases=["botocore.response.StreamingBody"],
                    doc=shape.documentation,
                )

            else:
                raise ValueError({
                    "shape.name": shape.name,
                    "shape.type_name": shape.type_name,
                })

        return module

    def generate_client_module(self):
        module = self.module(
            name="client",
            imports=[
                "import datetime",
                "import typing",
                "import boto3",
                f"from {self.botogen.target_autoboto_package_name} import ClientBase, ShapeBase, OutputShapeBase",
                "from . import shapes",
            ],
        )

        client_cls = module.class_(
            name="Client",
            bases=["ClientBase"],
        )

        client_cls.func("__init__", params=["self", "*args", "**kwargs"]).of(
            f"super().__init__(\"{self.service_name}\", *args, **kwargs)"
        )

        for operation in self.operations.values():
            params = []

            operation_method_name = xform_name(operation.name)
            operation_method_params = ["self"]
            paginator_model = operation.get_paginator()

            if operation.input_shape:
                operation_method_params.append(Parameter(
                    name="_request",
                    type_=f"shapes.{operation.input_shape.name}",
                    default=None,
                ))

                for member in operation.input_shape.sorted_members:
                    params.append(Parameter(
                        name=self.make_shape_attribute_name(member.name),
                        type_=self.type_annotation_for_shape(member.shape.name, quoted=False, ns="shapes."),
                        required=member.is_required,
                        default=Literal("ShapeBase.NOT_SET"),
                        documentation=member.documentation,
                    ))

            if params:
                operation_method_params.append("*")
                operation_method_params.extend(params)

            operation_func = client_cls.func(
                name=operation_method_name,
                params=operation_method_params,
                doc=operation.documentation,
                return_type=(
                    f"shapes.{operation.output_shape.name}"
                    if operation.output_shape else
                    None
                )
            )

            if operation.input_shape:
                operation_func.block("if _request is None:").of(
                    self.dict_from_locals(
                        name="_params",
                        params=params,
                        not_specified_literal="ShapeBase.NOT_SET"
                    ),
                    f"_request = shapes.{operation.input_shape.name}(**_params)",
                )
                if operation.output_shape and paginator_model:
                    operation_func.add(f"""\
                        paginator = self.get_paginator("{operation_method_name}").paginate(**_request.to_boto())
                        page_generator = (page for page in paginator)
                        first_page = next(page_generator)
                        result = shapes.{operation.output_shape.name}.from_boto(first_page)
                        result._page_iterator = page_generator
                        return result
                    """, indentation=1)
                else:
                    operation_func.add(f"""\
                        response = self._boto_client.{operation_method_name}(**_request.to_boto())
                    """, indentation=1)
            else:
                operation_func.add(f"""\
                    response = self._boto_client.{operation_method_name}()
                """, indentation=1)

            if operation.output_shape:
                operation_func.add(f"""\
                    return shapes.{operation.output_shape.name}.from_boto(response)
                """, indentation=1)

        return module

    def load_service_definition(self):
        for name in self.service_model.shape_names:
            shape = self.service_model.shape_for(name)
            self.shapes[name] = shape
        for name in self.service_model.operation_names:
            self.operations[name] = self.service_model.operation_model(name)
            if self.operations[name].get_paginator():
                # Mark paginated shapes for which we need to generate the paginate() method.
                self.paginated_output_shapes.add(self.operations[name].output_shape.name)

    def type_annotation_for_shape(self, shape_name, quoted=True, ns="") -> str:
        shape = self.shapes[shape_name]
        q = "\"" if quoted else ""
        if shape.is_enum:
            return f"typing.Union[str, {q}{ns}{shape.name}{q}]"
        elif shape.type_name in AbShape.PRIMITIVE_TYPES:
            type_ = AbShape.PRIMITIVE_TYPES[shape.type_name]
            if type_ is datetime.datetime:
                return "datetime.datetime"
            else:
                return type_.__name__
        elif shape.type_name == "list":
            return f"typing.List[{self.type_annotation_for_shape(shape.member.name, quoted=quoted, ns=ns)}]"
        elif shape.type_name == "structure":
            return f"{q}{ns}{shape.name}{q}"
        elif shape.type_name == "map":
            return (
                f"typing.Dict[{self.type_annotation_for_shape(shape.key.name, quoted=quoted, ns=ns)}, "
                f"{self.type_annotation_for_shape(shape.value.name, quoted=quoted, ns=ns)}]"
            )
        else:
            return "typing.Any"

    @property
    def service_build_dir(self) -> Path:
        path = self.botogen.get_autoboto_path(f"services/{self.service_name}")
        if not path.exists():
            os.makedirs(path)
        (path / "__init__.py").touch()
        return path

    def make_shape_attribute_name(self, name, containing_class=None):
        name = xform_name(name)
        if keyword.iskeyword(name):
            name = name + "_"  # "and" becomes "and_"
        if containing_class is not None and hasattr(containing_class, name):
            log.warning(
                f"{containing_class} has attribute {name!r} so we are appending \"_\" to the shape attribute name"
            )
            name = name + "_"
        return name

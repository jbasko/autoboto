import textwrap
from pathlib import Path

import dataclasses
from botocore.model import Shape, StructureShape
from html2text import html2text

from autoboto.permanent.falsey import NOT_SET, NOT_SPECIFIED
from .log import log


build_dir = Path(__file__).resolve().parents[2] / "build"  # type: Path


class CodeBlock:
    def __init__(self, *blocks):
        self._blocks = []

        for block in blocks:
            self.add(block)

    def __bool__(self):
        return bool(self._blocks)

    def add_indented(self, *blocks, indentation=1):
        for block in blocks:
            if block is not None:
                self._blocks.append([indentation, block])
        return self

    def add(self, *blocks):
        return self.add_indented(*blocks, indentation=0)

    def close(self, close_str=")"):
        """
        If the last block is not indented, this will add the close_str to
        the last block, otherwise will add a new unindented block.
        """
        if self._blocks[-1][0] == 0:
            self._blocks[-1][1] += close_str
        else:
            self.add(close_str)
        return self

    def consisting_of(self, *blocks):
        for block in blocks:
            self.add_indented(block)
        return self

    def to_lines(self, indentation=0):
        lines = []
        for block_indentation, block in self._blocks:
            if isinstance(block, str):
                lines.append(textwrap.indent(
                    textwrap.dedent(block),
                    (indentation + block_indentation) * "    ",
                ))
            else:
                lines.extend(block.to_lines(indentation=indentation + block_indentation))
        if not lines:
            lines.append(indentation * "    " + "pass")
        return lines

    def __str__(self):
        return "\n".join(self.to_lines())


def format_doc_str(doc_str):
    return "\n".join(textwrap.wrap(html2text(doc_str), 100))


@dataclasses.dataclass
class GeneratedMethod:
    name: str
    documentation: str = None


@dataclasses.dataclass
class GeneratedDataclass:
    name: str

    # Names of base classes
    bases: list = None

    documentation: str = None

    before_fields: CodeBlock = dataclasses.field(default_factory=CodeBlock)

    fields: list = dataclasses.field(default_factory=list)

    after_fields: CodeBlock = dataclasses.field(default_factory=CodeBlock)

    def generate_fields_from_shape(self, shape: Shape):
        """
        Given a Shape, create a field for each its member.
        """

        if type(shape) is StructureShape:
            required_members = [
                (name, member)
                for name, member in shape.members.items()
                if name in shape.required_members
            ]
            for name, member in required_members:
                self.fields.append(ShapeField(
                    name=name,
                    shape=member,
                ))

            other_members = [
                (name, member)
                for name, member in shape.members.items()
                if name not in shape.required_members
            ]
            for name, member in other_members:
                self.fields.append(ShapeField(
                    name=name,
                    shape=member,
                ))

        else:
            log.debug(f"Nothing to generate for {shape}")


@dataclasses.dataclass
class ShapeField:
    name: str
    shape: Shape

    @property
    def default(self):
        type_name = self.shape.type_name
        if type_name == "list":
            return NOT_SPECIFIED
        else:
            return NOT_SET

    @property
    def default_factory(self):
        type_name = self.shape.type_name
        if type_name == "list":
            return "list"
        else:
            return NOT_SPECIFIED

    @property
    def metadata(self):
        return NOT_SPECIFIED

    @property
    def documentation(self):
        return self.shape.documentation

    @property
    def type_annotation(self):
        type_name = self.shape.type_name
        if type_name in ("integer", "long"):
            return "int"
        elif type_name == "string":
            return "str"
        elif type_name == "timestamp":
            return "datetime.datetime"
        elif type_name == "structure":
            return f'"{self.shape.name}"'
        elif type_name == "list":
            return f"List[\"{self.shape.member.name}\"]"
        elif type_name == "boolean":
            return "bool"
        elif type_name == "map":
            return "dict"
        elif type_name == "blob":
            return "Any"
        else:
            raise ValueError(type_name)


def generate_dataclass(dc_class: GeneratedDataclass):
    class_block = CodeBlock(
        "@dataclasses.dataclass",
        f"class {dc_class.name}{'(' + ', '.join(dc_class.bases) + ')' if dc_class.bases else ''}:",
    )

    fields_block = CodeBlock()
    for field in dc_class.fields:
        if field.documentation:
            fields_block.add("")
            fields_block.add(textwrap.indent(format_doc_str(field.documentation), "# "))
        fields_block.add(
            CodeBlock(f"{field.name}: {field.type_annotation} = dataclasses.field(").consisting_of(
                f"default={field.default!r}," if field.default is not NOT_SPECIFIED else None,
                f"default_factory={field.default_factory}," if field.default_factory is not NOT_SPECIFIED else None,
                f"metadata={field.metadata!r}," if field.metadata is not NOT_SPECIFIED else None,
            ).close(")")
        )

    documentation = None
    if dc_class.documentation:
        documentation = CodeBlock(
            '"""',
            format_doc_str(dc_class.documentation),
            '"""',
        )

    return class_block.consisting_of(
        documentation,
        dc_class.before_fields if dc_class.before_fields else None,
        fields_block,
        dc_class.after_fields if dc_class.after_fields else None,
    )

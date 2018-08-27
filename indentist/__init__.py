import builtins
import textwrap
from pathlib import Path
from typing import Any, GenericMeta, Type

import dataclasses


DEFAULT_NOT_SET = object()


def join_lines(*lines):
    """
    Join lines with "\n", but skip lines that are None.

    This is useful when generating lines in conditional code:

        join_lines(
            "import logging" if "logging" in imports else None,
        )

    """
    return "\n".join(line for line in lines if line is not None)


def dataclass_field_is_required(field: dataclasses.Field):
    return field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING


def type_to_sig_part(type_):
    if isinstance(type_, GenericMeta):
        return str(type_)
    elif isinstance(type_, type):
        return type_.__name__
    elif isinstance(type_, str):
        return type_
    else:
        raise ValueError(type_)


@dataclasses.dataclass
class Parameter:
    name: str
    type_: Type
    default: Any = DEFAULT_NOT_SET

    class literal:
        """
        When you need to pass a default value that should be printed as is, not quoted.
        """
        def __init__(self, value: str):
            self.value = value

        def __str__(self):
            return self.value

        def __repr__(self):
            return self.value

    NOT_SET = literal("Parameter.NOT_SET")

    def to_sig_part(self):
        # if self.default is not DEFAULT_NOT_SET and self.default is not dataclasses.MISSING:
        if self.default is not dataclasses.MISSING:
            default = f"={self.default!r}"
        else:
            default = ""
        return f"{self.name}: {type_to_sig_part(self.type_)}{default}"


@dataclasses.dataclass
class Context:
    imports: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class CodeBlock:
    name: str = None
    imports: list = dataclasses.field(default_factory=list)
    decorators: list = dataclasses.field(default_factory=list)
    doc: str = None
    _blocks: list = dataclasses.field(default_factory=list)
    indented: bool = False

    opening: str = None  # only used when name != opening, favour overriding get_opening
    closing: str = None

    # A list of values that should be interpreted as not set in addition to indentist's own DEFAULT_NOT_SET.
    not_set_values: list = dataclasses.field(default_factory=list)

    @classmethod
    def module(cls, name, **kwargs) -> "ModuleCodeBlock":
        return ModuleCodeBlock(name, **kwargs)

    @classmethod
    def block(cls, name=None, *blocks, **kwargs) -> "CodeBlock":
        """
        Create a new code block with the specified sub-blocks.

        Examples:

            block("for x in range(42):").of(
                "y = x * 2",
                "print(x)",
            )

            block("[", closing="]").of(*items)

        """
        code = CodeBlock(name=name, **kwargs)
        for block in blocks:
            code._blocks.append((0, block))
        return code

    @classmethod
    def class_(
            cls,
            name: str = Parameter.NOT_SET,
            imports: list = Parameter.NOT_SET,
            decorators: list = Parameter.NOT_SET,
            doc: str = Parameter.NOT_SET,
            _blocks: list = Parameter.NOT_SET,
            indented: bool = Parameter.NOT_SET,
            opening: str = Parameter.NOT_SET,
            closing: str = Parameter.NOT_SET,
            not_set_values: list = Parameter.NOT_SET,
            bases: list = Parameter.NOT_SET,
    ) -> "ClassCodeBlock":
        params_for_dataclass = {}
        if name != Parameter.NOT_SET:
            params_for_dataclass['name'] = name
        if imports != Parameter.NOT_SET:
            params_for_dataclass['imports'] = imports
        if decorators != Parameter.NOT_SET:
            params_for_dataclass['decorators'] = decorators
        if doc != Parameter.NOT_SET:
            params_for_dataclass['doc'] = doc
        if _blocks != Parameter.NOT_SET:
            params_for_dataclass['_blocks'] = _blocks
        if indented != Parameter.NOT_SET:
            params_for_dataclass['indented'] = indented
        if opening != Parameter.NOT_SET:
            params_for_dataclass['opening'] = opening
        if closing != Parameter.NOT_SET:
            params_for_dataclass['closing'] = closing
        if not_set_values != Parameter.NOT_SET:
            params_for_dataclass['not_set_values'] = not_set_values
        if bases != Parameter.NOT_SET:
            params_for_dataclass['bases'] = bases
        return ClassCodeBlock(**params_for_dataclass)

    @classmethod
    def def_(cls, *args, **kwargs) -> "DefCodeBlock":
        return DefCodeBlock(*args, **kwargs)

    @classmethod
    def dict(cls, *args, **kwargs) -> "DictCodeBlock":
        return DictCodeBlock(*args, **kwargs)

    @classmethod
    def dataclass(cls, *args, **kwargs) -> "DataclassCodeBlock":
        return DataclassCodeBlock(*args, **kwargs)

    @classmethod
    def dataclass_field(cls, *args, **kwargs) -> "DataclassFieldCodeBlock":
        return DataclassFieldCodeBlock(*args, **kwargs)

    def of(self, *indented_blocks) -> "CodeBlock":
        """
        Add sub-blocks with one level of indentation relative to the parent block.
        Nones are skipped.
        For custom indentation, use the add() method.

        Returns the parent block itself, useful for chaining.
        """
        for block in indented_blocks:
            if block is not None:
                self._blocks.append((1, block))
        return self

    def add(self, *blocks, indentation="default") -> "CodeBlock":
        """
        Add sub-blocks. If indentation is "default", the sub-block indentation depends on
        parent block's "indented" attribute -- if parent block is marked as indented,
        sub-blocks will be indented.

        Nones are skipped.

        Returns the parent block itself, useful for chaining.
        """
        if indentation == "default":
            indentation = 1 if self.indented else 0

        for block in blocks:
            if block is not None:
                self._blocks.append((indentation, block))
        return self

    def get_opening(self):
        """
        The opening is usually a single-line string that starts the unique part of the code construct.
        If you have a multi-line construct, don't use opening for that, instead return None
        in get_opening() and override get_blocks().
        """
        return self.opening or self.name or ""

    def to_lines(self, context: Context, indentation=0):
        # Do not override this.

        for block_indentation, block in self.get_blocks():
            if block is None:
                continue
            prefix = (indentation + block_indentation) * "    "
            if isinstance(block, str):
                # The dedent is to allow passing multi-line strings with triple-quotes around them.
                yield textwrap.indent(textwrap.dedent(block), prefix)
            elif isinstance(block, CodeBlock):
                yield textwrap.indent(block.to_code(context=context), prefix)
            else:
                raise ValueError(block)

    def get_blocks(self):
        """
        Override this method for custom content.
        If you override it, you are responsible for adding pass to empty blocks which require it.
        """

        if self.indented and self.doc:
            yield 1, join_lines(
                '"""',
                textwrap.dedent(self.doc.strip()),
                '"""',
            )

        yield from self._blocks

        if self.indented and not self._blocks:
            yield 1, "pass"

    def to_code(self, context: Context=None):
        """
        Generate the code and return it as a string.
        """
        # Do not override this method!

        context = context or Context()
        for imp in self.imports:
            if imp not in context.imports:
                context.imports.append(imp)

        before_opening = ""
        if self.decorators:
            before_opening = join_lines(*self.decorators)

        opening = self.get_opening() or ""
        if before_opening and opening:
            full_opening = before_opening + "\n" + opening
        else:
            full_opening = before_opening + opening

        lines = list(self.to_lines(context=context))
        closing = self.closing

        if not lines:
            if closing:
                return full_opening + closing
            elif self.indented:
                return join_lines(full_opening, "    pass")
            else:
                return full_opening
        else:
            # newlines won't be generated for Nones
            return join_lines(
                full_opening or None,
                *lines,
                closing or None,
            )

    def exec(self, globals=None, locals=None):
        if locals is None:
            locals = {}
        builtins.exec(self.to_code(), globals, locals)
        return locals

    def add_to_imports(self, import_line):
        if "import" not in import_line:
            raise ValueError(import_line)
        if import_line not in self.imports:
            self.imports.append(import_line)

    def add_to_decorators(self, decorator_line):
        if decorator_line not in self.decorators:
            self.decorators.append(decorator_line)

    def is_set(self, value):
        """
        Returns True if the value is NOT one of the values that this CodeBlock is meant to interpret as not set.
        """
        return value not in self.not_set_values and value is not DEFAULT_NOT_SET


@dataclasses.dataclass
class ClassCodeBlock(CodeBlock):
    bases: list = dataclasses.field(default_factory=list)
    indented: bool = True

    def get_opening(self):
        bases = []
        for b in self.bases or ():
            if isinstance(b, type):
                bases.append(b.__name__)
            else:
                bases.append(b)

        if bases:
            return f"class {self.name}({', '.join(bases)}):"
        else:
            return f"class {self.name}:"


@dataclasses.dataclass
class DefCodeBlock(CodeBlock):
    params: list = dataclasses.field(default_factory=list)
    return_type: Any = DEFAULT_NOT_SET
    indented: bool = True

    @property
    def return_annotation(self):
        if self.return_type is DEFAULT_NOT_SET:
            return ""
        else:
            return f" -> {type_to_sig_part(self.return_type)}"

    def get_opening(self):
        return None

    def get_blocks(self):
        params = []
        for p in self.params:
            if isinstance(p, Parameter):
                params.append(p.to_sig_part())
            else:
                params.append(p)

        params_str = ", ".join(params)

        if len(params_str) + len(self.return_annotation) < 40:
            yield 0, f"def {self.name}({params_str}){self.return_annotation}:"
        else:
            yield 0, CodeBlock(f"def {self.name}(", closing=f"){self.return_annotation}:").of(
                *(f"{p}," for p in params)
            )

        yield from super().get_blocks()


@dataclasses.dataclass
class DictCodeBlock(CodeBlock):
    items: dict = None
    literal_items: dict = None
    indented: bool = True
    closing: str = "}"

    def get_opening(self):
        if self.name:
            return f"{self.name} = {{"
        else:
            return "{"

    def get_blocks(self):
        # TODO Allow items to be code blocks!

        if self.items:
            for key, value in self.items.items():
                yield 1, f"{key!r}: {value!r},"

        if self.literal_items:
            for key, value in self.literal_items.items():
                yield 1, f"{key!r}: {value},"


@dataclasses.dataclass
class DataclassCodeBlock(ClassCodeBlock):

    def __post_init__(self):
        self.add_to_imports("import dataclasses")
        self.add_to_decorators("@dataclasses.dataclass")


@dataclasses.dataclass
class DataclassFieldCodeBlock(CodeBlock):
    type_: Any = None
    default: Any = dataclasses.field(default=DEFAULT_NOT_SET)
    default_factory: Any = dataclasses.field(default=DEFAULT_NOT_SET)
    init: bool = dataclasses.field(default=DEFAULT_NOT_SET)
    repr: bool = dataclasses.field(default=DEFAULT_NOT_SET)

    def __post_init__(self):
        self.add_to_imports("import dataclasses")
        self.add_to_imports("import typing")

    @property
    def type_annotation(self):
        return type_to_sig_part(self.type_)

    def get_opening(self):
        return None

    def get_blocks(self):
        if self.doc:
            yield 0, ""  # blank line before fields with doc string
            yield 0, textwrap.indent("\n".join(textwrap.wrap(self.doc, width=80, break_long_words=False)), "# ")

        if not self.is_custom:
            yield 0, f"{self.name}: {self.type_annotation}"
            return

        yield 0, CodeBlock(f"{self.name}: {self.type_annotation} = dataclasses.field(", closing=")").of(
            f"default={self.default_repr}," if self.is_set(self.default) else None,
            f"default_factory={self.default_factory_repr}," if self.is_set(self.default_factory) else None,
            f"init={self.init_repr}," if self.is_set(self.init) else None,
            f"repr={self.repr_repr}," if self.is_set(self.repr) else None,
        )

    @property
    def is_custom(self):
        return (
            self.is_set(self.default) or
            self.is_set(self.default_factory) or
            self.is_set(self.init) or
            self.is_set(self.repr)
        )

    @property
    def default_repr(self):
        return self.default

    @property
    def default_factory_repr(self):
        if callable(self.default_factory):
            return self.default_factory.__name__
        elif isinstance(self.default_factory, str):
            return self.default_factory
        else:
            raise ValueError(self.default_factory)

    @property
    def init_repr(self):
        return str(self.init)

    @property
    def repr_repr(self):
        return str(self.repr)


@dataclasses.dataclass
class ImportScopeCodeBlock(CodeBlock):
    def to_code(self, context: Context=None):
        context = context or Context()
        without_imports = super().to_code(context=context)
        return "\n".join(context.imports) + "\n\n\n" + without_imports


@dataclasses.dataclass
class ModuleCodeBlock(ImportScopeCodeBlock):
    def get_opening(self):
        return None

    def write_to(self, path: Path, encoding="utf-8"):
        with open(path, "w", encoding=encoding) as f:
            f.write(self.to_code().rstrip())
            f.write("\n")


def generate_dataclass_factory_delegate(dc, name=None, not_specified_literal=Parameter.NOT_SET):
    """
    Given a dataclass dc, generates code for a function that will take
    the fields of dc as optional keyword or positional arguments and forward
    to another function only those arguments for which values are supplied.
    """
    name = name or f"create_{dc.__name__.lower()}"

    params = []
    for f in dataclasses.fields(dc):
        is_required = dataclass_field_is_required(f)
        param = Parameter(
            name=f.name,
            type_=f.type,
            # We only want to require required fields. But for others we don't want to set them to defaults
            # because we want to distinguish between user not setting any value and user supplying a default value.
            # If user does not set any value then we shouldn't be passing anything to the dataclass initialiser
            # about the particular parameter.
            default=dataclasses.MISSING if is_required else Parameter.NOT_SET,
        )
        params.append(param)

    func = CodeBlock.def_(
        name=name,
        params=params,
        return_type=dc,
    ).of(
        "params_for_dataclass = {}"
    )

    for f in dataclasses.fields(dc):
        func.add(CodeBlock.block(f"if {f.name} != {not_specified_literal}:").of(
            f"params_for_dataclass[{f.name!r}] = {f.name}"
        ))

    func.add(f"return {dc.__name__}(**params_for_dataclass)")

    return func


def _generate_delegates_for_yourself():
    """
    Indentist uses itself (during development) to generate the factory methods above.
    """
    factory = generate_dataclass_factory_delegate(ClassCodeBlock)
    factory.add_to_decorators("@classmethod")
    factory.params.insert(0, "cls")
    print(factory.to_code())


if __name__ == "__main__":
    _generate_delegates_for_yourself()

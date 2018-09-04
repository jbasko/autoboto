import builtins
import textwrap
import typing
from pathlib import Path
from typing import Any, List

from html2text import html2text

from .constants import Constants
from .context import Context
from .parameters import Parameter, type_to_sig_part
from .strings import join_lines


class FinalisedBlocks:
    def __init__(self, blocks):
        self._blocks_ = blocks

    def __getitem__(self, item):
        return self._blocks_[item]

    def __iter__(self):
        return iter(self._blocks_)

    def append(self, *args):
        raise RuntimeError(f"This block has been finalised and sub-blocks can no longer be added to it.")

    def extend(self, *args):
        raise RuntimeError(f"This block has been finalised and sub-blocks can no longer be added to it.")


class AttrsMixin:
    def _has_attr(self, name):
        if name in self.__dict__:
            return True
        for cls in self.__class__.__mro__:
            if name in cls.__dict__:
                return True
        return False

    def _init_attrs(self, **attrs):
        for k in list(attrs.keys()):
            if self._has_attr(k):
                setattr(self, k, attrs.pop(k))
        for k in attrs.keys():
            raise AttributeError(k)
        return attrs

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class BlockBase(AttrsMixin):
    def __init__(self, **attrs):
        from .code_generator import CodeGenerator
        self.code: CodeGenerator = attrs.pop("code")
        self._init_attrs(**attrs)


class Counter:
    def __init__(self, num_blocks=0, num_indented_blocks=0, num_nones=0, num_indented_non_doc_blocks=0):
        # Total number of non-None blocks
        self.num_blocks = num_blocks

        # Number of blocks that were indented relative to current indentation
        self.num_indented_blocks = num_indented_blocks

        # It's nice to have a "pass" even when a method or class has a triple-quoted doc string.
        self.num_indented_non_doc_blocks = num_indented_non_doc_blocks

        # Number of Nones passed as blocks (only useful for debugging)
        self.num_nones = num_nones


class CodeBlock(BlockBase):
    """
    Represents a generic block of code. Do not instantiate directly.
    Instead, create blocks with factory methods available on Context.
    """

    closed_by = None

    # Set to True if the code block expects a non-empty, indented body.
    # For a generic instance of CodeBlock, this is implicitly set to True
    # as soon as of() method is called on the instance.
    expects_body_or_pass = None

    def __init__(self, **kwargs):

        self.name = None

        self._blocks = []
        self._suffix = ""  # custom suffix to the generated code, to be used only internally for things like commas.

        self.closed_by = self.closed_by  # Default to the value of the class attribute
        self.expects_body_or_pass = self.expects_body_or_pass  # Default to the value of the class attribute

        self.imports = []
        self.decorators = []
        self.doc = None

        # A list of values that should be interpreted as not set in addition to indentist's own DEFAULT_NOT_SET.
        self.not_set_values = []

        # TODO Remove this.
        self.context = None

        super().__init__(**kwargs)

    def finalise(self):
        """
        Mark the block as finalised which means no more sub-blocks can be added.
        """
        self._blocks = FinalisedBlocks(self._blocks)

    @property
    def is_finalised(self):
        return isinstance(self._blocks, FinalisedBlocks)

    def comma(self) -> "CodeBlock":
        """
        Adds comma to the end of this block and finalises this block.
        """
        self._suffix = ","
        if not self.is_finalised:
            self.finalise()
        return self

    def of(self, *indented_blocks) -> "CodeBlock":
        """
        By default, marks the block as expecting an indented "body" blocks of which are then supplied
        as arguments to this method.

        Unless the block specifies a "closed_by", if no body blocks are supplied or they are all Nones,
        this will generate a "pass" statement as the body. If there is a "closed_by" specified, then
        that will be used on the same indentation level as the opening of the block.

        After all the arguments have been handled, this block is marked as finalised and no more blocks
        can be appended to it.

        None blocks are skipped.

        Returns the block itself.
        """

        if self.closed_by is None:
            self.expects_body_or_pass = True

        for block in indented_blocks:
            if block is not None:
                self._blocks.append((1, block))

        # Finalise it so that we cannot add more sub-blocks to this block.
        self.finalise()

        return self

    def add(self, *blocks, indentation=0) -> "CodeBlock":
        """
        Adds sub-blocks at the specified indentation level, which defaults to 0.

        Nones are skipped.

        Returns the parent block itself, useful for chaining.
        """
        for block in blocks:
            if block is not None:
                self._blocks.append((indentation, block))

        return self

    def to_lines(self, context: Context, indentation=0, counter=None):
        # Do not override this.

        counter = counter or Counter()

        for block_indentation, block in self.get_blocks():
            if block is None:
                counter.num_nones += 1
                continue

            counter.num_blocks += 1

            prefix = (indentation + block_indentation) * "    "
            if isinstance(block, str):
                if block_indentation:
                    counter.num_indented_blocks += 1
                    counter.num_indented_non_doc_blocks += 1
                # This is to handle triple-quoted multi-line strings which
                # need to be first dedented and then indented to the required level.
                # This is NOT about handling instances of TripleQuotedString!
                # This is about user passing to add() or of() an actually triple-quoted
                # string which probably has indentation that the user does not intend it
                # to have.
                yield textwrap.indent(textwrap.dedent(block), prefix)
            elif isinstance(block, CodeBlock):
                if block_indentation:
                    counter.num_indented_blocks += 1
                    if not isinstance(block, DocString):
                        counter.num_indented_non_doc_blocks += 1
                yield textwrap.indent(block.to_code(context=context), prefix)
            else:
                raise ValueError(block)

    def process_decorators(self):
        for decorator in self.decorators:
            yield 0, decorator

    def process_triple_quoted_doc_string(self):
        if self.expects_body_or_pass and self.doc:
            if isinstance(self.doc, str):
                yield 1, self.code.doc_string(self.doc)
            elif isinstance(self.doc, DocString):
                yield 1, self.doc
            elif isinstance(self.doc, CodeBlock):
                yield 1, self.code.doc_string(self.doc)
            else:
                raise TypeError(type(self.doc))

    def get_blocks(self):
        """
        Override this method for custom content, but then you are responsible for:
        - generating doc string (you can call self.process_triple_quoted_doc_string())
        - generating "pass" on empty body
        """

        self.process_triple_quoted_doc_string()

        num_indented_blocks = 0
        for indentation, block in self._blocks:
            if indentation > 0:
                num_indented_blocks += 1
            yield indentation, block

        if self.expects_body_or_pass and num_indented_blocks == 0:
            yield 1, "pass"
            return

    def to_code(self, context: Context =None):
        """
        Generate the code and return it as a string.
        """
        # Do not override this method!

        context = context or Context()
        for imp in self.imports:
            if imp not in context.imports:
                context.imports.append(imp)

        counter = Counter()
        lines = list(self.to_lines(context=context, counter=counter))

        if counter.num_indented_non_doc_blocks == 0:
            if self.expects_body_or_pass:
                lines.append("    pass")
            elif self.closed_by:
                lines[-1] += self.closed_by
        else:
            if self.closed_by:
                lines.append(self.closed_by)

        return join_lines(*lines) + self._suffix

    def exec(self, globals=None, locals=None):
        if locals is None:
            locals = {}

        # TODO
        # This is broken at the moment because the names declared in global scope of the code block
        # won't be available because exec will execute the code as if the code
        # was inside a class body.
        # Need to extract globals from the code block and pass them as globals!

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
        return value not in self.not_set_values and value is not Constants.DEFAULT_NOT_SET


class ClassCodeBlock(CodeBlock):
    expects_body_or_pass = True

    def __init__(self, **kwargs):
        self.bases = []
        super().__init__(**kwargs)

    def get_blocks(self):
        yield 0, ""  # two empty lines before a class
        yield 0, ""
        yield from self.process_decorators()

        bases = []
        for b in self.bases or ():
            if isinstance(b, type):
                bases.append(b.__name__)
            else:
                bases.append(b)

        if bases:
            yield 0, f"class {self.name}({', '.join(bases)}):"
        else:
            yield 0, f"class {self.name}:"

        yield from self.process_triple_quoted_doc_string()
        yield from self._blocks

    def func(self, name=None, **kwargs):
        func = self.code.func(name=name, **kwargs)
        self.add(func, indentation=1)
        return func


class FunctionCodeBlock(CodeBlock):
    expects_body_or_pass = True

    def __init__(self, **kwargs):
        self.params: List = []
        self.return_type: Any = Constants.DEFAULT_NOT_SET
        super().__init__(**kwargs)

    @property
    def return_annotation(self):
        if self.return_type is Constants.DEFAULT_NOT_SET:
            return ""
        else:
            return f" -> {type_to_sig_part(self.return_type)}"

    def get_blocks(self):
        yield 0, ""
        yield from self.process_decorators()

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
            yield 0, self.code.block(f"def {self.name}(", closed_by=f"){self.return_annotation}:").of(
                *(f"{p}," for p in params)
            )

        yield from self.process_triple_quoted_doc_string()
        yield from self._blocks

    def block(self, *blocks, **kwargs) -> CodeBlock:
        block = self.code.block(*blocks, **kwargs)
        self.add(block, indentation=1)
        return block


class ListCodeBlock(CodeBlock):
    closed_by = "]"

    # If set to True, there will be no spacing between name and value: "name=[" vs "name = ["
    as_kwarg = False

    def __init__(self, **kwargs):
        self.items = None

        # Literal items are generated with both keys and values stringified.
        self.literal_items = None

        super().__init__(**kwargs)

    def get_blocks(self):
        if self.name:
            s = "" if self.as_kwarg else " "
            yield 0, f"{self.name}{s}={s}["
        else:
            yield 0, "["

        if self.items:
            for item in self.items:
                yield 1, f"{item!r},"

        if self.literal_items:
            for item in self.literal_items:
                yield 1, f"{item},"

        yield from self._blocks


class DictCodeBlock(CodeBlock):

    closed_by = "}"

    # If set to True, there will be no spacing between name and value: "name={" vs "name = {"
    as_kwarg = False

    def __init__(self, **kwargs):
        self.items = None

        # Literal items are generated with values stringified.
        self.literal_items = None

        super().__init__(**kwargs)

    def get_blocks(self):
        if self.name:
            s = "" if self.as_kwarg else " "
            yield 0, f"{self.name}{s}={s}{{"
        else:
            yield 0, "{"

        if self.items:
            for key, value in self.items.items():
                yield 1, f"{key!r}: {value!r},"

        if self.literal_items:
            # Literal items (the meaning of "literal" is pretty vague in this context)
            # are generated with both keys and values stringified.
            for key, value in self.literal_items.items():
                yield 1, f"{key}: {value},"

        yield from self._blocks


class DataclassCodeBlock(ClassCodeBlock):
    expects_body_or_pass = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_to_imports("import dataclasses")
        self.add_to_decorators("@dataclasses.dataclass")

    def field(self, name, **kwargs) -> "DataclassFieldCodeBlock":
        field = self.code.dataclass_field(name=name, **kwargs)
        self.add(field, indentation=1)
        return field


class DataclassFieldCodeBlock(CodeBlock):

    def __init__(self, **kwargs):
        self.type_ = typing.Any
        self.default = Constants.DEFAULT_NOT_SET
        self.default_factory = Constants.DEFAULT_NOT_SET
        self.init = Constants.DEFAULT_NOT_SET
        self.repr = Constants.DEFAULT_NOT_SET
        self.metadata = {}
        super().__init__(**kwargs)
        self.add_to_imports("import dataclasses")
        self.add_to_imports("import typing")

    @property
    def type_annotation(self):
        return type_to_sig_part(self.type_)

    def get_blocks(self):
        if self.doc:
            yield 0, ""  # blank line before fields with doc string
            yield 0, self.code.doc_block_comment(self.doc)

        if not self.is_custom:
            yield 0, f"{self.name}: {self.type_annotation}"
            return

        yield 0, self.code.block(f"{self.name}: {self.type_annotation} = dataclasses.field(", closed_by=")").of(
            f"default={self.default_repr}," if self.is_set(self.default) else None,
            f"default_factory={self.default_factory_repr}," if self.is_set(self.default_factory) else None,
            f"init={self.init_repr}," if self.is_set(self.init) else None,
            f"repr={self.repr_repr}," if self.is_set(self.repr) else None,
            self.code.dict("metadata", as_kwarg=True, closed_by="},", items=self.metadata) if self.metadata else None,
        )

    @property
    def is_custom(self):
        return (
            self.is_set(self.default) or
            self.is_set(self.default_factory) or
            self.is_set(self.init) or
            self.is_set(self.repr) or
            self.metadata
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


class ImportScopeCodeBlock(CodeBlock):
    def to_code(self, context: Context =None):
        context = context or Context()
        without_imports = super().to_code(context=context)
        return "\n".join(context.imports) + "\n\n\n" + without_imports


class ModuleCodeBlock(ImportScopeCodeBlock):
    def class_(self, name=None, **kwargs) -> "ClassCodeBlock":
        cls = self.code.class_(name=name, **kwargs)
        self.add(cls)
        return cls

    def dataclass(self, name=None, **kwargs) -> "DataclassCodeBlock":
        cls = self.code.dataclass(name=name, **kwargs)
        self.add(cls)
        return cls

    def new_type(self, name=None, type_def=None, **kwargs) -> "NewTypeCodeBlock":
        block = self.code.new_type(name=name, type_def=type_def, **kwargs)
        self.add(block)
        return block

    def write_to(self, path: Path, encoding="utf-8", format=None):
        with open(path, "w", encoding=encoding) as f:
            f.write(self.to_code())

        if format:
            from yapf.yapflib.yapf_api import FormatFile
            FormatFile(str(path), in_place=True, style_config=format)


class DocString(CodeBlock):
    def get_blocks(self):
        if not self:
            return
        yield 0, '"""'
        for indentation, block in self._blocks:
            assert isinstance(block, str)
            if self.code.documention_input_is_html:
                block = html2text(block, bodywidth=80).strip()
            yield indentation, block
        yield 0, '"""'


class NewTypeCodeBlock(CodeBlock):
    def __init__(self, **kwargs):
        self.type_def = None
        super().__init__(**kwargs)
        self.add_to_imports("import typing")

    def get_blocks(self):
        yield 0, ""
        yield 0, ""
        if self.doc:
            yield 0, self.code.doc_block_comment(self.doc)
        yield 0, f"{self.name} = typing.NewType(\"{self.name}\", {self.type_def})"


class DocBlockComment(CodeBlock):
    def get_blocks(self):
        yield 0, ""  # Precede any doc block comment with an empty line
        for indentation, block in self._blocks:
            assert isinstance(block, str)
            if self.code.documention_input_is_html:
                block = html2text(block, bodywidth=75).strip()
            else:
                block = "\n".join(textwrap.wrap(block, width=75))
            yield indentation, textwrap.indent(block, prefix="# ")

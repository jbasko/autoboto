import logging
from typing import List

from .blocks import (
    ClassCodeBlock, CodeBlock, DataclassCodeBlock, DataclassFieldCodeBlock, DictCodeBlock, DocBlockComment, DocString,
    FunctionCodeBlock, ListCodeBlock, ModuleCodeBlock, NewTypeCodeBlock
)
from .constants import Constants
from .parameters import Parameter

log = logging.getLogger(__name__)


class CodeGenerator:

    # Do not add any line-spacing in here. It's the responsibility of the blocks
    # and perhaps some automated code formatter afterwards.

    def __init__(self):
        self.documention_input_is_html = False

    def module(self, name, **kwargs) -> "ModuleCodeBlock":
        return ModuleCodeBlock(name=name, **kwargs, code=self)

    def block(self, *blocks, **kwargs) -> "CodeBlock":
        """
        Build a basic code block.
        Positional arguments should be instances of CodeBlock or strings.
        All code blocks passed as positional arguments are added at indentation level 0.
        None blocks are skipped.
        """
        assert "name" not in kwargs
        kwargs.setdefault("code", self)
        code = CodeBlock(**kwargs)
        for block in blocks:
            if block is not None:
                code._blocks.append((0, block))
        return code

    def class_(self, name=None, **kwargs) -> ClassCodeBlock:
        kwargs.setdefault("code", self)
        return ClassCodeBlock(name=name, **kwargs)

    def func(self, name=None, **kwargs) -> "FunctionCodeBlock":
        kwargs.setdefault("code", self)
        return FunctionCodeBlock(name=name, **kwargs)

    def list(self, name=None, **kwargs) -> "ListCodeBlock":
        kwargs.setdefault("code", self)
        return ListCodeBlock(name=name, **kwargs)

    def dict(self, name=None, **kwargs) -> "DictCodeBlock":
        kwargs.setdefault("code", self)
        return DictCodeBlock(name=name, **kwargs)

    def dict_from_locals(self, name, params: List[Parameter], not_specified_literal=Constants.VALUE_NOT_SET):
        """
        Generate code for a dictionary of locals whose value is not the specified literal.
        """
        code = self.block(f"{name} = {{}}")
        for p in params:
            code.add(
                self.block(f"if {p.name} is not {not_specified_literal}:").of(
                    f"{name}[{p.name!r}] = {p.name}"
                ),
            )
        return code

    def dataclass(self, name=None, **kwargs) -> "DataclassCodeBlock":
        kwargs.setdefault("code", self)
        return DataclassCodeBlock(name=name, **kwargs)

    def dataclass_field(self, name=None, **kwargs) -> "DataclassFieldCodeBlock":
        kwargs.setdefault("code", self)
        return DataclassFieldCodeBlock(name=name, **kwargs)

    def doc_string(self, *string_blocks, **kwargs):
        kwargs.setdefault("code", self)
        return DocString(**kwargs).add(*string_blocks)

    def doc_block_comment(self, *strings, **kwargs):
        kwargs.setdefault("code", self)
        return DocBlockComment(**kwargs).add(*strings)

    def new_type(self, name=None, type_def=None, **kwargs) -> "NewTypeCodeBlock":
        kwargs.setdefault("code", self)
        return NewTypeCodeBlock(name=name, type_def=type_def, **kwargs)

import logging
import os
from pathlib import Path
from typing import List

from indentist.blocks import ListCodeBlock
from .blocks import (
    ClassCodeBlock, CodeBlock, DataclassCodeBlock, DataclassFieldCodeBlock, FunctionCodeBlock, DictCodeBlock,
    HtmlStringCodeBlock, ModuleCodeBlock, TripleQuotedStringBlock
)
from .constants import Constants
from .parameters import Parameter

log = logging.getLogger(__name__)


class CodeGenerator:

    build_dir: Path = None

    def __init__(self):
        pass

    def prepare_build_sub_dir(self, sub_dir: Path, delete_files: List[str]):
        assert self.build_dir in sub_dir.parents

        if not self.build_dir.exists():
            os.makedirs(self.build_dir)
            log.info(f"Created build directory {self.build_dir}")

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

    def html_string(self, *html_string_blocks, **kwargs):
        kwargs.setdefault("code", self)
        return HtmlStringCodeBlock(**kwargs).add(*html_string_blocks)

    def triple_quoted_string(self, *string_blocks, **kwargs):
        kwargs.setdefault("code", self)
        return TripleQuotedStringBlock(**kwargs).add(*string_blocks)

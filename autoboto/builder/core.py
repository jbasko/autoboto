from pathlib import Path

from html2text import html2text

from indentist import CodeBlock as C
from autoboto.permanent.falsey import NOT_SPECIFIED


build_dir = Path(__file__).resolve().parents[2] / "build"  # type: Path


def generate_dataclass_v2(name, bases=None, documentation=None, fields=None, before_fields=None, after_fields=None):
    return C.dataclass(
        name=name,
        bases=bases,
        doc=html2text(documentation) if documentation else None,
    ).of(
        *(before_fields if before_fields else ()),
        *(
            C.dataclass_field(
                name=field.name,
                type_=field.type_annotation,
                default=field.default,
                default_factory=field.default_factory,
                doc=html2text(field.documentation) if field.documentation else None,
                metadata=field.metadata,
                not_set_values=[NOT_SPECIFIED],
            )
            for field in fields or ()
        ),
        *(after_fields if after_fields else ()),
    )

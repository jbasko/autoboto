from typing import Optional

import dataclasses


@dataclasses.dataclass
class Style:
    snake_case_variable_names: bool = False
    top_level_iterators: bool = False
    yapf_style_config: Optional[str] = "facebook"

    @classmethod
    def from_dict(cls, v2_style_dict: dict):
        return cls(**v2_style_dict)

"""
Generate autoboto code.
"""
import argparse
from typing import get_type_hints

import dataclasses

from botogen.botogen import Botogen


def run():
    from .config import botogen_config

    parser = argparse.ArgumentParser(description=__doc__)

    config_fields = list(get_type_hints(botogen_config))

    for name in config_fields:
        parser.add_argument(f"--{name.replace('_', '-')}", default=None)

    args = parser.parse_args()
    for name in config_fields:
        arg_value = getattr(args, name)
        if arg_value is not None:
            botogen_config = dataclasses.replace(botogen_config, **{name: arg_value})

    Botogen(config=botogen_config).run()

"""
Generate autoboto code.
"""
import argparse

import dataclasses

from autoboto.builder.botogen import Botogen


def run():
    from .config import botogen_config

    parser = argparse.ArgumentParser(description=__doc__)

    for name in botogen_config:
        parser.add_argument(f"--{name.replace('_', '-')}", default=None)

    args = parser.parse_args()
    for name in botogen_config:
        arg_value = getattr(args, name)
        if arg_value is not None:
            botogen_config = dataclasses.replace(botogen_config, **{name: arg_value})

    Botogen(config=botogen_config).run()

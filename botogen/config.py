import shutil
import tempfile
import typing
from pathlib import Path

import dataclasses
import pkg_resources
from wr_profiles import envvar_profile

from .log import log

botogen_dir = Path(__file__).parent


@dataclasses.dataclass
class BotogenConfig:
    # List of services to generate code for.
    # If one of the entries is "*", all services will be generated.
    services: typing.List[str] = None

    # Name of the yapf style to format code with.
    # Specify empty string to speed up the build by not formatting the generated code at all.
    yapf_style: typing.Any = None

    # The directory in which to put the target package.
    # Defaults to the current directory.
    target_dir: Path = dataclasses.field(default_factory=Path.cwd)

    # Single-word package name. No dots allowed.
    target_package: str = "autoboto"

    # Not configurable via environment variables.
    # Defaults to a temporary directory.
    # When running unit tests, it points to build/{timestamp}.
    build_dir: Path = None

    build_dir_is_temporary: bool = None

    # Not configurable via environment variables.
    autoboto_template_dir: Path = dataclasses.field(
        default_factory=lambda: pkg_resources.resource_filename("botogen", "autoboto_template"),
    )

    def __post_init__(self):
        if not isinstance(self.services, list):
            self.services = [s for s in self.services.strip().split(",")] if self.services else []

        if self.target_dir and not isinstance(self.target_dir, Path):
            self.target_dir = Path(self.target_dir).resolve()

        # Make sure noone attempts to generate "botogen".
        assert self.target_package != "botogen"

        # It has to be a simple, one-part package name because we rely on it in a few places.
        assert "." not in self.target_package

        if self.build_dir is None:
            self.build_dir = Path(tempfile.mkdtemp())
            assert self.build_dir.exists()
            self.build_dir_is_temporary = True

    def __del__(self):
        if self.build_dir_is_temporary and self.build_dir.exists():
            log.info(f"Deleting {self.build_dir}")
            shutil.rmtree(self.build_dir)


botogen_env = envvar_profile(
    profile_root="botogen",
    services="*",  # comma-separated list of services to generate
    yapf_style="facebook",  # pass empty string "" to disable formatting and speed up the build
    target_dir=".",
    target_package="autoboto",
)

botogen_config = BotogenConfig(**botogen_env)

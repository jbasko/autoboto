import collections.abc
import typing
from pathlib import Path

import dataclasses
import wr_profiles


class BotogenEnv(wr_profiles.Profile, collections.abc.Mapping):
    profile_root = "botogen"

    services = wr_profiles.Property(default="*")
    yapf_style = wr_profiles.Property(default="facebook")
    build_dir = wr_profiles.Property(default=None)
    target_package = wr_profiles.Property(default="autoboto")

    def __iter__(self) -> typing.Iterator[str]:
        for p in self.profile_props:
            yield p.name

    def __len__(self):
        return len(self.profile_props)

    def __getitem__(self, item) -> typing.Any:
        return self._get_prop_value(item)


botogen_env = BotogenEnv()


@dataclasses.dataclass
class BotogenConfig:
    services: typing.List[str] = None
    yapf_style: typing.Any = None
    build_dir: Path = None
    target_package: str = None

    def __post_init__(self):
        if not isinstance(self.services, list):
            self.services = [s for s in self.services.strip().split(",")] if self.services else []

        if not isinstance(self.build_dir, Path):
            if self.build_dir is None:
                self.build_dir = Path(__file__).parents[2] / "autoboto"
            else:
                self.build_dir = Path(self.build_dir)

    def __iter__(self) -> typing.Iterator[str]:
        for f in dataclasses.fields(self):
            yield f.name

    def __getitem__(self, item) -> typing.Any:
        return getattr(self, item)


botogen_config = BotogenConfig(**botogen_env)

import os
import tempfile
from pathlib import Path
from typing import List

from .ab import AbServiceModel
from .log import log
from .service_generator import ServiceGenerator
from .styles import Style


def generate(
    target_package: str = "botocomplete",
    services: List[str] = None,
    style: Style = None,
    build_dir: Path = None,
) -> "Botogen":
    """
    Generate your boto3 interface library!
    """
    default_style = Style(
        snake_case_variable_names=True,
        top_level_iterators=True,
    )
    default_services = ["s3", "cloudformation"]
    default_build_dir = Path.cwd() / "build"

    lib_gen = Botogen(
        target_package=target_package,
        services=services or default_services,
        style=style or default_style,
        build_dir=build_dir or default_build_dir,
    )
    lib_gen.run()
    return lib_gen


class Botogen:
    def __init__(
        self,
        target_package: str,
        services: List[str] = None,
        style: Style = None,
        build_dir: str = None,
    ):
        self.target_package = target_package
        self.services = services or []
        self.style = style or Style()

        self._temp_build_dir = None
        if build_dir:
            self.build_dir = Path(build_dir)
        else:
            self._temp_build_dir = tempfile.TemporaryDirectory()
            self.build_dir = Path(self._temp_build_dir.name)

    def run(self):
        log.debug(f"build_dir = {self.build_dir}")
        log.debug(f"target_package = {self.target_package}")
        log.debug(f"services = {self.services}")
        log.debug(f"style = {self.style}")

        if "*" in self.services:
            services = AbServiceModel.loader.list_available_services("service-2")
        else:
            services = self.services

        for service_name in services:
            ServiceGenerator(
                service_name=service_name,
                botogen=self,
            ).run()

    @property
    def services_build_dir(self):
        path = self.build_dir / "services"
        if not path.exists():
            os.makedirs(path)
            (path / "__init__.py").touch()
        return path

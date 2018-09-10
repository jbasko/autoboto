import importlib
import shutil
import sys
from pathlib import Path

import botocore

from .ab import AbServiceModel
from .config import BotogenConfig, botogen_config
from .indentist import CodeGenerator
from .log import log
from .service_generator import ServiceGenerator


class Botogen:
    def __init__(self, config: BotogenConfig = None, **config_values):
        if config is None:
            if config_values:
                self.config = BotogenConfig(**config_values)
            else:
                self.config = botogen_config
        else:
            assert not config_values
            self.config = config

    def run(self):
        if "*" in self.config.services:
            services = AbServiceModel.loader.list_available_services("service-2")
        else:
            services = self.config.services
        log.debug(f"services = {services}")
        log.debug(f"yapf_style = {self.config.yapf_style}")
        log.debug(f"build_dir = {self.config.build_dir}")
        log.debug(f"target_dir = {self.config.target_dir}")
        log.debug(f"target_package = {self.config.target_package}")

        if self.build_autoboto_package_dir.exists():
            shutil.rmtree(self.build_autoboto_package_dir)

        shutil.copytree(
            self.config.autoboto_template_dir,
            self.build_autoboto_package_dir,
        )

        versions_module = CodeGenerator().module("versions")
        versions_module.add(
            "# Version of botocore from which autoboto services code was generated",
            f"botocore_version = {tuple(int(x) for x in botocore.__version__.split('.'))!r}",
        )
        versions_module.write_to(self.build_autoboto_package_dir / "versions.py", format=self.config.yapf_style)

        services_dir = self.build_autoboto_package_dir / "services"
        services_dir.mkdir()
        (services_dir / "__init__.py").touch()

        # Make sure the build directory is the first one in path
        sys.path.insert(0, str(self.config.build_dir))

        for service_name in services:
            ServiceGenerator(
                service_name=service_name,
                botogen=self,
            ).run()
            self._try_generated_service_import(service_name)

        # Remove the previously added build directory from the path
        sys.path.remove(str(self.config.build_dir))

        # Move the generated package to the target_dir
        assert self.config.target_dir.exists()

        if self.target_autoboto_package_dir.exists():
            shutil.rmtree(self.target_autoboto_package_dir)

        shutil.copytree(self.build_autoboto_package_dir, self.target_autoboto_package_dir)
        log.info(f"Generated package {self.config.target_package} at {self.target_autoboto_package_dir}")

    def import_generated_autoboto(self):
        """
        Imports the autoboto package generated in the build directory (not target_dir).

        For example:
            autoboto = botogen.import_generated_autoboto()

        """
        if str(self.config.build_dir) not in sys.path:
            sys.path.append(str(self.config.build_dir))
        return importlib.import_module(self.config.target_package)

    def import_generated_autoboto_module(self, name):
        """
        Imports a module from the generated autoboto package in the build directory (not target_dir).

        For example, to import autoboto.services.s3.shapes, call:
            botogen.import_generated_autoboto_module("services.s3.shapes")

        """
        if str(self.config.build_dir) not in sys.path:
            sys.path.append(str(self.config.build_dir))
        return importlib.import_module(f"{self.config.target_package}.{name}")

    @property
    def build_autoboto_package_dir(self) -> Path:
        """
        Path to the build package directory.
        """
        return self.config.build_dir / self.config.target_package

    @property
    def target_autoboto_package_dir(self) -> Path:
        """
        Path to the target package directory.
        For a release that would be ./autoboto
        """
        return self.config.target_dir / self.config.target_package

    def get_autoboto_path(self, relative_path) -> Path:
        return self.build_autoboto_package_dir / relative_path

    @property
    def target_autoboto_package_name(self) -> str:
        """
        Name of the autoboto package that should be used in the generated imports.
        """
        return self.config.target_package

    def _try_generated_service_import(self, service_name):
        service_package_name = f"{self.target_autoboto_package_name}.services.{service_name}"

        log.debug(f"importing the generated {service_package_name}")
        service = importlib.import_module(service_package_name)

        assert service.shapes
        assert service.Client
        service.Client()

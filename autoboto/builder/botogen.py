import os

from .ab import AbServiceModel
from .config import BotogenConfig
from .log import log
from .service_generator import ServiceGenerator


class Botogen:
    def __init__(self, config: BotogenConfig = None, **config_values):
        if config is None:
            self.config = BotogenConfig(**config_values)
        else:
            assert not config_values
            self.config = config

    def run(self):
        log.debug(f"yapf_style = {self.config.yapf_style}")
        log.debug(f"build_dir = {self.config.build_dir}")

        if "*" in self.config.services:
            services = AbServiceModel.loader.list_available_services("service-2")
        else:
            services = self.config.services
        log.debug(f"services = {services}")

        for service_name in services:
            ServiceGenerator(
                service_name=service_name,
                botogen=self,
            ).run()

    @property
    def services_build_dir(self):
        path = self.config.build_dir / "services"
        if not path.exists():
            os.makedirs(path)
            (path / "__init__.py").touch()
        return path

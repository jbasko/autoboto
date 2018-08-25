import botocore.model
from botocore import xform_name
from botocore.loaders import Loader

loader = Loader()


class ServiceModel(botocore.model.ServiceModel):
    def __init__(self, service_name):
        super().__init__(
            service_description=loader.load_service_model(service_name, "service-2"),
            service_name=service_name,
        )

    def operation_model(self, operation_name) -> botocore.model.OperationModel:
        return super().operation_model(operation_name)

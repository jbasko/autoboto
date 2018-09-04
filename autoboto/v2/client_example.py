import boto3

_NOT_SET = object()


class Client:
    service_name = "s3"

    def __init__(self, *args, **kwargs):
        self.boto_client = boto3.client(self.service_name, *args, **kwargs)

    def list_objects_v2(
        self,
        # list_objects_v2_request=None, # TODO Later
        *,
        bucket_name=_NOT_SET,
        owner=_NOT_SET,
        # ...
    ):
        _params = {}
        if bucket_name is not _NOT_SET:
            _params["bucket_name"] = bucket_name
        if owner is not _NOT_SET:
            _params["owner"] = owner
        # ... for all other params

        list_objects_v2_request = deserialize(shapes.ListObjectsV2Request, _params)
        response = self.boto_client.list_objects_v2(**list_objects_v2_request.to_boto_dict())
        return deserialise(shapes.ListObjectsV2Output, response)


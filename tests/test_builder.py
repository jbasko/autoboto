import datetime as dt
import importlib
import inspect

import dataclasses

from autoboto.builder.core import build_dir
from autoboto.builder.generate_all import generate_service_shapes, generate_service_operations, \
    generate_service_package, generate_service_client
from autoboto.permanent.falsey import NOT_SET
from indentist import Constants


def test_build_dir():
    assert str(build_dir).endswith("/autoboto/build")


def test_not_set_and_not_specified():
    assert NOT_SET is NOT_SET
    assert NOT_SET == NOT_SET


def test_generates_s3_service_shapes():
    generate_service_package("s3")
    shapes_path, shapes_module_name = generate_service_shapes("s3", generated_package="build")

    shapes = importlib.import_module(shapes_module_name)

    assert hasattr(shapes, "ListBucketsOutput")

    assert shapes.ListBucketsOutput
    obj = shapes.ListBucketsOutput.from_dict({
        "Buckets": [
            {
                "Name": "first",
                "CreationDate": dt.datetime.utcnow()
            },
            {
                "Name": "second",
                "CreationDate": dt.datetime.utcnow()
            },
        ],
        "Owner": {
            "DisplayName": "The Owner",
            "ID": "the-owner-id",
        },
    })
    assert len(obj.Buckets) == 2
    assert obj.Buckets[1].Name == "second"
    assert obj.Owner.DisplayName == "The Owner"


def test_generates_s3_service_operations():
    generate_service_package("s3")

    client_path, client_module_name = generate_service_client("s3", generated_package="build")
    client = importlib.import_module(client_module_name)

    method = client.Client.list_objects_v2
    assert callable(method)

    method_sig = inspect.signature(method)
    bucket_param = method_sig.parameters["Bucket"]
    assert bucket_param.default is inspect.Parameter.empty  # required param hence must be empty
    delimiter_param = method_sig.parameters["Delimiter"]
    assert delimiter_param.default == Constants.VALUE_NOT_SET  # optional param

    operations_path, operations_module_name = generate_service_operations("s3", generated_package="build")
    operations = importlib.import_module(operations_module_name)
    assert operations.dataclasses
    assert operations.CompleteMultipartUpload
    assert operations.UploadPartCopy
    assert len(dataclasses.fields(operations.UploadPartCopy)) == 17

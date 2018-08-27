import importlib

import dataclasses

from autoboto.builder.core import build_dir
from autoboto.builder.generate_all import generate_service_shapes, generate_service_operations, generate_service_package
from autoboto.permanent.falsey import NOT_SET


def test_build_dir():
    assert str(build_dir).endswith("/autoboto/build")


def test_not_set_and_not_specified():
    assert NOT_SET is NOT_SET
    assert NOT_SET == NOT_SET


def test_generates_s3_service_shapes():
    generate_service_package("s3")
    module_path, module_name = generate_service_shapes("s3", generated_package="build")
    with open(module_path, encoding="utf-8") as f:
        module_code = f.read()

    env = {}
    exec(module_code, env)

    assert env
    assert env["dataclasses"]
    assert env["AbortIncompleteMultipartUpload"]
    assert env["WebsiteConfiguration"]


def test_generates_s3_service_operations():
    generate_service_package("s3")
    module_path, module_name = generate_service_operations("s3", generated_package="build")

    module = importlib.import_module(module_name)
    assert module.dataclasses
    assert module.CompleteMultipartUpload
    assert module.UploadPartCopy
    assert len(dataclasses.fields(module.UploadPartCopy)) == 17

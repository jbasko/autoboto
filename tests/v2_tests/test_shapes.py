import datetime
import typing

import dataclasses
import pytest

import autoboto
from autoboto import TypeInfo, serialize_to_boto
from autoboto.base import deserialise_from_boto


@pytest.fixture(scope="session")
def s3_shapes(build_dir):
    autoboto.generate(
        services=["s3"],
        style=autoboto.Style(
            snake_case_variable_names=True,
            yapf_style_config=None,  # no formatting in tests to speed up
        ),
        build_dir=build_dir,
        target_package="build.test"
    )
    from build.test.services.s3 import shapes
    return shapes


def test_s3_list_objects_v2_request_shape(s3_shapes):
    request_shape = s3_shapes.ListObjectsV2Request
    assert request_shape.bucket
    assert request_shape.delimiter
    assert request_shape.encoding_type
    assert request_shape.request_payer

    assert dataclasses.is_dataclass(request_shape)

    request = s3_shapes.ListObjectsV2Request(
        bucket="test-bucket",
        delimiter=",",
        fetch_owner=True,
    )
    assert request._get_boto_mapping()[0] == ("bucket", "Bucket", TypeInfo(str))
    assert request._get_boto_mapping()[2] == ("encoding_type", "EncodingType", TypeInfo(s3_shapes.EncodingType))
    assert request.to_boto_dict() == {
        "Bucket": "test-bucket",
        "Delimiter": ",",
        "FetchOwner": True,
    }


def test_s3_list_objects_v2_output_shape(s3_shapes):
    assert dataclasses.is_dataclass(s3_shapes.ListObjectsV2Output)

    output_shape = s3_shapes.ListObjectsV2Output()
    assert dataclasses.is_dataclass(output_shape)

    assert hasattr(output_shape, "contents")
    assert hasattr(output_shape, "is_truncated")

    types = typing.get_type_hints(s3_shapes.ListObjectsV2Output)
    assert TypeInfo(types["is_truncated"]).type is bool


def test_s3_metadata_shape(s3_shapes):
    assert not hasattr(s3_shapes, "Metadata")
    assert not hasattr(s3_shapes, "MetadataKey")
    assert not hasattr(s3_shapes, "MetadataValue")
    assert typing.get_type_hints(s3_shapes.PutObjectRequest)["metadata"] is typing.Dict[str, str]


def test_deserialise_from_boto(s3_shapes):
    assert deserialise_from_boto(typing.Any, [{1, 2, 3}]) == [{1, 2, 3}]

    assert deserialise_from_boto(typing.Any, None) is None
    assert deserialise_from_boto(int, None) is None
    assert deserialise_from_boto(datetime.datetime, None) is None
    assert deserialise_from_boto(typing.Dict[str, str], None) is None

    assert deserialise_from_boto(str, "hello") == "hello"
    assert deserialise_from_boto(int, "42") == "42"
    assert deserialise_from_boto(int, 42) == 42
    assert deserialise_from_boto(bool, False) is False
    assert deserialise_from_boto(datetime.datetime, datetime.datetime(2018, 8, 31)) == datetime.datetime(2018, 8, 31)
    assert deserialise_from_boto(datetime.datetime, "2018-08-31") == "2018-08-31"

    assert deserialise_from_boto(typing.List[str], ["hel", "lo"]) == ["hel", "lo"]
    assert deserialise_from_boto(typing.Tuple[str], ["hel", "lo"]) == ("hel", "lo")

    assert deserialise_from_boto(typing.Dict[str, str], {"name": 42}) == {"name": 42}
    assert deserialise_from_boto(typing.Dict[str, str], {"name": "42"}) == {"name": "42"}

    boto_owner = {
        "DisplayName": "owner-display-name",
        "ID": "owner-id",
    }
    assert deserialise_from_boto(s3_shapes.Owner, boto_owner) == s3_shapes.Owner("owner-display-name", "owner-id")

    boto_list_buckets_output = {
        "Buckets": [
            {
                "Name": "first-bucket",
                "CreationDate": datetime.datetime(2018, 8, 31, 12, 30),
            },
            {
                "Name": "second-bucket",
                "CreationDate": datetime.datetime(2018, 9, 2, 8, 45),
            },
        ],
        "Owner": {
            "DisplayName": "owner-display-name",
            "ID": "owner-id",
        },
    }
    list_buckets_output = deserialise_from_boto(s3_shapes.ListBucketsOutput, boto_list_buckets_output)
    assert isinstance(list_buckets_output.owner, s3_shapes.Owner)
    assert list_buckets_output.owner.display_name == "owner-display-name"
    assert isinstance(list_buckets_output.buckets[0], s3_shapes.Bucket)
    assert list_buckets_output.buckets[1].name == "second-bucket"

    assert list_buckets_output.to_boto_dict() == boto_list_buckets_output


def test_handle_enums(s3_shapes):
    assert deserialise_from_boto(s3_shapes.ObjectStorageClass, "STANDARD") is s3_shapes.ObjectStorageClass.STANDARD
    assert serialize_to_boto(s3_shapes.ObjectStorageClass, s3_shapes.ObjectStorageClass.GLACIER) == "GLACIER"

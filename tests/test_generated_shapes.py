import datetime
import typing

import dataclasses


def test_shapes_have_boto_fields(s3_shapes):
    assert s3_shapes.ListBucketsOutput.boto_fields == ["ResponseMetadata", "Buckets", "Owner"]
    assert s3_shapes.ListBucketsOutput.autoboto_fields == ["response_metadata", "buckets", "owner"]


def test_s3_list_objects_v2_request_shape(s3_shapes):
    request_shape = s3_shapes.ListObjectsV2Request
    assert hasattr(request_shape, "bucket")
    assert hasattr(request_shape, "delimiter")
    assert hasattr(request_shape, "encoding_type")
    assert hasattr(request_shape, "request_payer")

    assert dataclasses.is_dataclass(request_shape)

    request = s3_shapes.ListObjectsV2Request(
        bucket="test-bucket",
        delimiter=",",
        fetch_owner=True,
    )
    assert request._get_boto_mapping()[0] == ("bucket", "Bucket", s3_shapes.TypeInfo(str))
    assert request._get_boto_mapping()[2] == (
        "encoding_type", "EncodingType", s3_shapes.TypeInfo(s3_shapes.EncodingType)
    )
    assert request.to_boto_dict() == {
        "Bucket": "test-bucket",
        "Delimiter": ",",
        "FetchOwner": True,
    }


def test_s3_list_objects_v2_output_shape(s3_shapes, autoboto):
    assert dataclasses.is_dataclass(s3_shapes.ListObjectsV2Output)
    assert issubclass(s3_shapes.ListObjectsV2Output, s3_shapes.ShapeBase)
    assert issubclass(s3_shapes.ListObjectsV2Output, s3_shapes.OutputShapeBase)

    output_shape = s3_shapes.ListObjectsV2Output()
    assert dataclasses.is_dataclass(output_shape)

    assert hasattr(output_shape, "contents")
    assert hasattr(output_shape, "is_truncated")

    types = typing.get_type_hints(s3_shapes.ListObjectsV2Output)
    assert autoboto.TypeInfo(types["is_truncated"]).type is bool


def test_s3_metadata_shape(s3_shapes):
    assert not hasattr(s3_shapes, "Metadata")
    assert not hasattr(s3_shapes, "MetadataKey")
    assert not hasattr(s3_shapes, "MetadataValue")
    assert typing.get_type_hints(s3_shapes.PutObjectRequest)["metadata"] is typing.Dict[str, str]


def test_deserialise_from_boto(s3_shapes, autoboto):
    deserialise_from_boto = autoboto.deserialise_from_boto
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
    autoboto_owner = deserialise_from_boto(s3_shapes.Owner, boto_owner)
    assert s3_shapes.Owner("owner-display-name", "owner-id") == autoboto_owner

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
        "ResponseMetadata": {
            "RequestId": "REQUESTID",
            "HostId": "hostid",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amz-id-2": "hostid",
                "x-amz-request-id": "REQUESTID",
                "date": "Wed, 05 Sep 2018 19:09:33 GMT",
                "content-type": "application/xml",
                "transfer-encoding": "chunked",
                "server": "AmazonS3",
            },
            "RetryAttempts": 0,
        },
    }
    output = deserialise_from_boto(s3_shapes.ListBucketsOutput, boto_list_buckets_output)

    assert isinstance(output.owner, s3_shapes.Owner)
    assert output.owner.display_name == "owner-display-name"

    assert isinstance(output.buckets[0], s3_shapes.Bucket)
    assert output.buckets[1].name == "second-bucket"

    assert output.response_metadata["RequestId"] == "REQUESTID"
    assert output.response_metadata["HTTPHeaders"]["x-amz-request-id"] == "REQUESTID"

    assert output.to_boto_dict() == boto_list_buckets_output


def test_handle_enums(s3_shapes, autoboto):
    # Enum name matches the value
    standard = autoboto.deserialise_from_boto(s3_shapes.ObjectStorageClass, "STANDARD")
    assert standard is s3_shapes.ObjectStorageClass.STANDARD
    assert autoboto.serialize_to_boto(s3_shapes.ObjectStorageClass, s3_shapes.ObjectStorageClass.GLACIER) == "GLACIER"

    # Enum name doesn't match the value
    eu_west_1 = autoboto.deserialise_from_boto(s3_shapes.BucketLocationConstraint, "eu-west-1")
    assert eu_west_1 is s3_shapes.BucketLocationConstraint.eu_west_1
    assert autoboto.serialize_to_boto(
        s3_shapes.BucketLocationConstraint, s3_shapes.BucketLocationConstraint.eu_west_1
    ) == "eu-west-1"

    # Enum value unknown, but we still accept it.
    us_east_2 = autoboto.deserialise_from_boto(s3_shapes.BucketLocationConstraint, "us-east-2")
    assert us_east_2 is "us-east-2"
    assert autoboto.serialize_to_boto(s3_shapes.BucketLocationConstraint, "us-east-2") == "us-east-2"


def test_output_shapes_are_detected_and_have_response_metadata_added(s3_shapes):
    assert hasattr(s3_shapes.NotificationConfiguration(), "response_metadata")
    assert hasattr(s3_shapes.ListBucketsOutput(), "response_metadata")
    assert not hasattr(s3_shapes.GetBucketNotificationConfigurationRequest(), "response_metadata")

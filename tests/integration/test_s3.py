import random
import string

import pytest

import autoboto.services.s3 as s3


@pytest.fixture(scope="session")
def client():
    return s3.Client()


def new_bucket_name():
    return f"autoboto-test-{(''.join(random.choice(string.ascii_lowercase) for i in range(30)))}"


def test_manages_buckets(client):
    bucket_name = new_bucket_name()

    client.create_bucket(
        bucket=bucket_name,
        # TODO This is ugly
        create_bucket_configuration=s3.shapes.CreateBucketConfiguration(location_constraint="eu-west-1"),
    )

    location = client.get_bucket_location(bucket=bucket_name)
    assert location.location_constraint == "eu-west-1"

    buckets = client.list_buckets().buckets
    assert len(buckets) > 0

    assert any(bucket.name == bucket_name for bucket in buckets)

    for bucket in client.list_buckets().buckets:
        client.delete_bucket(bucket=bucket.name)

    assert len(client.list_buckets().buckets) == 0

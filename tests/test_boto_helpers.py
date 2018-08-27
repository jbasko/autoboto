import pytest

from autoboto.builder.boto_helpers import ServiceModel, iter_sorted_members


@pytest.fixture(scope="session")
def s3_service_model() -> ServiceModel:
    return ServiceModel("s3")


def test_required_members_come_first_in_sorted_order(s3_service_model):
    member_names = [m.name for m in iter_sorted_members(s3_service_model.shape_for("CopyObjectRequest"))]
    assert member_names[0:5] == [
        "Bucket",
        "CopySource",
        "Key",
        "ACL",
        "CacheControl",
    ]

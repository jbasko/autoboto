import os

import boto3
import pytest


@pytest.fixture(autouse=True, scope="session")
def set_envvars():
    os.environ["AWS_PROFILE"] = "autoboto-test"


@pytest.fixture(autouse=True)
def ensure_correct_aws_account_is_used():
    expected_account_id = os.environ["AUTOBOTO_TEST_AWS_ACCOUNT_ID"]
    if not expected_account_id:
        raise RuntimeError("Must set non-empty AUTOBOTO_TEST_AWS_ACCOUNT_ID to run integration tests")
    actual_account_id = boto3.client("sts").get_caller_identity().get("Account")
    assert str(expected_account_id) == str(actual_account_id)

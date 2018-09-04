from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def build_dir():
    return Path(__file__).parents[1] / "build" / "test"

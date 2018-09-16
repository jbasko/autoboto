import datetime as dt
import shutil
import sys
from pathlib import Path

import pytest

from botogen import Botogen

# These only make sense in local development environment.
# When autoboto is installed as a package, you shouldn't be running the tests.

_project_root_dir: Path = Path(__file__).parents[2]
_project_build_dir: Path = _project_root_dir / "build"

# The directory under which all test builds live
_test_build_dir_parent: Path = _project_build_dir / "test"


@pytest.fixture(scope="session")
def build_dir() -> Path:
    """
    Creates a build directory for this test session and adds it to sys.path
    """

    path = _test_build_dir_parent / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not path.exists():
        path.mkdir(parents=True)

    sys.path.append(str(path))

    try:
        yield path
    finally:
        # Delete the build directory afterwards
        shutil.rmtree(path)


@pytest.fixture(scope="session")
def target_dir() -> Path:
    """
    The target directory is the directory (non-package) in which
    the generated package is put after it has been successfully built.
    """
    path = _project_build_dir / "test-packages"
    if not path.exists():
        path.mkdir(parents=True)
    return path


@pytest.fixture(scope="session")
def target_package(build_dir):
    """
    The name of the target package relative to the build directory (which is added to sys.path).
    """
    return f"autoboto_{build_dir.name}"


@pytest.fixture(scope="session")
def botogen(build_dir, target_dir, target_package) -> Botogen:
    botogen = Botogen(
        services=["s3"],
        yapf_style=None,
        build_dir=build_dir,
        target_dir=target_dir,
        target_package=target_package,
    )
    botogen.run()
    return botogen


@pytest.fixture(scope="session")
def autoboto(botogen):
    return botogen.import_generated_autoboto()


@pytest.fixture(scope="session")
def s3_shapes(botogen):
    try:
        return botogen.import_generated_autoboto_module("services.s3.shapes")
    except ImportError:
        raise Exception(
            f"Failed to import {botogen.config.target_package}.services.s3.shapes with sys.path={sys.path}"
        )

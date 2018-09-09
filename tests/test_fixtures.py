import sys


def test_build_dir_exists_and_is_added_to_sys_path(build_dir):
    assert build_dir.exists()
    assert str(build_dir) in sys.path


def test_target_dir_is_under_test_packages(target_dir):
    assert target_dir.name == "test-packages"
    assert target_dir.parent.name == "build"


def test_botogen_is_configured(botogen, build_dir, target_dir, target_package):
    assert botogen.config.build_dir == build_dir
    assert botogen.config.target_dir == target_dir
    assert botogen.config.target_package == target_package


def test_botogen_generates_target_package(botogen, target_package):
    botogen.run()

    package = botogen.import_generated_autoboto()
    assert package.__version__
    assert package.botocore_version

    s3 = botogen.import_generated_autoboto_module("services.s3")
    assert s3.shapes
    assert s3.Client

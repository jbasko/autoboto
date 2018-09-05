from autoboto.builder.botogen import Botogen
from autoboto.builder.service_generator import ServiceGenerator


def test_shapes_lookup(build_dir):
    botogen = Botogen(target_package="build.test", build_dir=build_dir)
    s3 = ServiceGenerator(service_name="s3", botogen=botogen)

    assert s3.shapes["AllowedOrigin"].is_primitive
    assert s3.type_annotation_for_shape("AllowedOrigin") == "str"

    assert not s3.shapes["AllowedOrigins"].is_primitive
    assert s3.type_annotation_for_shape("AllowedOrigins") == "typing.List[str]"

    assert not s3.shapes["CORSRule"].is_primitive
    assert s3.type_annotation_for_shape("CORSRule") == "\"CORSRule\""

    assert s3.shapes["MFADelete"].is_enum
    assert s3.type_annotation_for_shape("MFADelete") == "\"MFADelete\""

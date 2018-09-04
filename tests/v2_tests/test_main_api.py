import autoboto


def test_all_imports():
    assert getattr(autoboto, "generate")
    assert getattr(autoboto, "Style")


def test_generate_works(build_dir):
    gen = autoboto.generate(
        build_dir=build_dir,
        style=autoboto.Style(yapf_style_config=None),
    )
    assert gen.target_package == "botocomplete"
    assert gen.services == ["s3", "cloudformation"]

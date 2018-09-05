from autoboto.builder.botogen import Botogen


def test_generate_works(build_dir):
    Botogen(
        build_dir=build_dir,
        yapf_style=None,
    ).run()

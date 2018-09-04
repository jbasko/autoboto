from pathlib import Path

import autoboto

if __name__ == "__main__":
    target_dir = Path(__file__).parents[1].resolve()
    assert str(target_dir).endswith("autoboto")
    assert target_dir.exists()
    assert (target_dir / "builder").exists()
    assert (target_dir / "indentist").exists()
    autoboto.generate(
        build_dir=target_dir,
        services=["*"],
    )

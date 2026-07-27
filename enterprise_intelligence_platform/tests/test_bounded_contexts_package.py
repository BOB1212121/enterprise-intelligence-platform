from pathlib import Path


def test_bounded_contexts_package_exists() -> None:
	package_dir = Path(__file__).resolve().parents[1] / "bounded_contexts"
	assert package_dir.is_dir()
	assert (package_dir / "__init__.py").is_file()

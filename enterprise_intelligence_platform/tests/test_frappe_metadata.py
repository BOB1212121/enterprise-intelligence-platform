from importlib import import_module
from pathlib import Path


def test_frappe_hooks_metadata_is_valid() -> None:
	hooks_module = import_module("enterprise_intelligence_platform.hooks")

	assert getattr(hooks_module, "app_name", "") == "enterprise_intelligence_platform"
	assert getattr(hooks_module, "app_title", "")
	assert getattr(hooks_module, "app_publisher", "")
	assert getattr(hooks_module, "app_description", "")
	assert getattr(hooks_module, "app_email", "")
	assert getattr(hooks_module, "app_license", "")


def test_modules_txt_has_module_entry() -> None:
	modules_file = Path(__file__).resolve().parents[1] / "modules.txt"
	content = modules_file.read_text(encoding="utf-8").strip()
	assert content

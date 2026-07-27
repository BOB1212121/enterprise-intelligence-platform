from importlib import import_module


def test_app_package_imports() -> None:
	app_pkg = import_module("enterprise_intelligence_platform")
	assert app_pkg is not None


def test_hooks_module_imports() -> None:
	hooks_module = import_module("enterprise_intelligence_platform.hooks")
	assert hooks_module is not None

"""pytest conftest: provide the minimal frappe.local context that
frappe.whitelist()'s validate_argument_types wrapper needs at call time.

Without this, unit tests that call @frappe.whitelist()-decorated functions
fail with AttributeError: flags because frappe.local is not initialised.
"""
import frappe


def pytest_configure(config):  # noqa: ARG001
    try:
        frappe.local.flags  # already set by a prior frappe.init()
    except AttributeError:
        frappe.local.flags = frappe._dict(in_test=True)

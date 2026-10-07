"""Reusable response comparator. No network or business writes by default."""

import httpx


def shape(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        # Compare distinct element shapes, not list lengths or business data values.
        return {"array": sorted({repr(shape(item)) for item in value})}
    if isinstance(value, dict):
        return {key: shape(item) for key, item in sorted(value.items())}
    raise TypeError(type(value).__name__)


def compare_responses(node, python, important_headers=("content-type",)):
    differences = {}
    if node.status_code != python.status_code:
        differences["status"] = (node.status_code, python.status_code)
    for header in important_headers:
        left, right = node.headers.get(header, ""), python.headers.get(header, "")
        if header.lower() == "content-type":
            left, right = left.split(";")[0], right.split(";")[0]
        if left != right:
            differences[f"header:{header}"] = (left, right)
    if "json" in node.headers.get("content-type", "") and "json" in python.headers.get(
        "content-type", ""
    ):
        if shape(node.json()) != shape(python.json()):
            differences["json_shape"] = (shape(node.json()), shape(python.json()))
    return differences


def fetch_read_only(base_url, path, headers=None):
    # Intentionally no POST/PUT/DELETE API in this scaffolding.
    with httpx.Client(
        base_url=base_url, timeout=10, follow_redirects=False, trust_env=False
    ) as client:
        return client.get(path, headers=headers)

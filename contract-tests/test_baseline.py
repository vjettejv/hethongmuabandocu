import json
import re
import subprocess
from pathlib import Path

import httpx
import pytest
from parity import compare_responses

ROOT = Path(__file__).resolve().parents[1]
SERVICES = [
    "auth",
    "user",
    "post",
    "category",
    "message",
    "notification",
    "review",
    "search",
    "favorite",
]


@pytest.mark.parametrize("service", SERVICES)
def test_inventory_covers_node_routes(contracts, service):
    baseline = contracts["baseline_commit"]
    assert baseline == "92777b8f70b6717e3ffd12657c725b2ea4e3d0ab"
    text = subprocess.check_output(
        ["git", "show", f"{baseline}:{service}-service/src/routes/index.js"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    source = {
        (method.upper(), path)
        for method, path in re.findall(r"router\.(get|post|put|delete)\('([^']+)'", text)
    }
    recorded = {
        (item["method"], item["service_path"])
        for item in contracts["endpoints"]
        if item["service"] == f"{service}-service"
    }
    assert recorded == source


def test_contracts_complete_and_unique(contracts):
    endpoints = contracts["endpoints"]
    assert len(endpoints) == 37
    assert len({item["id"] for item in endpoints}) == 37
    for item in endpoints:
        assert all(
            key in item
            for key in (
                "method",
                "gateway_path",
                "auth",
                "request",
                "success",
                "errors",
                "evidence",
            )
        )
        assert not item["gateway_path"].startswith("/api/")
        assert item["success"]["statuses"]


def test_known_notification_shadow_preserved_in_baseline(contracts):
    item = next(
        item
        for item in contracts["endpoints"]
        if item["method"] == "GET" and item["gateway_path"] == "/messages/notifications"
    )
    assert item["observed_dispatch"] == 'getHistory(contactId="notifications")'
    assert item["declared_response"] != item["success"]["shape"]


def test_safe_auth_fixture_and_compatibility():
    data = json.loads((ROOT / "contracts/fixtures/auth-login.synthetic.json").read_text())
    assert data["response"]["token"] == "synthetic-token-not-valid"
    assert set(data["response"]["user"]) == {"id", "username", "email", "roleId"}
    assert isinstance(data["response"]["user"]["id"], int)
    plan = json.loads((ROOT / "contracts/auth/compatibility.json").read_text())
    assert plan["implemented"] is False
    assert plan["password"]["real_hashes_copied"] is False
    assert plan["jwt"]["ttl_seconds"] == 86400


def test_parity_detects_status_shape_and_headers():
    node = httpx.Response(200, json={"userId": 101, "data": []})
    python = httpx.Response(201, json={"user_id": "101", "data": []})
    result = compare_responses(node, python)
    assert set(result) == {"status", "json_shape"}
    wrong_type = httpx.Response(200, text="not JSON")
    assert "header:content-type" in compare_responses(node, wrong_type)


def test_parity_ignores_generated_values_but_keeps_types():
    assert (
        compare_responses(
            httpx.Response(200, json={"id": 101, "token": "node"}),
            httpx.Response(200, json={"id": 102, "token": "python"}),
        )
        == {}
    )

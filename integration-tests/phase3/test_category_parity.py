import pytest
from conftest import CATEGORY_DBS, compare, compare_records, literal, pair, select


def test_empty_list_has_no_automatic_seed(live):
    responses = pair(live, "category", "GET", "/")
    compare(responses, 200)
    assert responses["node"].json() == responses["python"].json() == []


def test_existing_list_raw_array_and_timestamps(live):
    for database in CATEGORY_DBS.values():
        select(
            "category",
            f"INSERT INTO `{database}`.categories "
            "(id,name,description,createdAt,updatedAt) VALUES "
            "(7,'phase3_test_category',NULL,'2026-01-02','2026-01-02')",
        )
    responses = pair(live, "category", "GET", "/")
    compare(responses, 200)
    assert isinstance(responses["python"].json(), list)
    compare_records(responses["node"].json()[0], responses["python"].json()[0])


@pytest.mark.parametrize("path", ["/", "/admin/categories", "/admin/categories/"])
@pytest.mark.parametrize(
    "payload",
    [
        {"name": "phase3_test_category"},
        {"name": "phase3_test_category", "description": ""},
        {"name": "phase3_test_Đồ cũ", "description": None},
    ],
)
def test_create_raw_or_admin_envelope_and_database_effects(live, path, payload):
    responses = pair(live, "category", "POST", path, payload=payload)
    compare(responses, 201)
    records = {
        kind: (response.json()["data"] if path != "/" else response.json())
        for kind, response in responses.items()
    }
    compare_records(records["node"], records["python"], generated=True)
    for kind, record in records.items():
        assert record["name"] == payload["name"]
        if "description" in payload:
            assert record["description"] == payload["description"]
        else:
            assert "description" not in record
        if path != "/":
            assert set(responses[kind].json()) == {"data"}
        assert (
            select(
                "category",
                f"SELECT COUNT(*) FROM `{CATEGORY_DBS[kind]}`.categories "
                f"WHERE id={record['id']} AND name={literal(payload['name'])}",
            ).strip()
            == "1"
        )


@pytest.mark.parametrize("path", ["/", "/admin/categories"])
@pytest.mark.parametrize("payload", [{}, {"name": None}])
def test_missing_name_keeps_legacy_500_and_envelope(live, path, payload):
    responses = pair(live, "category", "POST", path, payload=payload)
    compare(responses, 500)
    assert (
        responses["node"].json()
        == responses["python"].json()
        == {"error": "notNull Violation: Category.name cannot be null"}
    )


@pytest.mark.parametrize("path", ["/", "/admin/categories"])
def test_duplicate_category_preserves_validation_error(live, path):
    payload = {"name": "phase3_test_category"}
    compare(pair(live, "category", "POST", "/", payload=payload), 201)
    responses = pair(live, "category", "POST", path, payload=payload)
    compare(responses, 500)
    assert responses["node"].json() == responses["python"].json() == {"error": "Validation error"}
    for database in CATEGORY_DBS.values():
        assert select("category", f"SELECT COUNT(*) FROM `{database}`.categories").strip() == "1"


@pytest.mark.parametrize(
    "path", ["/categories", "/categories/", "/admin/categories", "/categories/admin/categories"]
)
def test_gateway_category_root_admin_alias_without_redirect(live, path):
    client, urls = live
    response = client.post(urls["gateway"] + path, json={"name": "phase3_test_gateway"})
    assert response.status_code == 201
    record = response.json()["data"] if "admin" in path else response.json()
    assert record["name"] == "phase3_test_gateway"
    listed = client.get(urls["gateway"] + "/categories")
    assert listed.status_code == 200 and isinstance(listed.json(), list)
    assert listed.json()[0]["id"] == record["id"]

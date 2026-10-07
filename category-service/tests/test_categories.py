import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from categories import selectors, services
from categories.exceptions import CategoryError
from categories.models import Category
from categories.serializers import projection
from django.db import IntegrityError, OperationalError


@pytest.fixture
def category():
    return Category(
        id=7,
        name="phase3_test_category",
        description=None,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


def test_legacy_mapping_and_no_default_ordering():
    assert Category._meta.db_table == "categories" and not Category._meta.managed
    assert not Category._meta.ordering
    assert Category._meta.get_field("name").unique
    assert Category._meta.get_field("created_at").column == "createdAt"
    assert Category._meta.get_field("updated_at").column == "updatedAt"


def test_list_is_raw_array_and_timestamp_matches_node(client, monkeypatch, category):
    monkeypatch.setattr(selectors, "all_categories", lambda: [category])
    response = client.get("/")
    assert response.status_code == 200 and response.json() == [projection(category)]
    assert response.json()[0]["createdAt"] == "2026-01-02T00:00:00.000Z"
    assert response.json()[0]["description"] is None


def test_empty_database_list_does_not_seed(client, monkeypatch):
    monkeypatch.setattr(selectors, "all_categories", lambda: [])
    response = client.get("/")
    assert response.status_code == 200 and response.json() == []


@pytest.mark.parametrize(
    "path,wrapped", [("/", False), ("/admin/categories", True), ("/admin/categories/", True)]
)
def test_create_endpoint_specific_envelope_without_redirect(
    client, monkeypatch, category, path, wrapped
):
    create = MagicMock(return_value=category)
    monkeypatch.setattr(services, "create_category", create)
    response = client.post(
        path, json.dumps({"name": category.name}), content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json() == ({"data": projection(category)} if wrapped else projection(category))
    create.assert_called_once_with({"name": category.name})


@pytest.mark.parametrize("payload", [{}, {"name": None}])
@pytest.mark.parametrize("path", ["/", "/admin/categories"])
def test_missing_name_preserves_500_error_envelope(client, payload, path):
    response = client.post(path, json.dumps(payload), content_type="application/json")
    assert response.status_code == 500
    assert response.json() == {"error": "notNull Violation: Category.name cannot be null"}


@pytest.mark.parametrize("description", [None, "", "phase3_test_desc"])
def test_create_null_empty_and_nonempty_description(monkeypatch, category, description):
    manager = MagicMock()
    manager.create.return_value = category
    monkeypatch.setattr(Category, "objects", manager)
    assert services.create_category({"name": "", "description": description}) is category
    call = manager.create.call_args.kwargs
    assert call["name"] == "" and call["description"] == description
    assert call["created_at"] == call["updated_at"]


def test_description_omitted_defaults_null(monkeypatch, category):
    manager = MagicMock()
    manager.create.return_value = category
    monkeypatch.setattr(Category, "objects", manager)
    services.create_category({"name": "phase3_test_category", "id": 999})
    assert manager.create.call_args.kwargs["description"] is None
    assert "id" not in manager.create.call_args.kwargs
    assert "description" not in projection(category)


def test_duplicate_maps_to_legacy_validation_error(monkeypatch):
    cause = Exception(1062, "sensitive duplicate details")
    error = IntegrityError("sensitive details")
    error.__cause__ = cause
    manager = MagicMock()
    manager.create.side_effect = error
    monkeypatch.setattr(Category, "objects", manager)
    with pytest.raises(CategoryError, match="^Validation error$"):
        services.create_category({"name": "phase3_test_category"})


@pytest.mark.parametrize("path", ["/", "/admin/categories"])
def test_database_errors_never_leak_sensitive_details(client, monkeypatch, path):
    def fail(_):
        raise OperationalError("password and sensitive SQL details")

    monkeypatch.setattr(services, "create_category", fail)
    response = client.post(
        path, json.dumps({"name": "phase3_test_category"}), content_type="application/json"
    )
    assert response.status_code == 500 and response.json() == {"error": "Internal Server Error"}


def test_list_failure_hides_database_details(client, monkeypatch):
    def fail():
        raise OperationalError("password and sensitive SQL details")

    monkeypatch.setattr(selectors, "all_categories", fail)
    response = client.get("/")
    assert response.status_code == 500 and response.json() == {"error": "Internal Server Error"}

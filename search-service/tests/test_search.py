from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from search_app import selectors, services
from search_app.exceptions import LegacyError
from search_app.models import SearchIndex
from search_app.serializers import FIELDS, response


@pytest.mark.parametrize("price", [None, Decimal("0"), Decimal("12.50")])
def test_projection_price_and_id(price):
    row = SimpleNamespace(**{field: None for field in FIELDS})
    row.postId = 17
    row.price = price
    row.createdAt = row.updatedAt = datetime(2026, 1, 1, tzinfo=UTC)
    data = response(row)
    assert data["id"] == data["postId"] == 17
    assert data["price"] == (format(price, ".2f") if price is not None else None)


def test_runtime_mapping():
    assert SearchIndex._meta.db_table == "searchindices" and not SearchIndex._meta.managed
    assert SearchIndex._meta.pk.name == "postId" and SearchIndex._meta.pk.column == "postId"
    assert not any(field.is_relation for field in SearchIndex._meta.fields)


@pytest.mark.parametrize(
    "data,message",
    [
        ({}, "Column 'postId' cannot be null"),
        ({"postId": 1}, "Field 'title' doesn't have a default value"),
        ({"title": None, "postId": 1}, "notNull Violation: SearchIndex.title cannot be null"),
    ],
)
def test_missing_title_legacy500(data, message):
    with pytest.raises(LegacyError) as error:
        services.sync(data)
    assert error.value.status == 500
    assert str(error.value) == message


def test_upsert_supplied_only_and_generated_times(monkeypatch):
    cursor = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = cursor
    monkeypatch.setattr(
        services,
        "connection",
        SimpleNamespace(
            cursor=lambda: context,
            ops=SimpleNamespace(adapt_datetimefield_value=lambda value: value),
        ),
    )
    assert services.sync(
        {"postId": 9, "title": "test", "price": "1.225", "createdAt": "ignored"}
    ) == {"message": "Index synced"}
    sql, values = cursor.execute.call_args.args
    assert "ON DUPLICATE KEY UPDATE" in sql and "`updatedAt`=VALUES(`updatedAt`)" in sql
    assert "`createdAt`=VALUES(`createdAt`)" not in sql
    assert "`description`" not in sql and Decimal("1.23") in values


def test_approved_filter_and_like_wildcards(monkeypatch):
    query = MagicMock()
    query.extra.return_value = query
    query.filter.return_value = query
    manager = MagicMock()
    manager.filter.return_value = query
    monkeypatch.setattr(SearchIndex, "objects", manager)
    selectors.search({"query": "%_", "minPrice": "0", "maxPrice": "20", "categoryId": "1"})
    manager.filter.assert_called_once_with(status="approved")
    assert query.extra.call_args_list[0].kwargs["params"] == ["%%_%", "%%_%"]
    query.order_by.assert_called_once_with("-createdAt")

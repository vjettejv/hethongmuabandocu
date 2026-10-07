import pytest
from conftest import compare, rows, seed_search


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"query": "Alpha"},
        {"query": "match description"},
        {"query": "alpha"},
        {"query": "%"},
        {"query": "_"},
        {"categoryId": "1"},
        {"categoryId": "invalid"},
        {"minPrice": "0"},
        {"minPrice": "12.50"},
        {"maxPrice": "12.50"},
        {"minPrice": "1", "maxPrice": "20"},
        {"query": "match", "categoryId": "1", "minPrice": "1", "maxPrice": "20.01"},
        {"query": "missing"},
        {"status": "available"},
        {"page": "2", "limit": "1"},
    ],
)
def test_search_query_contract(live, params):
    client, urls = live
    seed_search()
    responses = [
        client.get(urls["search"][kind] + "/", params=params) for kind in ("node", "python")
    ]
    assert responses[0].status_code == responses[1].status_code == 200
    compare(responses[0].json(), responses[1].json())
    for row in responses[1].json():
        assert row["id"] == row["postId"] and row["status"] == "approved"
        assert row["price"] is None or type(row["price"]) is str
    if not params:
        assert [r["id"] for r in responses[1].json()] == [5, 2, 4, 1]


@pytest.mark.parametrize(
    "payload",
    [
        {
            "postId": 19,
            "title": "phase5_test sync",
            "price": 12.50,
            "status": "approved",
            "categoryId": 1,
            "imageUrl": None,
            "categoryName": "safe",
            "description": "safe",
        },
        {"postId": 19, "title": "phase5_test sync", "price": "1.225", "status": "available"},
        {
            "postId": 19,
            "title": "phase5_test sync",
            "price": None,
            "description": None,
            "imageUrl": None,
            "categoryName": None,
            "status": "deleted",
        },
        {"postId": "19", "title": "phase5_test sync", "price": "0.00", "status": "approved"},
    ],
)
def test_sync_insert_and_price_effects(live, payload):
    client, urls = live
    result = []
    for kind in ("node", "python"):
        response = client.post(urls["search"][kind] + "/sync", json=payload)
        assert response.status_code == 200 and response.json() == {"message": "Index synced"}
        row = rows("search", "phase5_search_" + kind, "searchindices")[0]
        result.append(row)
        query = client.get(urls["search"][kind] + "/").json()
        assert bool(query) == (payload["status"] == "approved")
        if query:
            assert type(query[0]["price"]) is str
    for key in ("createdAt", "updatedAt"):
        result[0].pop(key)
        result[1].pop(key)
    assert result[0] == result[1]


@pytest.mark.parametrize("status", ["approved", "rejected", "deleted", "pending", None, "custom"])
def test_upsert_existing_preserves_omitted_fields(live, status):
    client, urls = live
    seed_search()
    results = []
    for kind in ("node", "python"):
        response = client.post(
            urls["search"][kind] + "/sync",
            json={
                "postId": 1,
                "title": "phase5_test changed",
                "status": status,
                "price": "8.25",
                "categoryName": "Changed",
                "imageUrl": None,
            },
        )
        assert response.status_code == 200
        rows_after = rows("search", "phase5_search_" + kind, "searchindices")
        assert len(rows_after) == 5
        row = next(row for row in rows_after if row["postId"] == 1)
        assert row["description"] == "match description" and row["categoryId"] == 1
        assert row["status"] == status and row["title"] == "phase5_test changed"
        results.append(row)
    # Compare observed timestamp policy separately from nondeterministic current time.
    assert (results[0]["createdAt"] == "2026-01-01 00:00:00.000000") == (
        results[1]["createdAt"] == "2026-01-01 00:00:00.000000"
    )
    for result in results:
        result.pop("createdAt")
        result.pop("updatedAt")
    assert results[0] == results[1]


@pytest.mark.parametrize("payload", [{}, {"postId": 1}, {"postId": 1, "title": None}])
def test_sync_required_title(live, payload):
    client, urls = live
    results = [
        client.post(urls["search"][kind] + "/sync", json=payload) for kind in ("node", "python")
    ]
    assert results[0].status_code == results[1].status_code == 500
    assert results[0].json() == results[1].json()

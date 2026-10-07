import re
from decimal import ROUND_HALF_UP, Decimal

import pytest
from conftest import (
    POST_DBS,
    USER_ID,
    compare_record,
    events,
    file_inventory,
    headers,
    seed_posts,
    select,
    signed_token,
    wait_for,
)


def request_pair(live, method, path, **kwargs):
    client, urls = live
    return {
        kind: client.request(method, url + path, **kwargs) for kind, url in urls["post"].items()
    }


@pytest.mark.parametrize(
    "path,ids",
    [
        ("/", [6, 5, 4]),
        ("/?status=approved", [5]),
        ("/?status=pending", [6]),
        ("/?categoryId=1", [4]),
        ("/?categoryId=999999", [6]),
        ("/?keyword=ALPHA", [4]),
        ("/?keyword=ph%beta", [5]),
        ("/?keyword=phase4_test%", [6, 5, 4]),
        ("/?keyword=nothing", []),
        ("/?status=", [6, 5, 4]),
        ("/?categoryId=1&status=approved", []),
    ],
)
def test_list_filters_and_price(live, path, ids):
    seed_posts()
    responses = request_pair(live, "GET", path)
    assert all(response.status_code == 200 for response in responses.values())
    node, python = (responses[kind].json() for kind in ("node", "python"))
    assert [row["id"] for row in node] == [row["id"] for row in python] == ids
    for left, right in zip(node, python, strict=True):
        compare_record(left, right)
        assert isinstance(right["price"], (int, float))
        assert "Images" in right and "Category" in right
    for kind in responses:
        assert len(events(live, kind, "CATEGORY")) == 1


@pytest.mark.parametrize("path,expected", [("/4", 4), ("/4/", 4), ("/6", 6)])
def test_public_detail(live, path, expected):
    seed_posts()
    responses = request_pair(live, "GET", path)
    assert all(response.status_code == 200 for response in responses.values())
    compare_record(responses["node"].json(), responses["python"].json())
    assert responses["python"].json()["id"] == expected
    if expected == 6:
        assert responses["python"].json()["Category"] == {"id": 999999, "name": "Đang cập nhật"}


@pytest.mark.parametrize("path", ["/99999999", "/not-a-number"])
def test_detail_missing(live, path):
    for response in request_pair(live, "GET", path).values():
        assert response.status_code == 404 and response.json() == {"error": "Post not found"}


@pytest.mark.parametrize(
    "path,method",
    [
        ("/my-posts", "GET"),
        ("/", "POST"),
        ("/4", "DELETE"),
        ("/admin/posts", "GET"),
        ("/admin/posts/4", "PUT"),
        ("/admin/posts/4", "DELETE"),
    ],
)
@pytest.mark.parametrize("mode", ["missing", "invalid", "expired", "wrong"])
def test_jwt_errors(live, path, method, mode):
    authorization = (
        {}
        if mode == "missing"
        else {
            "Authorization": "Bearer "
            + (
                "bad"
                if mode == "invalid"
                else signed_token(expired=mode == "expired", wrong=mode == "wrong")
            )
        }
    )
    for response in request_pair(live, method, path, headers=authorization).values():
        assert response.status_code == 401
        assert response.json() == {
            "error": "Unauthorized" if mode == "missing" else "Invalid token"
        }


def test_my_posts_and_admin_list_non_admin_jwt(live):
    seed_posts()
    auth = headers()
    for path, ids in [("/my-posts", [6, 4]), ("/admin/posts", [6, 5, 4])]:
        responses = request_pair(live, "GET", path, headers=auth)
        rows = {
            kind: response.json()["data"] if path.startswith("/admin") else response.json()
            for kind, response in responses.items()
        }
        assert all(response.status_code == 200 for response in responses.values())
        assert [row["id"] for row in rows["python"]] == ids
        for left, right in zip(rows["node"], rows["python"], strict=True):
            compare_record(left, right)


@pytest.mark.parametrize("price", ["100", "12.50", "1.234", "1.225", 25, 25.75])
@pytest.mark.parametrize("description", ["omitted", "", None])
def test_json_create_raw_types_nulls_defaults(live, price, description):
    payload = {
        "categoryId": 1,
        "title": "phase4_test Tiêu đề đồ cũ",
        "price": price,
        "condition": "legacy-custom",
        "userId": USER_ID + 1,
        "status": "approved",
    }
    if description != "omitted":
        payload["description"] = description
    responses = request_pair(live, "POST", "/", json=payload, headers=headers())
    assert all(response.status_code == 201 for response in responses.values())
    assert all(
        response.json()["message"] == "Post created successfully" for response in responses.values()
    )
    node, python = (responses[kind].json()["post"] for kind in ("node", "python"))
    compare_record(node, python, generated=True)
    assert python["userId"] == USER_ID and python["status"] == "available"
    assert python["price"] == price and type(python["price"]) is type(price)
    assert "Images" not in python and "Category" not in python
    if description == "omitted":
        assert "description" not in python
    client, urls = live
    for kind, raw in [("node", node), ("python", python)]:
        wait_for(lambda kind=kind: len(events(live, kind, "SEARCH")) == 1)
        search_payload = events(live, kind, "SEARCH")[0]["payload"]
        expected = {
            "postId": raw["id"],
            "title": payload["title"],
            "price": price,
            "categoryId": 1,
            "imageUrl": None,
            "status": "available",
            "categoryName": client.get("http://127.0.0.1:3000/categories").json()[0]["name"],
        }
        if description != "omitted":
            expected["description"] = description
        assert search_payload == expected
        query = client.get(urls["post"][kind] + f"/{raw['id']}").json()
        assert isinstance(query["price"], (int, float)) and query["Images"] == []
        expected_price = float(
            Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )
        assert query["price"] == expected_price
        assert query["title"] == payload["title"]
        assert query["description"] == (None if description == "omitted" else description)
        assert client.get(urls["search"][kind]).json() == []


@pytest.mark.parametrize("missing", ["title", "categoryId", "price"])
def test_create_missing_required(live, missing):
    payload = {"title": "phase4_test", "categoryId": 1, "price": "1"}
    del payload[missing]
    responses = request_pair(live, "POST", "/", json=payload, headers=headers())
    assert all(response.status_code == 500 for response in responses.values())
    assert (
        responses["node"].json()
        == responses["python"].json()
        == {"error": f"notNull Violation: Post.{missing} cannot be null"}
    )


@pytest.mark.parametrize("price", ["invalid", ""])
def test_invalid_price_status_and_explicit_error_divergence(live, price):
    responses = request_pair(
        live,
        "POST",
        "/",
        json={"title": "phase4_test invalid", "categoryId": 1, "price": price},
        headers=headers(),
    )
    assert all(response.status_code == 500 for response in responses.values())
    assert responses["node"].json()["error"]
    assert responses["python"].json() == {"error": "Invalid post data"}
    for database in POST_DBS.values():
        assert select("post", f"SELECT COUNT(*) FROM `{database}`.posts").strip() == "0"


@pytest.mark.parametrize("count", [0, 1, 5])
def test_multipart_images_maximum_and_create_serialization(live, count):
    client, urls = live
    auth = headers()
    for kind, url in urls["post"].items():
        files = [
            ("images", (f"phase4_test_photo{i}.bin", bytes(range(256)), "application/octet-stream"))
            for i in range(count)
        ]
        # Always force multipart, including the zero-file case.
        files += [
            ("categoryId", (None, "1")),
            ("title", (None, "phase4_test multipart")),
            ("price", (None, "123.45")),
            ("condition", (None, "anything")),
        ]
        response = client.post(url, files=files, headers=auth)
        assert response.status_code == 201
        raw = response.json()["post"]
        assert raw["categoryId"] == "1" and raw["price"] == "123.45"
        assert not {"Images", "Category", "description"} & set(raw)
        queried = client.get(url + f"/{raw['id']}").json()
        assert len(queried["Images"]) == count
        assert queried["price"] == 123.45
        for index, image in enumerate(queried["Images"]):
            assert re.fullmatch(r"/uploads/\d+-phase4_test_photo\d\.bin", image["imageUrl"])
            assert image["imageUrl"].endswith(f"photo{index}.bin")
            binary = client.get(url + image["imageUrl"])
            assert binary.content == bytes(range(256))
            assert binary.headers["content-type"] == "application/octet-stream"
        wait_for(lambda kind=kind: len(events(live, kind, "SEARCH")) == 1)
        assert events(live, kind, "SEARCH")[0]["payload"]["imageUrl"] == (
            queried["Images"][0]["imageUrl"] if count else None
        )


@pytest.mark.parametrize("field,count", [("images", 6), ("image", 1)])
def test_rejected_multipart_field_and_limit(live, field, count):
    files = [(field, (f"phase4_test_bad{i}.bin", b"data")) for i in range(count)]
    files += [
        ("categoryId", (None, "1")),
        ("title", (None, "phase4_test invalid")),
        ("price", (None, "1")),
    ]
    responses = request_pair(live, "POST", "/", files=files, headers=headers())
    assert all(response.status_code == 500 for response in responses.values())
    assert (
        responses["node"].json()
        == responses["python"].json()
        == {"error": "Internal Server Error", "details": "Unexpected field"}
    )
    assert file_inventory("python") == set()


@pytest.mark.parametrize("owner", [True, False])
def test_owner_delete_metadata_and_search(live, owner):
    seed_posts()
    responses = request_pair(
        live, "DELETE", "/4", headers=headers(user_id=USER_ID if owner else USER_ID + 1)
    )
    expected = (
        {"message": "Deleted successfully"}
        if owner
        else {"error": "Post not found or unauthorized"}
    )
    assert all(response.status_code == (200 if owner else 404) for response in responses.values())
    assert all(response.json() == expected for response in responses.values())
    for kind, database in POST_DBS.items():
        assert select("post", f"SELECT COUNT(*) FROM `{database}`.posts WHERE id=4").strip() == (
            "0" if owner else "1"
        )
        assert select(
            "post", f"SELECT COUNT(*) FROM `{database}`.images WHERE postId=4"
        ).strip() == ("0" if owner else "2")
        if owner:
            wait_for(lambda kind=kind: len(events(live, kind, "SEARCH")) == 1)
            payload = events(live, kind, "SEARCH")[0]["payload"]
            assert payload["status"] == "deleted" and payload["imageUrl"] is None
            assert payload["price"] == "12.50" and payload["postId"] == 4
            wait_for(
                lambda kind=kind: (
                    select(
                        "search",
                        f"SELECT status FROM phase4_search_{kind}.searchindices WHERE postId=4",
                    ).strip()
                    == "deleted"
                )
            )


@pytest.mark.parametrize(
    "method,path,status,body",
    [
        ("DELETE", "/99999999", 404, {"error": "Post not found or unauthorized"}),
        ("PUT", "/admin/posts/99999999", 404, {"error": "Not found"}),
        ("DELETE", "/admin/posts/99999999", 200, {"message": "Deleted"}),
    ],
)
def test_endpoint_specific_missing(live, method, path, status, body):
    for response in request_pair(
        live, method, path, json={"status": "approved"}, headers=headers()
    ).values():
        assert response.status_code == status and response.json() == body


def test_admin_delete_metadata_no_search(live):
    seed_posts()
    for response in request_pair(live, "DELETE", "/admin/posts/4", headers=headers()).values():
        assert response.status_code == 200 and response.json() == {"message": "Deleted"}
    for kind, database in POST_DBS.items():
        assert (
            select("post", f"SELECT COUNT(*) FROM `{database}`.images WHERE postId=4").strip()
            == "0"
        )
        assert events(live, kind, "SEARCH") == []


@pytest.mark.parametrize("status", ["approved", "rejected", "pending", "custom", None])
def test_moderation_raw_search_and_exact_message(live, status):
    seed_posts()
    responses = request_pair(
        live, "PUT", "/admin/posts/4", json={"status": status}, headers=headers()
    )
    assert all(response.status_code == 200 for response in responses.values())
    node, python = (responses[kind].json()["data"] for kind in ("node", "python"))
    compare_record(node, python, generated=True)
    assert python["price"] == "12.50" and python["status"] == status
    assert "Images" in python and "Category" not in python
    client, urls = live
    for kind in responses:
        wait_for(lambda kind=kind: len(events(live, kind, "SEARCH")) == 1)
        outgoing = events(live, kind, "SEARCH")[0]["payload"]
        assert outgoing == {
            "postId": 4,
            "title": "phase4_test Alpha",
            "description": "",
            "price": "12.50",
            "categoryId": 1,
            "imageUrl": "/uploads/phase4_test_fixture.bin",
            "categoryName": python.get("Category", {}).get(
                "name", client.get("http://127.0.0.1:3000/categories").json()[0]["name"]
            ),
            "status": status,
        }
        wait_for(
            lambda kind=kind: (
                select(
                    "search",
                    f"SELECT COUNT(*) FROM phase4_search_{kind}.searchindices WHERE postId=4",
                ).strip()
                == "1"
            )
        )
        searched = client.get(urls["search"][kind]).json()
        assert len(searched) == (1 if status == "approved" else 0)
        if status in {"approved", "rejected"}:
            wait_for(lambda kind=kind: len(events(live, kind, "MESSAGE")) == 1)
            message = events(live, kind, "MESSAGE")[0]["payload"]
            assert message == {
                "receiverId": USER_ID,
                "title": "Bài viết đã được duyệt"
                if status == "approved"
                else "Bài viết bị từ chối",
                "message": 'Bài viết "phase4_test Alpha" của bạn '
                + (
                    "đã được hiển thị trên chợ." if status == "approved" else "đã bị từ chối duyệt."
                ),
            }
            wait_for(
                lambda kind=kind: (
                    select(
                        "message",
                        f"SELECT COUNT(*) FROM phase4_message_{kind}.notifications "
                        f"WHERE userId={USER_ID}",
                    ).strip()
                    == "1"
                )
            )
            # Repeating a status syncs Search again but produces no second notification.
            assert (
                client.put(
                    urls["post"][kind] + "/admin/posts/4",
                    json={"status": status},
                    headers=headers(),
                ).status_code
                == 200
            )
            wait_for(lambda kind=kind: len(events(live, kind, "SEARCH")) == 2)
            assert len(events(live, kind, "MESSAGE")) == 1

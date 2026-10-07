import pytest
from conftest import BODY, USER, compare, files, read_file, seed_reviews


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"rating": "1"},
        {"rating": "5"},
        {"rating": "3"},
        {"hasImage": "true"},
        {"hasImage": "false"},
        {"hasImage": "TRUE"},
        {"rating": "5", "hasImage": "true"},
        {"rating": "2"},
        {"rating": "0"},
        {"rating": "invalid"},
    ],
)
def test_list_filters_ordering(live, params):
    client, urls = live
    seed_reviews()
    responses = [
        client.get(urls["review"][kind] + f"/user/{USER}", params=params)
        for kind in ("node", "python")
    ]
    assert responses[0].status_code == responses[1].status_code == 200
    compare(responses[0].json(), responses[1].json())
    if not params:
        assert [row["id"] for row in responses[0].json()] == [2, 3, 1]


@pytest.mark.parametrize(
    "data",
    [
        {"reviewerId": 11, "revieweeId": USER, "rating": 1},
        {"reviewerId": "11", "revieweeId": str(USER), "rating": "5", "comment": "safe"},
        {"reviewerId": 11, "revieweeId": USER, "rating": 3, "postId": None, "comment": None},
        {"reviewerId": 11, "revieweeId": USER, "rating": 4, "comment": ""},
    ],
)
@pytest.mark.parametrize("multipart", [False, True])
def test_create_raw_types_and_nulls(live, data, multipart):
    client, urls = live
    responses = []
    for kind in ("node", "python"):
        # JSON preserves explicit nulls; multipart has string values.
        payload = (
            {key: str(value) for key, value in data.items() if value is not None}
            if multipart
            else data
        )
        arguments = (
            {
                "data": payload,
                "files": {"image": ("phase5_test_optional.bin", BODY, "application/octet-stream")},
            }
            if multipart
            else {"json": payload}
        )
        result = client.post(urls["review"][kind] + "/", **arguments)
        assert result.status_code == 201, result.text
        responses.append(result.json())
        if multipart:
            assert read_file(kind, result.json()["imageUrl"]) == BODY
        reloaded = client.get(urls["review"][kind] + f"/user/{USER}").json()[0]
        assert type(reloaded["rating"]) is int and "postId" in reloaded and "comment" in reloaded
    compare(*responses, generated=True)


@pytest.mark.parametrize("rating", [0, 6, "invalid", None])
def test_invalid_rating_status(live, rating):
    client, urls = live
    results = [
        client.post(
            urls["review"][kind] + "/",
            json={"reviewerId": 11, "revieweeId": USER, "rating": rating},
        )
        for kind in ("node", "python")
    ]
    assert results[0].status_code == results[1].status_code == 500
    if rating != "invalid":
        assert results[0].json() == results[1].json()
    else:
        assert results[1].json() == {"error": "Invalid review data"}


@pytest.mark.parametrize("data", [{}, {"rating": 1}, {"reviewerId": 11, "rating": 1}])
def test_missing_required(live, data):
    client, urls = live
    responses = [client.post(urls["review"][kind] + "/", json=data) for kind in ("node", "python")]
    assert responses[0].status_code == responses[1].status_code == 500
    assert responses[0].json() == responses[1].json()


@pytest.mark.parametrize(
    "data",
    [
        {"rating": 5},
        {"comment": "phase5_test alpha"},
        {"rating": "2"},
        {"comment": "changed"},
        {"comment": ""},
        {"rating": 0},
        {"rating": None},
        {"comment": None},
        {},
    ],
)
def test_update_truthy_semantics(live, data):
    client, urls = live
    seed_reviews()
    responses = [client.put(urls["review"][kind] + "/1", json=data) for kind in ("node", "python")]
    assert responses[0].status_code == responses[1].status_code == 200
    compare(responses[0].json(), responses[1].json(), generated=True)
    if data.get("comment") == "":
        assert responses[1].json()["comment"] == "phase5_test alpha"


@pytest.mark.parametrize("method", ["PUT", "DELETE"])
@pytest.mark.parametrize("identifier", ["999999", "invalid"])
def test_missing_review(live, method, identifier):
    client, urls = live
    responses = [
        client.request(method, urls["review"][kind] + "/" + identifier, json={"comment": "safe"})
        for kind in ("node", "python")
    ]
    assert responses[0].status_code == responses[1].status_code == 404
    assert responses[0].json() == responses[1].json() == {"error": "Review not found"}


def test_image_replacement_delete_and_public_routes(live):
    client, urls = live
    # Exercise ordinary available-dependency lifecycle after the outage test restarts Post.
    assert client.get(urls["post"] + "/").status_code == 200
    responses = []
    for kind in ("node", "python"):
        url = urls["review"][kind]
        first = client.post(
            url + "/",
            data={"reviewerId": "11", "revieweeId": str(USER), "rating": "4"},
            files={"image": ("phase5_test_a.png", BODY, "image/png")},
        )
        assert first.status_code == 201
        row = first.json()
        old = row["imageUrl"]
        assert read_file(kind, old) == BODY
        second = client.put(
            url + "/" + str(row["id"]),
            data={"comment": ""},
            files={"image": ("phase5_test_b.jpg", BODY + b"B", "image/jpeg")},
        )
        assert second.status_code == 200
        new = second.json()["imageUrl"]
        assert old.removeprefix("/uploads/") not in files(kind)
        assert read_file(kind, new) == BODY + b"B"
        if kind == "python":
            assert client.get(urls["gateway"] + new).content == BODY + b"B"
        deleted = client.delete(url + "/" + str(row["id"]))
        assert deleted.status_code == 200 and deleted.json() == {
            "message": "Review deleted successfully"
        }
        assert new.removeprefix("/uploads/") not in files(kind)
        assert client.get(url + f"/user/{USER}").json() == []
        responses.append(second.json())
    compare(*responses, generated=True)


def test_delete_without_image(live):
    client, urls = live
    seed_reviews()
    responses = [client.delete(urls["review"][kind] + "/1") for kind in ("node", "python")]
    assert responses[0].status_code == responses[1].status_code == 200
    assert responses[0].json() == responses[1].json()


@pytest.mark.parametrize("mode", ["wrong-field", "two-images"])
def test_unexpected_files_controlled(live, mode):
    client, urls = live
    uploads = [("images" if mode == "wrong-field" else "image", ("phase5_test_x.bin", BODY))]
    if mode == "two-images":
        uploads.append(("image", ("phase5_test_y.bin", BODY)))
    responses = [
        client.post(
            urls["review"][kind] + "/",
            data={"reviewerId": "11", "revieweeId": str(USER), "rating": "4"},
            files=uploads,
        )
        for kind in ("node", "python")
    ]
    assert responses[0].status_code == responses[1].status_code == 500
    assert responses[1].json() == {"error": "Unexpected field"}


@pytest.mark.parametrize("rating", [1.5, "1.5"])
def test_fractional_rating_mysql_rounding(live, rating):
    client, urls = live
    responses = []
    for kind in ("node", "python"):
        response = client.post(
            urls["review"][kind] + "/",
            json={"reviewerId": 11, "revieweeId": USER, "rating": rating},
        )
        assert response.status_code == 201
        assert response.json()["rating"] == rating
        assert client.get(urls["review"][kind] + f"/user/{USER}").json()[0]["rating"] == 2
        responses.append(response.json())
    compare(*responses, generated=True)

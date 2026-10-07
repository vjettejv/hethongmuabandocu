import pytest
from conftest import BODY, USER, headers, rows, select, wait_for


@pytest.mark.parametrize("status", ["approved", "rejected", "pending", "custom"])
def test_post_create_moderate_owner_delete_to_django_search(live, status):
    client, urls = live
    auth = headers()
    created = client.post(
        urls["gateway"] + "/posts",
        headers=auth,
        data={
            "categoryId": "1",
            "title": "phase5_test chain",
            "price": "12.50",
            "description": "safe",
        },
        files={"images": ("phase5_test_post.bin", BODY, "application/octet-stream")},
    )
    assert created.status_code == 201
    identifier = created.json()["post"]["id"]
    projected = wait_for(lambda: rows("search", "phase5_search_python", "searchindices"))[0]
    assert projected["postId"] == identifier and projected["status"] == "available"
    detail = client.get(urls["gateway"] + f"/posts/{identifier}").json()
    assert type(detail["price"]) is float and detail["Images"] and detail["Category"]
    assert client.get(urls["gateway"] + detail["Images"][0]["imageUrl"]).content == BODY
    assert (
        client.post(
            urls["gateway"] + "/favorites/toggle", headers=auth, json={"postId": identifier}
        ).status_code
        == 201
    )
    assert client.get(urls["gateway"] + "/favorites/my-favorites", headers=auth).json() == [detail]
    moderated = client.put(
        urls["gateway"] + f"/admin/posts/{identifier}", headers=auth, json={"status": status}
    )
    assert moderated.status_code == 200
    wait_for(lambda: rows("search", "phase5_search_python", "searchindices")[0]["status"] == status)
    events = wait_for(lambda: client.get(urls["dependencies"] + "/__events").json()["events"])
    syncs = [event for event in events if event["dependency"] == "SEARCH"]
    assert (
        syncs[0]["payload"]["postId"] == identifier and syncs[0]["payload"]["status"] == "available"
    )
    assert (
        syncs[0]["payload"]["price"] == "12.50"
        and syncs[0]["payload"]["imageUrl"] == detail["Images"][0]["imageUrl"]
    )
    if status == "approved":
        assert client.get(urls["gateway"] + "/search").json()[0]["id"] == identifier
    else:
        assert client.get(urls["gateway"] + "/search").json() == []
    assert client.delete(urls["gateway"] + f"/posts/{identifier}", headers=auth).status_code == 200
    projected = wait_for(
        lambda: rows("search", "phase5_search_python", "searchindices")[0]["status"] == "deleted"
    )
    assert projected
    assert rows("search", "phase5_search_python", "searchindices")[0]["imageUrl"] is None
    assert client.get(urls["gateway"] + "/favorites/my-favorites", headers=auth).json() == []
    assert client.get(urls["gateway"] + detail["Images"][0]["imageUrl"]).content == BODY


def test_admin_delete_keeps_stale_search(live):
    client, urls = live
    auth = headers()
    response = client.post(
        urls["post"] + "/",
        headers=auth,
        json={"title": "phase5_test admin", "price": 1, "categoryId": 1},
    )
    identifier = response.json()["post"]["id"]
    wait_for(lambda: rows("search", "phase5_search_python", "searchindices"))
    assert (
        client.delete(urls["gateway"] + f"/admin/posts/{identifier}", headers=auth).status_code
        == 200
    )
    assert rows("search", "phase5_search_python", "searchindices")[0]["status"] == "available"


def test_review_chunked_shared_post_serving(live):
    client, urls = live
    boundary = "phase5-stream-boundary"
    body = b""
    for key, value in [("reviewerId", "11"), ("revieweeId", str(USER)), ("rating", "5")]:
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
        ).encode()
    body += (
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="image"; '
            'filename="phase5_test_chunked.png"\r\nContent-Type: image/png\r\n\r\n'
        ).encode()
        + BODY
        + b"\r\n"
        + f"--{boundary}--\r\n".encode()
    )
    response = client.post(
        urls["gateway"] + "/reviews",
        headers={
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "X-Request-ID": "phase5-chunked",
        },
        content=(body[i : i + 17] for i in range(0, len(body), 17)),
    )
    assert response.status_code == 201, response.text
    url = response.json()["imageUrl"]
    assert client.get(urls["gateway"] + url).content == BODY
    assert client.get(urls["gateway"] + url, headers={"Range": "bytes=1-4"}).content == BODY[1:5]
    assert (
        client.delete(urls["gateway"] + "/reviews/" + str(response.json()["id"])).status_code == 200
    )
    assert client.get(urls["gateway"] + url).status_code == 404


def test_review_does_not_unlink_post_referenced_file(live):
    client, urls = live
    created = client.post(
        urls["review"]["python"] + "/",
        data={"reviewerId": "11", "revieweeId": str(USER), "rating": "4"},
        files={"image": ("phase5_test_shared.png", BODY, "image/png")},
    ).json()
    url = created["imageUrl"]
    value = "CONVERT(0x" + url.encode().hex() + " USING utf8mb4)"
    select(
        "post",
        f"INSERT INTO phase5_post_test.posts(id,userId,categoryId,title,price,status,"
        f"createdAt,updatedAt) VALUES(840,{USER},1,'phase5_test shared',1,"
        f"'available','2026-01-01','2026-01-01');INSERT INTO "
        f"phase5_post_test.images(postId,imageUrl,createdAt,updatedAt) VALUES(840,"
        f"{value},'2026-01-01','2026-01-01')",
    )
    assert client.delete(urls["review"]["python"] + "/" + str(created["id"])).status_code == 200
    assert client.get(urls["gateway"] + url).content == BODY


def test_deployed_business_docs_health(live):
    client, urls = live
    expected = {
        "favorite": {"/toggle", "/check/{postId}", "/my-favorites"},
        "review": {"/", "/user/{userId}", "/{id}"},
        "search": {"/", "/sync"},
    }
    for svc in expected:
        url = urls[svc]["python"]
        for path in ("/health", "/ready"):
            assert client.get(url + path).status_code == 200
        schema = client.get(
            url + "/schema/", headers={"Accept": "application/vnd.oai.openapi+json"}
        ).json()
        assert set(schema["paths"]) == expected[svc] | {"/health", "/ready"}

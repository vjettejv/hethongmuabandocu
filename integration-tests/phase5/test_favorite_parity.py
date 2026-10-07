from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from conftest import USER, compare, container, docker, headers, published, select, wait_for


@pytest.mark.parametrize("suffix", ["", "/"])
def test_toggle_check_remove_and_no_validation(live, suffix):
    client, urls = live
    auth = headers()
    for kind in ("node", "python"):
        url = urls["favorite"][kind]
        assert client.get(url + "/check/999999" + suffix, headers=auth).json() == {
            "isFavorited": False
        }
        result = client.post(
            url + "/toggle" + suffix, json={"postId": 999999, "userId": USER + 1}, headers=auth
        )
        assert result.status_code == 201 and result.json() == {
            "message": "Added to favorites",
            "isFavorited": True,
        }
        assert (
            select(
                "favorite", f"SELECT userId,postId FROM phase5_favorite_{kind}.favorites"
            ).strip()
            == f"{USER}\t999999"
        )
        assert client.get(url + "/check/999999" + suffix, headers=auth).json() == {
            "isFavorited": True
        }
        assert client.get(url + "/my-favorites" + suffix, headers=auth).json() == []
        result = client.post(url + "/toggle" + suffix, json={"postId": 999999}, headers=auth)
        assert result.status_code == 200 and result.json() == {
            "message": "Removed from favorites",
            "isFavorited": False,
        }
        assert client.delete(url + "/999999", headers=auth).status_code == 404


@pytest.mark.parametrize(
    "method,path", [("POST", "/toggle"), ("GET", "/check/1"), ("GET", "/my-favorites")]
)
@pytest.mark.parametrize("token", ["missing", "invalid", "expired", "wrong"])
def test_jwt_parity(live, method, path, token):
    client, urls = live
    auth = headers(token)
    responses = [
        client.request(method, urls["favorite"][kind] + path, headers=auth, json={"postId": 1})
        for kind in ("node", "python")
    ]
    assert responses[0].status_code == responses[1].status_code == 401
    assert responses[0].json() == responses[1].json()


@pytest.mark.parametrize("data", [{}, {"postId": None}, {"postId": 0}, {"postId": "12"}])
def test_toggle_input_parity(live, data):
    client, urls = live
    responses = [
        client.post(urls["favorite"][kind] + "/toggle", json=data, headers=headers())
        for kind in ("node", "python")
    ]
    assert responses[0].status_code == responses[1].status_code
    assert responses[0].json() == responses[1].json()


def test_parallel_uniqueness(live):
    client, urls = live
    auth = headers()
    for kind in ("node", "python"):
        url = urls["favorite"][kind] + "/toggle"
        with ThreadPoolExecutor(max_workers=6) as pool:
            responses = list(
                pool.map(
                    lambda _, url=url: client.post(url, json={"postId": 98123}, headers=auth),
                    range(6),
                )
            )
        assert all(r.status_code in {200, 201, 500} for r in responses)
        assert (
            int(
                select(
                    "favorite",
                    f"SELECT COUNT(*) FROM phase5_favorite_{kind}.favorites WHERE userId={USER} "
                    f"AND postId=98123",
                )
            )
            <= 1
        )


def test_hydration_real_post_types_missing_and_empty(live):
    client, urls = live
    auth = headers()
    for kind in ("node", "python"):
        assert client.get(urls["favorite"][kind] + "/my-favorites", headers=auth).json() == []
    select(
        "post",
        f"INSERT INTO phase5_post_test.posts(id,userId,categoryId,title,description,"
        f"price,status,`condition`,createdAt,updatedAt) VALUES(719,{USER},1,"
        f"'phase5_test hydration',NULL,12.50,'available',NULL,'2026-01-01',"
        f"'2026-01-01'),(720,{USER},999999,'phase5_test fallback',NULL,0,'approved',"
        f"NULL,'2026-01-02','2026-01-02');INSERT INTO phase5_post_test.images(postId,"
        f"imageUrl,createdAt,updatedAt) VALUES(719,"
        f"'/uploads/phase5_test_hydration.bin','2026-01-01','2026-01-01')",
    )
    results = []
    for kind in ("node", "python"):
        for identifier in (719, 999999, 720):
            assert (
                client.post(
                    urls["favorite"][kind] + "/toggle", json={"postId": identifier}, headers=auth
                ).status_code
                == 201
            )
        result = client.get(urls["favorite"][kind] + "/my-favorites", headers=auth)
        assert result.status_code == 200
        data = result.json()
        assert [p["id"] for p in data] == [719, 720]
        assert data[0]["price"] == 12.5 and type(data[0]["price"]) is float
        assert data[0]["Images"][0]["imageUrl"] == "/uploads/phase5_test_hydration.bin"
        assert data[1]["Category"]["name"] == "Đang cập nhật"
        results.append(data)
    compare(*results)


def test_post_unavailable_filtered(live):
    client, urls = live
    auth = headers()
    for kind in ("node", "python"):
        select(
            "favorite",
            f"INSERT INTO phase5_favorite_{kind}.favorites"
            f"(userId,postId,createdAt,updatedAt) VALUES({USER},1,NOW(),NOW())",
        )
    docker("stop", container("post-phase5"))
    try:
        for kind in ("node", "python"):
            result = client.get(urls["favorite"][kind] + "/my-favorites", headers=auth)
            assert result.status_code == 200 and result.json() == []
    finally:
        docker("start", container("post-phase5"))
        # Docker can assign a new ephemeral host port when a stopped container starts.
        urls["post"] = published("post-phase5", 3003)

        def post_ready():
            try:
                return client.get(urls["post"] + "/ready", timeout=2).status_code == 200
            except httpx.HTTPError:
                return False

        wait_for(post_ready)

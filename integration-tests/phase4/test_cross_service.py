import pytest
from conftest import (
    POST_DBS,
    USER_ID,
    container,
    docker,
    events,
    file_inventory,
    headers,
    seed_posts,
    select,
    wait_for,
)


@pytest.mark.parametrize("mode", ["failure", "invalid"])
def test_category_outage_fallback_and_create_success(live, mode):
    seed_posts()
    client, urls = live
    for kind in ("node", "python"):
        control = urls["dependencies"][kind]
        assert client.post(control + "/__control", json={"CATEGORY": mode}).status_code == 200
        detail = client.get(urls["post"][kind] + "/4")
        assert detail.status_code == 200
        assert detail.json()["Category"] == {"id": 1, "name": "Đang cập nhật"}
        response = client.post(
            urls["post"][kind],
            json={"categoryId": 999999, "title": "phase4_test orphan category", "price": "1"},
            headers=headers(),
        )
        assert response.status_code == 201
        wait_for(lambda kind=kind: len(events(live, kind, "SEARCH")) == 1)
        assert events(live, kind, "SEARCH")[0]["payload"]["categoryName"] == "Đang cập nhật"


@pytest.mark.parametrize("dependency", ["SEARCH", "MESSAGE"])
def test_dependency_http_outage_does_not_fail_write(live, dependency):
    client, urls = live
    seed_posts()
    for kind in ("node", "python"):
        assert (
            client.post(
                urls["dependencies"][kind] + "/__control", json={dependency: "failure"}
            ).status_code
            == 200
        )
        response = client.put(
            urls["post"][kind] + "/admin/posts/4", json={"status": "approved"}, headers=headers()
        )
        assert response.status_code == 200 and response.json()["data"]["status"] == "approved"
        wait_for(lambda kind=kind: len(events(live, kind, dependency)) == 1)
        assert (
            select("post", f"SELECT status FROM {POST_DBS[kind]}.posts WHERE id=4").strip()
            == "approved"
        )


def test_outgoing_request_id_and_one_category_call(live):
    client, urls = live
    seed_posts()
    response = client.put(
        urls["post"]["python"] + "/admin/posts/4",
        json={"status": "approved"},
        headers={**headers(), "X-Request-ID": "phase4-dependency-id"},
    )
    assert response.status_code == 200
    wait_for(lambda: len(events(live, "python")) == 3)
    captured = events(live, "python")
    assert {event["dependency"] for event in captured} == {"CATEGORY", "SEARCH", "MESSAGE"}
    assert all(event["requestId"] == "phase4-dependency-id" for event in captured)


def test_create_search_failure_keeps_post_and_image(live):
    client, urls = live
    for kind in ("node", "python"):
        assert (
            client.post(
                urls["dependencies"][kind] + "/__control", json={"SEARCH": "failure"}
            ).status_code
            == 200
        )
        response = client.post(
            urls["post"][kind],
            headers=headers(),
            files=[
                ("categoryId", (None, "1")),
                ("title", (None, "phase4_test failed sync")),
                ("price", (None, "1")),
                ("images", ("phase4_test_search_failure.bin", b"data")),
            ],
        )
        assert response.status_code == 201
        identifier = response.json()["post"]["id"]
        wait_for(lambda kind=kind: len(events(live, kind, "SEARCH")) == 1)
        detail = client.get(urls["post"][kind] + f"/{identifier}").json()
        assert len(detail["Images"]) == 1 and detail["status"] == "available"


@pytest.mark.parametrize("alias", [False, True])
def test_gateway_admin_aliases_and_no_redirect(live, alias):
    seed_posts()
    client, urls = live
    path = "/posts/admin/posts" if alias else "/admin/posts"
    auth = headers()
    for spelling in (path, path + "/"):
        response = client.get(urls["gateway"] + spelling, headers=auth)
        assert response.status_code == 200 and len(response.json()["data"]) == 3
    assert (
        client.put(
            urls["gateway"] + path + "/4", headers=auth, json={"status": "custom"}
        ).status_code
        == 200
    )
    assert client.delete(urls["gateway"] + path + "/4", headers=auth).json() == {
        "message": "Deleted"
    }


@pytest.mark.parametrize("path", ["/posts", "/posts/", "/posts/4", "/posts/4/"])
def test_gateway_public_paths_no_redirect(live, path):
    seed_posts()
    client, urls = live
    response = client.get(urls["gateway"] + path)
    assert response.status_code == 200 and "location" not in response.headers


def test_real_node_favorite_hydrates_python_post_and_skips_missing(live):
    seed_posts()
    select(
        "favorite",
        "INSERT INTO phase4_favorite_test.favorites "
        "(userId,postId,createdAt,updatedAt) VALUES "
        f"({USER_ID},4,NOW(),NOW()),({USER_ID},99999999,NOW(),NOW())",
    )
    client, urls = live
    for base, path in [
        (urls["favorite"], "/my-favorites"),
        (urls["gateway"], "/favorites/my-favorites"),
    ]:
        response = client.get(base + path, headers=headers())
        assert response.status_code == 200
        rows = response.json()
        assert len(rows) == 1 and rows[0]["id"] == 4
        assert rows[0]["price"] == 12.5 and isinstance(rows[0]["price"], (int, float))
        assert len(rows[0]["Images"]) == 2 and rows[0]["Category"]["id"] == 1
    client.delete(urls["post"]["python"] + "/admin/posts/4", headers=headers())
    assert client.get(urls["favorite"] + "/my-favorites", headers=headers()).json() == []


def test_atomic_image_failure_rolls_back_post_and_owned_files(live):
    script = """
import os
os.environ['DJANGO_SETTINGS_MODULE']='config.settings'
import django
django.setup()
from unittest.mock import patch
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.services import create
from posts.models import Post,Image
before=Post.objects.count()
with patch.object(Image.objects,'bulk_create',side_effect=IntegrityError('synthetic')):
 try:
  create(4100100,{'categoryId':1,'title':'phase4_test rollback','price':'1'},
         [SimpleUploadedFile('phase4_test_rollback.bin',b'rollback')],'phase4-rollback')
 except IntegrityError: pass
 else: raise AssertionError('Expected image write failure')
assert Post.objects.count()==before
print('PASS transaction rollback')
"""
    before = file_inventory("python")
    assert (
        docker("exec", container("post-candidate"), "python", "-c", script)
        == "PASS transaction rollback"
    )
    assert file_inventory("python") == before


def test_gateway_streamed_multipart_and_binary_range_owner_delete_keeps_file(live):
    client, urls = live
    boundary = "phase4-stream-boundary"
    file_content = bytes(range(256)) * 24576  # 6 MiB, above Django's in-memory file threshold.
    prefix = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="categoryId"\r\n\r\n1\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\n'
        "phase4_test streamed\r\n"
        f'--{boundary}\r\nContent-Disposition: form-data; name="price"\r\n\r\n9.50\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="images"; '
        'filename="phase4_test_stream.bin"\r\nContent-Type: application/octet-stream\r\n\r\n'
    ).encode()
    suffix = (
        f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="images"; '
        'filename="phase4_test_second.bin"\r\nContent-Type: application/octet-stream\r\n\r\n'
        f"second\r\n--{boundary}--\r\n"
    ).encode()

    def chunks():
        yield prefix
        for index in range(0, len(file_content), 65536):
            yield file_content[index : index + 65536]
        yield suffix

    response = client.post(
        urls["gateway"] + "/posts",
        content=chunks(),
        headers={
            **headers(),
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        },
    )
    assert response.status_code == 201
    identifier = response.json()["post"]["id"]
    detail = client.get(urls["gateway"] + f"/posts/{identifier}").json()
    assert len(detail["Images"]) == 2
    url = urls["gateway"] + detail["Images"][0]["imageUrl"]
    binary = client.get(url)
    assert binary.content == file_content and int(binary.headers["content-length"]) == len(
        file_content
    )
    partial = client.get(url, headers={"Range": "bytes=100-199"})
    assert partial.status_code == 206 and partial.content == file_content[100:200]
    assert client.head(url).headers["content-length"] == str(len(file_content))
    assert client.get(url, headers={"If-None-Match": binary.headers["etag"]}).status_code == 304
    assert (
        client.delete(urls["gateway"] + f"/posts/{identifier}", headers=headers()).status_code
        == 200
    )
    assert client.get(url).content == file_content  # Legacy physical files remain.


def test_synthetic_preexisting_file_served_by_node_and_python(live):
    name = "4100000000000-phase4_test_preexisting.bin"
    payload = b"phase4-preexisting\x00\xff\x01"
    for kind in ("node", "python"):
        service = "post-reference" if kind == "node" else "post-candidate"
        if kind == "node":
            script = (
                "require('fs').writeFileSync('/app/uploads/'+process.argv[1],"
                "Buffer.from(process.argv[2],'hex'),{flag:'wx'});"
            )
            docker("exec", container(service), "node", "-e", script, name, payload.hex())
        else:
            script = (
                "import sys,pathlib; p=pathlib.Path('/app/uploads')/sys.argv[1]; "
                "p.open('xb').write(bytes.fromhex(sys.argv[2]))"
            )
            docker("exec", container(service), "python", "-c", script, name, payload.hex())
    client, urls = live
    for base in urls["post"].values():
        response = client.get(base + "/uploads/" + name)
        assert response.content == payload and response.status_code == 200
        assert "content-disposition" not in response.headers
        response = client.get(base + "/uploads/" + name, headers={"Range": "bytes=0-5"})
        assert response.status_code == 206 and response.content == payload[:6]
    assert client.get(urls["gateway"] + "/uploads/" + name).content == payload


def test_empty_favorites_and_null_category_fallback(live):
    client, urls = live
    assert client.get(urls["favorite"] + "/my-favorites", headers=headers()).json() == []
    seed_posts()
    select(
        "favorite",
        "INSERT INTO phase4_favorite_test.favorites "
        "(userId,postId,createdAt,updatedAt) VALUES "
        f"({USER_ID},6,NOW(),NOW())",
    )
    row = client.get(urls["favorite"] + "/my-favorites", headers=headers()).json()[0]
    assert row["Category"] == {"id": 999999, "name": "Đang cập nhật"}

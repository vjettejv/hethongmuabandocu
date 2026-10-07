import json
import time

from conftest import AUTH_ID, literal, node_token, select


def test_node_message_contacts_consume_django_user_and_handle_404(live):
    client, urls = live
    peer, missing = AUTH_ID + 1, AUTH_ID + 2
    profile = client.put(
        urls["user"]["python"] + f"/{peer}",
        json={"fullName": "phase3_test_contact", "avatar": None},
    )
    assert profile.status_code == 200 and profile.json()["authId"] == str(peer)
    assert client.get(urls["user"]["python"] + f"/{missing}").status_code == 404
    for contact in [peer, missing]:
        select(
            "message",
            "INSERT INTO phase3_message_test.messages "
            "(senderId,receiverId,content,isRead,createdAt,updatedAt) VALUES "
            f"({AUTH_ID},{contact},'phase3_test_message',0,UTC_TIMESTAMP(),UTC_TIMESTAMP())",
        )
    headers = {"Authorization": "Bearer " + node_token()}
    response = client.get(urls["gateway"] + "/messages/contacts", headers=headers)
    assert response.status_code == 200 and isinstance(response.json()["data"], list)
    contacts = {item["id"]: item for item in response.json()["data"]}
    assert contacts[peer]["user"] == {
        "id": peer,
        "fullName": "phase3_test_contact",
        "username": "phase3_test_contact",
    }
    assert contacts[missing]["user"] == {"id": missing, "username": f"User {missing}"}
    assert contacts[peer]["lastMessage"]["content"] == "phase3_test_message"


def test_node_post_list_detail_and_isolated_create_consume_django_category(live):
    client, urls = live
    category = client.post(
        urls["category"]["python"], json={"name": "phase3_test_post_category", "description": None}
    )
    assert category.status_code == 201
    category_id = category.json()["id"]
    headers = {"Authorization": "Bearer " + node_token()}
    payload = {
        "categoryId": str(category_id),
        "title": "phase3_test_post",
        "price": "12.34",
        "description": "phase3_test_post_description",
        "condition": "used",
    }
    response = client.post(
        urls["gateway"] + "/posts",
        files=[(key, (None, value)) for key, value in payload.items()],
        headers=headers,
    )
    assert response.status_code == 201
    post_id = response.json()["post"]["id"]
    deadline = time.monotonic() + 8
    while True:
        synced = client.get(urls["search_fixture"] + f"/sync/{post_id}")
        if synced.status_code == 200:
            break
        assert time.monotonic() < deadline, "Isolated Post create did not sync category information"
        time.sleep(0.1)
    assert synced.json() == {
        "postId": post_id,
        "categoryId": str(category_id),
        "categoryName": "phase3_test_post_category",
    }
    for path in ["/posts", f"/posts/{post_id}"]:
        result = client.get(urls["gateway"] + path)
        assert result.status_code == 200
        post = result.json()[0] if isinstance(result.json(), list) else result.json()
        assert (
            post["id"] == post_id
            and post["Category"] == client.get(urls["category"]["python"]).json()[0]
        )
        assert post["Category"]["name"] == "phase3_test_post_category"
        assert isinstance(post["price"], float)
    assert (
        select(
            "post",
            f"SELECT COUNT(*) FROM phase3_post_test.posts WHERE id={post_id} "
            f"AND title={literal('phase3_test_post')}",
        ).strip()
        == "1"
    )
    # Search requests go to a test transport fixture, never the legacy Search service.
    assert json.loads(
        select("post", "SELECT JSON_ARRAYAGG(title) FROM phase3_post_test.posts")
    ) == ["phase3_test_post"]

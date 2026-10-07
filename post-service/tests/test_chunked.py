from io import BytesIO

import pytest
from common.chunked import ChunkedBodyAdapter


@pytest.mark.parametrize("size", [0, 100, 400000])
def test_terminated_body_gets_real_length_and_disk_spooling(size):
    content = b"x" * size
    seen = []

    def app(environ, start_response):
        assert environ["CONTENT_LENGTH"] == str(size)
        seen.append(environ["wsgi.input"].read())
        if size > 256 * 1024:
            assert environ["wsgi.input"]._rolled is True
        return [b"ok"]

    environ = {"wsgi.input": BytesIO(content), "wsgi.input_terminated": True}
    response = ChunkedBodyAdapter(app)(environ, lambda *_: None)
    assert list(response) == [b"ok"] and seen == [content]
    response.close()
    assert environ["wsgi.input"].closed


def test_known_length_is_passed_through():
    environ = {"CONTENT_LENGTH": "3", "wsgi.input": BytesIO(b"abc")}
    original = environ["wsgi.input"]

    def app(env, start):
        return [env["wsgi.input"].read()]

    assert ChunkedBodyAdapter(app)(environ, None) == [b"abc"]
    assert environ["wsgi.input"] is original


def test_body_limit_matches_nginx_without_memory_growth():
    adapter = ChunkedBodyAdapter(lambda *_: pytest.fail("must not call Django"), max_bytes=3)
    statuses = []
    response = adapter(
        {"wsgi.input": BytesIO(b"abcd"), "wsgi.input_terminated": True},
        lambda status, headers: statuses.append(status),
    )
    assert statuses == ["413 Payload Too Large"]
    assert response == [b'{"error":"Request too large"}']

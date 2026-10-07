"""Adapt decoded, terminated Gunicorn bodies to Django's Content-Length contract."""

from tempfile import SpooledTemporaryFile


class BufferedResponse:
    def __init__(self, response, stream):
        self.response = response
        self.stream = stream

    def __iter__(self):
        yield from self.response

    def close(self):
        try:
            if hasattr(self.response, "close"):
                self.response.close()
        finally:
            self.stream.close()


class ChunkedBodyAdapter:
    def __init__(self, application, max_bytes=50 * 1024 * 1024):
        self.application = application
        self.max_bytes = max_bytes

    def __call__(self, environ, start_response):
        if environ.get("CONTENT_LENGTH") or not environ.get("wsgi.input_terminated"):
            return self.application(environ, start_response)
        # Gunicorn marks decoded HTTP bodies as terminated. Django otherwise
        # assumes an absent Content-Length means an empty body. Spool in chunks
        # to disk, never collect the whole multipart request in memory.
        stream = SpooledTemporaryFile(max_size=256 * 1024)
        try:
            length = 0
            while chunk := environ["wsgi.input"].read(65536):
                length += len(chunk)
                if length > self.max_bytes:
                    stream.close()
                    body = b'{"error":"Request too large"}'
                    start_response(
                        "413 Payload Too Large",
                        [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
                    )
                    return [body]
                stream.write(chunk)
            stream.seek(0)
            environ["wsgi.input"] = stream
            environ["CONTENT_LENGTH"] = str(length)
            response = self.application(environ, start_response)
            return BufferedResponse(response, stream)
        except Exception:
            stream.close()
            raise

import mimetypes
import re
import time
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.utils.http import http_date, parse_http_date_safe

from posts.exceptions import PostError


def save_files(files):
    root = Path(settings.UPLOAD_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    owned = []
    try:
        for upload in files:
            name = re.sub(r"[\x00-\x1f\x7f]", "", upload.name.replace("\\", "/").split("/")[-1])
            name = name or "upload"
            tick = int(time.time() * 1000)
            while True:
                target = root / f"{tick}-{name}"
                if len("/uploads/" + target.name) > 255:
                    raise PostError("Invalid upload filename")
                try:
                    stream = target.open("xb")
                    break
                except FileExistsError:
                    tick += 1
            owned.append(target)
            with stream:
                for chunk in upload.chunks():
                    stream.write(chunk)
        return owned
    except Exception:
        cleanup(owned)
        raise


def cleanup(owned):
    for target in owned:
        target.unlink(missing_ok=True)


class FileSlice:
    def __init__(self, path, start, length):
        self.stream = path.open("rb")
        self.stream.seek(start)
        self.remaining = length

    def __iter__(self):
        while self.remaining:
            chunk = self.stream.read(min(self.remaining, 65536))
            if not chunk:
                break
            self.remaining -= len(chunk)
            yield chunk

    def close(self):
        self.stream.close()


def serve(request, filename):
    root = Path(settings.UPLOAD_ROOT).resolve()
    target = (root / filename).resolve()
    if (
        request.method not in {"GET", "HEAD"}
        or not target.is_relative_to(root)
        or any(part.startswith(".") for part in Path(filename).parts)
        or not target.is_file()
    ):
        return HttpResponse(status=404)
    stat = target.stat()
    size = stat.st_size
    etag = f'W/"{size:x}-{int(stat.st_mtime * 1000):x}"'
    modified = parse_http_date_safe(request.headers.get("If-Modified-Since", ""))
    if request.headers.get("If-None-Match") == etag or (
        "If-None-Match" not in request.headers
        and modified is not None
        and int(stat.st_mtime) <= modified
    ):
        response = HttpResponse(status=304)
    else:
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        range_value = request.headers.get("Range", "")
        if_range = request.headers.get("If-Range")
        if if_range and if_range not in {etag, http_date(stat.st_mtime)}:
            range_value = ""
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_value)
        if match and (match[1] or match[2]):
            start = int(match[1]) if match[1] else max(0, size - int(match[2]))
            end = min(size - 1, int(match[2])) if match[1] and match[2] else size - 1
            if start > end or start >= size:
                response = HttpResponse(status=416)
                response["Content-Range"] = f"bytes */{size}"
                return response
            response = (
                HttpResponse(content_type=content_type, status=206)
                if request.method == "HEAD"
                else StreamingHttpResponse(
                    FileSlice(target, start, end - start + 1), content_type=content_type, status=206
                )
            )
            response["Content-Length"] = str(end - start + 1)
            response["Content-Range"] = f"bytes {start}-{end}/{size}"
        else:
            response = (
                HttpResponse(content_type=content_type)
                if request.method == "HEAD"
                else FileResponse(target.open("rb"), content_type=content_type)
            )
            response["Content-Length"] = str(size)
        response["Accept-Ranges"] = "bytes"
        if "Content-Disposition" in response:
            del response["Content-Disposition"]
    response["ETag"] = etag
    response["Last-Modified"] = http_date(stat.st_mtime)
    response["Cache-Control"] = "public, max-age=0"
    return response

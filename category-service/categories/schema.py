def canonical_paths(endpoints):
    return [
        (path.rstrip("/") or "/", regex, method, callback)
        for path, regex, method, callback in endpoints
    ]

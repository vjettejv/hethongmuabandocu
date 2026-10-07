def canonical_paths(endpoints):
    # Optional slash regexes must document the supported legacy no-slash spelling.
    return [
        (path.rstrip("/") or "/", regex, method, callback)
        for path, regex, method, callback in endpoints
    ]

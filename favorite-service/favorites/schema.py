from drf_spectacular.openapi import AutoSchema


class LegacySchema(AutoSchema):
    def get_auth(self):
        return (
            [{"legacyBearer": []}]
            if type(self.view).__name__ in {"ToggleView", "CheckView", "FavoritesView"}
            else []
        )


def canonical_paths(endpoints):
    return [
        (path.rstrip("/") or "/", regex, method, callback)
        for path, regex, method, callback in endpoints
    ]

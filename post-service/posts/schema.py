from drf_spectacular.openapi import AutoSchema


class LegacySchema(AutoSchema):
    def get_auth(self):
        name = type(self.view).__name__
        protected = (
            name in {"MyPostsView", "AdminPostsView", "AdminDetailView"}
            or (name == "PostsView" and self.method == "POST")
            or (name == "DetailView" and self.method == "DELETE")
        )
        return [{"legacyBearer": []}] if protected else []


def canonical_paths(endpoints):
    return [
        (path.rstrip("/") or "/", regex, method, callback)
        for path, regex, method, callback in endpoints
    ]

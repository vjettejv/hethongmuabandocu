import re
from urllib.parse import unquote

from .models import SearchIndex


def legacy_parameters(request):
    # Express qs preserves a parameter verbatim when decodeURIComponent fails.
    # Django replaces invalid UTF-8, which changes SQL LIKE wildcard searches.
    def decode(value):
        if re.search(r"%(?![0-9a-fA-F]{2})", value):
            return value
        try:
            return unquote(value.replace("+", " "), encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            return value

    parameters = request.query_params.dict()
    for pair in request.META.get("QUERY_STRING", "").split("&"):
        key, _, value = pair.partition("=")
        key = decode(key)
        if key in {"query", "categoryId", "minPrice", "maxPrice"}:
            parameters[key] = decode(value)
    return parameters


def search(parameters):
    query = SearchIndex.objects.filter(status="approved")
    if parameters.get("query"):
        like = "%" + parameters["query"] + "%"
        query = query.extra(
            where=["(`title` LIKE %s OR `description` LIKE %s)"], params=[like, like]
        )
    if parameters.get("categoryId"):
        query = query.extra(where=["`categoryId` = %s"], params=[parameters["categoryId"]])
    for key, operator in (("minPrice", ">="), ("maxPrice", "<=")):
        if parameters.get(key):
            query = query.extra(where=[f"`price` {operator} %s"], params=[parameters[key]])
    return query.order_by("-createdAt")

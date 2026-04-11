from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    if isinstance(exc, serializers.ValidationError):
        response.data = {"error": _flatten_validation(response.data)}
    return response


def _flatten_validation(data):
    """Collapse a DRF ValidationError payload into a single string.

    Accepts the three shapes DRF produces:
      - list of strings:           ["msg", ...]
      - dict of lists:             {"field": ["msg", ...]}
      - nested dicts / mixed:      {"field": {"sub": ["msg"]}} or with lists of dicts
    Non-field errors (key "non_field_errors") are emitted without the prefix.
    """
    parts = list(_walk(data, prefix=""))
    return "; ".join(parts) if parts else "Invalid input"


def _walk(node, prefix):
    if isinstance(node, dict):
        for key, value in node.items():
            sub_prefix = "" if key == "non_field_errors" else (
                f"{prefix}.{key}" if prefix else str(key)
            )
            yield from _walk(value, sub_prefix)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item, prefix)
    else:
        msg = str(node)
        yield f"{prefix}: {msg}" if prefix else msg

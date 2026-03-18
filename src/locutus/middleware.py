import logging
import uuid

from flask import g, request


def set_request_id():
    # 1. Handle GCP specifically (due to the / delimiter)
    gcp_trace = request.headers.get("X-Cloud-Trace-Context")
    if gcp_trace:
        # Split by / to extract just the 32-char hex Trace ID
        g.request_id = gcp_trace.split("/")[0]
        return

    # 2. Handle others (AWS, X-Request-Id, etc.) as whole strings
    # These use hyphens/semicolons which are fine to keep as-is
    request_id = (
        request.headers.get("X-Amzn-Trace-Id")
        or request.headers.get("X-Request-Id")
        or str(uuid.uuid4())
    )
    g.request_id = request_id


def add_request_id_header(response):
    # Helpful for debugging: return the ID to the client in headers
    response.headers["X-Request-Id"] = g.request_id
    return response

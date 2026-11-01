"""Small injectable HTTP transport; responses redact authorization headers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Response:
    status: int
    body: dict
    headers: dict[str, str]


class HttpTransport:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict | None = None,
        form: dict[str, str] | None = None,
        raw: bytes | None = None,
    ) -> Response:
        body = raw
        request_headers = dict(headers or {})
        if json_body is not None:
            body = json.dumps(json_body).encode()
            request_headers["Content-Type"] = "application/json"
        elif form is not None:
            body = urlencode(form).encode()
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = Request(url, data=body, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                raw_body = response.read()
                parsed = json.loads(raw_body) if raw_body else {}
                return Response(response.status, parsed, dict(response.headers.items()))
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:1000]
            raise ValueError(f"provider request failed ({exc.code}): {detail}") from None

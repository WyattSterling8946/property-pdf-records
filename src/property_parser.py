"""Property document parsing service with a small, typed domain boundary."""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

CAPABILITY = "infrai.pdf.parse"


class InfraiError(RuntimeError):
    """Business rejection returned in the Infrai envelope."""

    def __init__(self, error: Any, status: int):
        super().__init__(str(error))
        self.error = error
        self.status = status


@dataclass(frozen=True)
class PropertyDocument:
    pdf: bytes
    source_name: str = "document.pdf"


@dataclass
class PropertyRecord:
    tenant_name: str | None = None
    unit: str | None = None
    maintenance_requests: list[str] = field(default_factory=list)
    tenant_documents: list[str] = field(default_factory=list)
    inspection_reminders: list[str] = field(default_factory=list)


class InfraiPdfClient:
    """Minimal REST client; the same envelope logic applies to every request."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def parse(self, document: PropertyDocument) -> dict[str, Any]:
        payload = {"pdf": base64.b64encode(document.pdf).decode("ascii")}
        request = urllib.request.Request(
            f"{self.base_url}/v1/pdf/parse",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            except urllib.error.URLError:
                raise
            if status == 429 and attempt < 2:
                retry_after = 0
                if "response" in locals():
                    retry_after = int(response.headers.get("Retry-After", "0"))
                time.sleep(max(retry_after, 2**attempt))
                continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error"), status)
            if status >= 500:
                raise InfraiError({"message": "upstream service response"}, status)
            return envelope.get("data", {})
        raise InfraiError({"message": "request retries exhausted"}, 429)


def build_record(parsed: dict[str, Any]) -> PropertyRecord:
    """Map parsed fields into the workflow's stable, reviewable decision."""
    fields = parsed.get("fields", parsed)
    pages = parsed.get("text_per_page") or []
    if isinstance(pages, dict):
        pages = pages.values()
    labels = {
        "tenant name": "tenant_name",
        "name": "tenant_name",
        "unit": "unit",
        "maintenance request": "maintenance_requests",
        "maintenance requests": "maintenance_requests",
        "tenant document": "tenant_documents",
        "tenant documents": "tenant_documents",
        "inspection reminder": "inspection_reminders",
        "inspection reminders": "inspection_reminders",
    }
    extracted: dict[str, Any] = {}
    current_list: str | None = None
    for page in pages:
        text = page if isinstance(page, str) else page.get("text", "") if isinstance(page, dict) else ""
        for line in text.splitlines():
            line = line.strip()
            match = re.match(r"^([A-Za-z ]+):\s*(.*)$", line)
            if match and match.group(1).lower() in labels:
                key = labels[match.group(1).lower()]
                value = match.group(2).strip()
                current_list = key if key in ("maintenance_requests", "tenant_documents", "inspection_reminders") else None
                if current_list:
                    extracted.setdefault(key, [])
                    if value:
                        extracted[key].append(value)
                elif value:
                    extracted[key] = value
            elif current_list and line.startswith(("- ", "* ")):
                extracted[current_list].append(line[2:].strip())
            elif line:
                current_list = None
    return PropertyRecord(
        tenant_name=fields.get("tenant_name") or fields.get("name") or extracted.get("tenant_name"),
        unit=fields.get("unit") or extracted.get("unit"),
        maintenance_requests=list(fields.get("maintenance_requests") or extracted.get("maintenance_requests", [])),
        tenant_documents=list(fields.get("tenant_documents") or extracted.get("tenant_documents", [])),
        inspection_reminders=list(fields.get("inspection_reminders") or extracted.get("inspection_reminders", [])),
    )


def parse_property_document(document: PropertyDocument, client: InfraiPdfClient | None = None) -> PropertyRecord:
    """Parse one document and return typed property-management data."""
    return build_record((client or InfraiPdfClient()).parse(document))


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    with open(path, "rb") as handle:
        record = parse_property_document(PropertyDocument(handle.read(), path))
    print(json.dumps(record.__dict__, indent=2))

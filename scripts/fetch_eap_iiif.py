#!/usr/bin/env python3
"""Fetch and preserve British Library EAP IIIF manifests/images.

Purpose
-------
Pramāṇa uses this tool for historical-witness acquisition. It does not OCR,
transcribe, normalize, adjudicate, or set verification authority.

The tool:
* fetches a IIIF Presentation v2/v3 manifest;
* fail-closes against optional expected manifest SHA / canvas count;
* saves manifest bytes + provenance sidecars;
* lists deterministic canvases;
* optionally downloads selected image canvases;
* hashes every downloaded image;
* writes a local image index suitable for later human manuscript review.

Raw EAP images are research/verification material. Do not publish or redistribute
them merely because they were fetched successfully; obey source/custodian terms.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


USER_AGENT = (
    "pramana-bhakthi-corpus/0.3 "
    "historical-witness provenance-preserving research fetch"
)


@dataclass(frozen=True)
class CanvasRef:
    index: int
    canvas_id: str
    label: str
    image_id: str | None
    service_id: str | None
    service_type: str | None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def fetch_bytes(url: str, timeout: int = 60) -> tuple[bytes, str, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return (
            response.read(),
            response.geturl(),
            response.headers.get("Content-Type"),
        )


def normalize_label(value: Any) -> str:
    """Return a stable human-readable label for IIIF v2/v3 label shapes."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Presentation 3 language map, e.g. {"en": ["Page 1"]}
        for preferred in ("en", "none"):
            items = value.get(preferred)
            if isinstance(items, list) and items:
                return str(items[0])
        for items in value.values():
            if isinstance(items, list) and items:
                return str(items[0])
            if isinstance(items, str):
                return items
    return str(value)


def _first_service(value: Any) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    service = value[0] if isinstance(value, list) else value
    if not isinstance(service, dict):
        return None, None
    service_id = service.get("id") or service.get("@id")
    service_type = service.get("type") or service.get("@type")
    return service_id, service_type


def parse_v2_canvases(manifest: dict[str, Any]) -> list[CanvasRef]:
    sequences = manifest.get("sequences") or []
    if not sequences:
        return []
    raw_canvases = sequences[0].get("canvases") or []
    out: list[CanvasRef] = []

    for index, canvas in enumerate(raw_canvases, start=1):
        annotations = canvas.get("images") or []
        resource: dict[str, Any] = {}
        if annotations:
            resource = annotations[0].get("resource") or {}

        image_id = resource.get("@id") or resource.get("id")
        service_id, service_type = _first_service(resource.get("service"))

        out.append(
            CanvasRef(
                index=index,
                canvas_id=canvas.get("@id") or canvas.get("id") or "",
                label=normalize_label(canvas.get("label")),
                image_id=image_id,
                service_id=service_id,
                service_type=service_type,
            )
        )
    return out


def parse_v3_canvases(manifest: dict[str, Any]) -> list[CanvasRef]:
    raw_canvases = manifest.get("items") or []
    out: list[CanvasRef] = []

    for index, canvas in enumerate(raw_canvases, start=1):
        body: dict[str, Any] = {}
        pages = canvas.get("items") or []
        if pages:
            annotations = pages[0].get("items") or []
            if annotations:
                raw_body = annotations[0].get("body") or {}
                if isinstance(raw_body, list):
                    body = raw_body[0] if raw_body else {}
                elif isinstance(raw_body, dict):
                    body = raw_body

        image_id = body.get("id") or body.get("@id")
        service_id, service_type = _first_service(body.get("service"))

        out.append(
            CanvasRef(
                index=index,
                canvas_id=canvas.get("id") or canvas.get("@id") or "",
                label=normalize_label(canvas.get("label")),
                image_id=image_id,
                service_id=service_id,
                service_type=service_type,
            )
        )
    return out


def parse_canvases(manifest: dict[str, Any]) -> list[CanvasRef]:
    context = manifest.get("@context")
    manifest_type = str(manifest.get("type") or manifest.get("@type") or "")

    if "Presentation 3" in str(context) or manifest_type == "Manifest":
        canvases = parse_v3_canvases(manifest)
        if canvases:
            return canvases

    canvases = parse_v2_canvases(manifest)
    if canvases:
        return canvases

    # A few servers omit obvious version signals. Try v3 last.
    return parse_v3_canvases(manifest)


def image_url_candidates(canvas: CanvasRef) -> list[str]:
    """Generate preferred download URLs without guessing text content."""
    urls: list[str] = []
    if canvas.service_id:
        base = canvas.service_id.rstrip("/")
        service_type = (canvas.service_type or "").lower()

        # IIIF Image API 3 commonly uses max; Image API 2 commonly accepts full.
        if "imageService3".lower() in service_type or "imageservice3" in service_type:
            urls.append(f"{base}/full/max/0/default.jpg")
            urls.append(f"{base}/full/full/0/default.jpg")
        else:
            urls.append(f"{base}/full/full/0/default.jpg")
            urls.append(f"{base}/full/max/0/default.jpg")

    if canvas.image_id:
        urls.append(canvas.image_id)

    # Stable de-duplication.
    seen: set[str] = set()
    return [u for u in urls if u and not (u in seen or seen.add(u))]


def parse_selection(spec: str | None, upper: int) -> list[int]:
    """Parse 1-based selections such as '1,4,7-10'. Empty means all."""
    if not spec:
        return list(range(1, upper + 1))

    selected: set[int] = set()
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            left, right = token.split("-", 1)
            start, end = int(left), int(right)
            if end < start:
                raise ValueError(f"descending range is not allowed: {token}")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(token))

    bad = sorted(i for i in selected if i < 1 or i > upper)
    if bad:
        raise ValueError(f"canvas indices out of range 1..{upper}: {bad}")
    return sorted(selected)


def enforce_manifest_contract(
    *,
    manifest_bytes: bytes,
    canvas_count: int,
    expected_sha256: str | None,
    expected_canvas_count: int | None,
) -> str:
    actual_sha = sha256_bytes(manifest_bytes)

    if expected_sha256 and actual_sha != expected_sha256:
        raise ValueError(
            "manifest hash mismatch: "
            f"expected {expected_sha256}, got {actual_sha}"
        )

    if expected_canvas_count is not None and canvas_count != expected_canvas_count:
        raise ValueError(
            "manifest canvas-count mismatch: "
            f"expected {expected_canvas_count}, got {canvas_count}"
        )

    return actual_sha


def fetch_image_with_fallback(
    canvas: CanvasRef, timeout: int
) -> tuple[bytes, str, str | None]:
    errors: list[str] = []
    for candidate in image_url_candidates(canvas):
        try:
            return fetch_bytes(candidate, timeout=timeout)
        except Exception as exc:  # retain all attempts for provenance/debugging
            errors.append(f"{candidate}: {exc}")
    raise RuntimeError(
        f"unable to fetch canvas {canvas.index}; attempts: " + " | ".join(errors)
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-key", required=True)
    ap.add_argument("--manifest-url", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--expected-manifest-sha256")
    ap.add_argument("--expected-canvas-count", type=int)
    ap.add_argument(
        "--canvases",
        help="1-based canvas selection, e.g. 1,5,10-20; default=all",
    )
    ap.add_argument("--manifest-only", action="store_true")
    ap.add_argument("--list", action="store_true", dest="list_only")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "manifest.json"
    manifest_sha_path = out_dir / "manifest.json.sha256"
    manifest_meta_path = out_dir / "manifest.meta.json"

    if manifest_path.exists() and not args.force:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        final_manifest_url = args.manifest_url
        content_type = "application/json (existing local snapshot)"
    else:
        raw, final_manifest_url, content_type = fetch_bytes(
            args.manifest_url, timeout=args.timeout
        )
        # Parse before writing. Malformed remote JSON never becomes a snapshot.
        manifest = json.loads(raw.decode("utf-8"))
        manifest_bytes = json_bytes(manifest)

    canvases = parse_canvases(manifest)
    if not canvases:
        raise SystemExit("manifest contains no parseable canvases")

    manifest_sha = enforce_manifest_contract(
        manifest_bytes=manifest_bytes,
        canvas_count=len(canvases),
        expected_sha256=args.expected_manifest_sha256,
        expected_canvas_count=args.expected_canvas_count,
    )

    if manifest_path.exists() and not args.force:
        if not manifest_sha_path.exists() or manifest_sha_path.read_text().strip() != manifest_sha:
            raise ValueError("existing manifest snapshot has missing/bad SHA sidecar")
    else:
        manifest_path.write_bytes(manifest_bytes)
        manifest_sha_path.write_text(manifest_sha + "\n", encoding="utf-8")
        manifest_meta_path.write_text(
            json.dumps(
                {
                    "source_key": args.source_key,
                    "manifest_url": args.manifest_url,
                    "final_manifest_url": final_manifest_url,
                    "content_type": content_type,
                    "sha256": manifest_sha,
                    "bytes": len(manifest_bytes),
                    "canvas_count": len(canvases),
                    "fetched_or_checked_at_utc": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "authority": "historical_witness_snapshot_only",
                    "verification_effect": "none",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    print(
        "MANIFEST",
        args.source_key,
        len(canvases),
        "canvases",
        len(manifest_bytes),
        "bytes",
        manifest_sha,
    )

    if args.list_only:
        for canvas in canvases:
            print(
                f"{canvas.index:04d}",
                repr(canvas.label),
                canvas.canvas_id,
                image_url_candidates(canvas)[:1],
            )

    if args.manifest_only or args.list_only:
        return

    selected = parse_selection(args.canvases, len(canvases))
    image_dir = out_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    existing_index_path = out_dir / "image_index.json"
    existing_entries: dict[int, dict[str, Any]] = {}
    if existing_index_path.exists() and not args.force:
        raw_index = json.loads(existing_index_path.read_text(encoding="utf-8"))
        existing_entries = {
            int(row["canvas_index"]): row for row in raw_index.get("images", [])
        }

    entries: dict[int, dict[str, Any]] = dict(existing_entries)

    for index in selected:
        canvas = canvases[index - 1]
        image_path = image_dir / f"{index:04d}.jpg"

        if image_path.exists() and not args.force:
            data = image_path.read_bytes()
            actual_sha = sha256_bytes(data)
            existing = entries.get(index)
            if not existing or existing.get("sha256") != actual_sha:
                raise ValueError(
                    f"unprovenanced or changed existing image: {image_path}"
                )
            print("SKIP_IMAGE", index, len(data), actual_sha)
            continue

        data, final_url, image_content_type = fetch_image_with_fallback(
            canvas, timeout=args.timeout
        )
        image_sha = sha256_bytes(data)
        image_path.write_bytes(data)

        entries[index] = {
            "canvas_index": index,
            "canvas_id": canvas.canvas_id,
            "label": canvas.label,
            "declared_image_id": canvas.image_id,
            "declared_service_id": canvas.service_id,
            "final_url": final_url,
            "path": str(image_path),
            "sha256": image_sha,
            "bytes": len(data),
            "content_type": image_content_type,
        }
        print("FETCHED_IMAGE", index, len(data), image_sha)

    existing_index_path.write_text(
        json.dumps(
            {
                "source_key": args.source_key,
                "manifest_url": args.manifest_url,
                "manifest_sha256": manifest_sha,
                "canvas_count": len(canvases),
                "images": [entries[k] for k in sorted(entries)],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

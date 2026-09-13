import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "fetch_eap_iiif.py"
SPEC = importlib.util.spec_from_file_location("fetch_eap_iiif", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
import sys
sys.modules["fetch_eap_iiif"] = MOD
SPEC.loader.exec_module(MOD)


def test_parse_v2_manifest():
    manifest = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "sequences": [
            {
                "canvases": [
                    {
                        "@id": "https://example/canvas/1",
                        "label": "Image 1",
                        "images": [
                            {
                                "resource": {
                                    "@id": "https://example/image/1/full/full/0/default.jpg",
                                    "service": {
                                        "@id": "https://example/image/1",
                                        "profile": "http://iiif.io/api/image/2/level2.json",
                                    },
                                }
                            }
                        ],
                    }
                ]
            }
        ],
    }
    rows = MOD.parse_canvases(manifest)
    assert len(rows) == 1
    assert rows[0].index == 1
    assert rows[0].label == "Image 1"
    assert rows[0].service_id == "https://example/image/1"
    assert MOD.image_url_candidates(rows[0])[0].endswith(
        "/full/full/0/default.jpg"
    )


def test_parse_v3_manifest():
    manifest = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "type": "Manifest",
        "items": [
            {
                "id": "https://example/canvas/1",
                "type": "Canvas",
                "label": {"en": ["Leaf 1"]},
                "items": [
                    {
                        "type": "AnnotationPage",
                        "items": [
                            {
                                "type": "Annotation",
                                "body": {
                                    "id": "https://example/image/1/full/max/0/default.jpg",
                                    "type": "Image",
                                    "service": [
                                        {
                                            "id": "https://example/image/1",
                                            "type": "ImageService3",
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }
    rows = MOD.parse_canvases(manifest)
    assert len(rows) == 1
    assert rows[0].label == "Leaf 1"
    assert rows[0].service_id == "https://example/image/1"
    assert MOD.image_url_candidates(rows[0])[0].endswith(
        "/full/max/0/default.jpg"
    )


def test_parse_selection():
    assert MOD.parse_selection(None, 4) == [1, 2, 3, 4]
    assert MOD.parse_selection("1,3-5,7", 8) == [1, 3, 4, 5, 7]


def test_manifest_contract_hash_and_count():
    payload = b'{"x": 1}\n'
    sha = MOD.sha256_bytes(payload)
    assert (
        MOD.enforce_manifest_contract(
            manifest_bytes=payload,
            canvas_count=202,
            expected_sha256=sha,
            expected_canvas_count=202,
        )
        == sha
    )


def test_manifest_contract_rejects_wrong_count():
    payload = b'{"x": 1}\n'
    try:
        MOD.enforce_manifest_contract(
            manifest_bytes=payload,
            canvas_count=201,
            expected_sha256=None,
            expected_canvas_count=202,
        )
    except ValueError as exc:
        assert "canvas-count mismatch" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_parse_v2_manifest()
    test_parse_v3_manifest()
    test_parse_selection()
    test_manifest_contract_hash_and_count()
    test_manifest_contract_rejects_wrong_count()
    print("test_fetch_eap_iiif: GREEN")

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "schema/review_policy.json"


def read_jsonl(path):
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def required(row, gate):
    if row["machine_classification"] == "source_anomaly":
        return True

    metric = gate.get("metric", "machine_classification")

    if metric == "strict_similarity":
        return row["similarity"] < float(gate["threshold"])

    if metric == "projected_similarity":
        return (
            row["ranking_projected_similarity"]
            < float(gate["threshold"])
        )

    if metric == "machine_classification":
        return (
            row["machine_classification"]
            == "textual_review_required"
        )

    raise ValueError(f"unknown review metric: {metric}")


def risk(row):
    return (
        row.get("ranking_projected_replacement_blocks", 0),
        row.get("ranking_projected_max_edit_span", 0),
        row.get("ranking_projected_edit_burden", 0),
        1 - row.get(
            "ranking_projected_similarity",
            row["similarity"]
        ),
    )


def clean(value):
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def build_packet(work, cfg, rows, mandatory, spot):
    out = ROOT / cfg["outputs"]["review_markdown"]
    out.parent.mkdir(parents=True, exist_ok=True)

    gate = cfg["manual_review_gate"]

    lines = [
        f"# {work} — Witness Review Packet",
        "",
        "> **Authority: UNVERIFIED.** "
        "This is a comparison and curation-triage artifact only.",
        "",
        "## Summary",
        "",
        f"- Total units: **{len(rows)}**",
        f"- Mandatory human review: **{len(mandatory)}**",
        f"- QA spot-checks: **{len(spot)}**",
        f"- Machine-triaged outside spot-check: "
        f"**{len(rows)-len(mandatory)-len(spot)}**",
        f"- Gate: `{json.dumps(gate, ensure_ascii=False)}`",
        f"- Witness independence: "
        f"**{cfg['witness'].get('independence', 'unproven')}**",
        "",
        "## Mandatory review queue",
        "",
    ]

    for r in mandatory:
        source_no = r.get("comparison_source_unit_no")
        suffix = (
            f" / witness source {source_no}"
            if source_no is not None else ""
        )

        lines += [
            f"### Unit {r['unit_no']}{suffix}",
            "",
            f"- Strict similarity: `{r['similarity']}`",
            f"- Projected similarity: "
            f"`{r['ranking_projected_similarity']}`",
            f"- Projected replacements: "
            f"`{r['ranking_projected_replacement_blocks']}`",
            f"- Projected max span: "
            f"`{r['ranking_projected_max_edit_span']}`",
            f"- Machine class: "
            f"`{r['machine_classification']}`",
            "",
            "**Project Madurai**",
            "",
            clean(r["primary_text"]),
            "",
            "**Wikisource witness**",
            "",
            clean(r["comparison_text"]),
            "",
        ]

        edits = r.get("edit_preview", [])
        if edits:
            lines += ["**Edit preview**", ""]
            for e in edits:
                lines.append(
                    f"- `{e['tag']}` "
                    f"`{clean(e['primary'])}` → "
                    f"`{clean(e['secondary'])}`"
                )
            lines.append("")

    lines += [
        "## QA spot-check queue",
        "",
        "These are machine-triaged rows selected only for curator QA.",
        "",
    ]

    for r in spot:
        source_no = r.get("comparison_source_unit_no")
        suffix = (
            f" / witness source {source_no}"
            if source_no is not None else ""
        )

        lines += [
            f"### Unit {r['unit_no']}{suffix}",
            "",
            f"- Strict similarity: `{r['similarity']}`",
            f"- Projected similarity: "
            f"`{r['ranking_projected_similarity']}`",
            "",
            "**Project Madurai**",
            "",
            clean(r["primary_text"]),
            "",
            "**Wikisource witness**",
            "",
            clean(r["comparison_text"]),
            "",
        ]

    out.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8"
    )

    return out


def finalize(work):
    policy = json.loads(
        POLICY.read_text(encoding="utf-8")
    )
    cfg = policy["works"][work]

    review_path = ROOT / cfg["outputs"]["review_jsonl"]
    summary_path = ROOT / cfg["outputs"]["summary_json"]

    rows = read_jsonl(review_path)
    gate = cfg["manual_review_gate"]

    start_number = (
        cfg["witness"]
        .get("extractor_options", {})
        .get("start_number")
    )

    for r in rows:
        r["manual_review_required"] = required(r, gate)
        r["review_tier"] = (
            "mandatory"
            if r["manual_review_required"]
            else "machine_triaged"
        )

        if (
            start_number is not None
            and r.get("comparison_source_unit_no") is None
        ):
            r["comparison_source_unit_no"] = (
                start_number + r["unit_no"] - 1
            )

        r["flags"] = [
            f for f in r.get("flags", [])
            if f != "spot_check_candidate"
        ]

    mandatory = [
        r for r in rows
        if r["manual_review_required"]
    ]

    triaged = [
        r for r in rows
        if not r["manual_review_required"]
    ]

    sampling = cfg.get("review_sampling", {})
    spot_n = max(
        int(sampling.get("spot_check_minimum", 3)),
        math.ceil(
            len(rows)
            * float(sampling.get("spot_check_fraction", 0.05))
        )
    )

    spot = sorted(
        triaged,
        key=risk,
        reverse=True
    )[:spot_n]

    spot_units = {r["unit_no"] for r in spot}

    for r in rows:
        if r["unit_no"] in spot_units:
            r["flags"].append("spot_check_candidate")

    ranked = sorted(
        rows,
        key=lambda r: (
            r["manual_review_required"],
            r["machine_classification"] == "source_anomaly",
            *risk(r),
        ),
        reverse=True
    )

    for i, r in enumerate(ranked, 1):
        r["manual_review_priority"] = i

    review_path.write_text(
        "".join(
            json.dumps(r, ensure_ascii=False) + "\n"
            for r in rows
        ),
        encoding="utf-8"
    )

    summary = (
        json.loads(summary_path.read_text(encoding="utf-8"))
        if summary_path.exists()
        else {}
    )

    summary.update({
        "manual_review_gate": gate,
        "mandatory_manual_review": len(mandatory),
        "mandatory_units": [
            r["unit_no"]
            for r in sorted(
                mandatory,
                key=lambda x: x["manual_review_priority"]
            )
        ],
        "spot_check_count": len(spot),
        "spot_check_units": [
            r["unit_no"] for r in spot
        ],
        "machine_triaged_without_spot_check":
            len(rows) - len(mandatory) - len(spot),
        "authority":
            "UNVERIFIED comparison/triage only. "
            "Triage does not grant verification authority."
    })

    summary_path.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    packet = build_packet(
        work,
        cfg,
        rows,
        sorted(
            mandatory,
            key=lambda x: x["manual_review_priority"]
        ),
        spot
    )

    print("\n=== FINAL REVIEW TRIAGE ===")
    print("work:", work)
    print("total:", len(rows))
    print("mandatory:", len(mandatory))
    print(
        "QA spot-check:",
        len(spot),
        [r["unit_no"] for r in spot]
    )
    print(
        "machine-triaged:",
        len(rows) - len(mandatory) - len(spot)
    )
    print("packet:", packet.relative_to(ROOT))
    print("authority: UNVERIFIED")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    args = ap.parse_args()
    finalize(args.work)


if __name__ == "__main__":
    main()

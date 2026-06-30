"""Export utilities: CSV, JSON, and HTML report generation for AbAnnotator results."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from html import escape

from .models import AnnotatedAntibody


def _cdr_length(result: AnnotatedAntibody, name: str) -> int:
    cdr = next((item for item in result.domain.cdrs if item.name == name), None)
    return cdr.length if cdr else 0


def _cdr_sequence(result: AnnotatedAntibody, name: str) -> str:
    cdr = next((item for item in result.domain.cdrs if item.name == name), None)
    return cdr.sequence if cdr else ""


def results_to_json(results: list[AnnotatedAntibody]) -> str:
    """Generate structured JSON export of annotation results."""
    output = []
    for r in results:
        sev = {"high": 0, "medium": 0, "low": 0}
        for f in r.liabilities:
            sev[f.severity] += 1
        output.append(
            {
                "name": r.input.name,
                "chain_type": r.domain.chain_type,
                "domain": r.domain.name,
                "sequence_length": len(r.domain.sequence),
                "scheme": r.domain.scheme,
                "germline": {
                    "v_gene": r.germline.v_gene,
                    "j_gene": r.germline.j_gene,
                    "identity": r.germline.identity,
                    "method": r.germline.method,
                },
                "regions": [
                    {
                        "name": region.name,
                        "start": region.start,
                        "end": region.end,
                        "length": region.length,
                        "sequence": region.sequence,
                    }
                    for region in sorted(
                        list(r.domain.cdrs) + list(r.domain.frameworks),
                        key=lambda x: x.start,
                    )
                ],
                "liabilities": [
                    {
                        "type": f.type,
                        "severity": f.severity,
                        "position": f.position,
                        "region": f.region,
                        "motif": f.motif,
                        "description": f.description,
                        "recommendation": f.recommendation,
                    }
                    for f in r.liabilities
                ],
                "risk_summary": {
                    "high": sev["high"],
                    "medium": sev["medium"],
                    "low": sev["low"],
                    "score": sev["high"] * 3 + sev["medium"] * 2 + sev["low"],
                },
            }
        )
    return json.dumps(output, indent=2)


def results_to_csv(results: list[AnnotatedAntibody]) -> str:
    """Generate CSV export of annotation results."""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "name",
            "chain_type",
            "domain",
            "germline_v",
            "germline_j",
            "germline_identity",
            "region",
            "start",
            "end",
            "sequence",
            "liability_count",
            "liabilities",
        ],
    )
    writer.writeheader()
    for result in results:
        liability_summary = "; ".join(
            f"{flag.severity}:{flag.type}@{flag.position}:{flag.motif}" for flag in result.liabilities
        )
        for cdr in result.domain.cdrs:
            writer.writerow(
                {
                    "name": result.input.name,
                    "chain_type": result.domain.chain_type,
                    "domain": result.domain.name,
                    "germline_v": result.germline.v_gene,
                    "germline_j": result.germline.j_gene,
                    "germline_identity": result.germline.identity,
                    "region": cdr.name,
                    "start": cdr.start,
                    "end": cdr.end,
                    "sequence": cdr.sequence,
                    "liability_count": len(result.liabilities),
                    "liabilities": liability_summary,
                }
            )
    return buffer.getvalue()


def generate_html_report(results: list[AnnotatedAntibody]) -> str:
    """Generate a self-contained HTML report for download."""
    rows_html = ""
    for i, r in enumerate(results, 1):
        sev = {"high": 0, "medium": 0, "low": 0}
        for f in r.liabilities:
            sev[f.severity] += 1
        risk = sev["high"] * 3 + sev["medium"] * 2 + sev["low"]

        cdr_rows = ""
        for cdr in r.domain.cdrs:
            cdr_rows += (
                f"<tr><td>{escape(cdr.name)}</td><td>{cdr.start}</td>"
                f"<td>{cdr.end}</td><td>{cdr.length}</td>"
                f"<td style='font-family:monospace'>{escape(cdr.sequence)}</td></tr>"
            )

        liab_rows = ""
        for flag in r.liabilities:
            sev_color = {"high": "#fee2e2", "medium": "#fef3c7", "low": "#dcfce7"}[flag.severity]
            liab_rows += (
                f"<tr><td style='background:{sev_color};font-weight:700'>{flag.severity.upper()}</td>"
                f"<td>{escape(flag.type)}</td><td>{flag.position}</td>"
                f"<td>{escape(flag.region)}</td><td style='font-family:monospace'>{escape(flag.motif)}</td>"
                f"<td>{escape(flag.recommendation)}</td></tr>"
            )
        if not liab_rows:
            liab_rows = "<tr><td colspan='6' style='color:#166534;text-align:center'>No liabilities detected</td></tr>"

        rows_html += f"""
        <div class="seq-block">
          <h2>#{i} {escape(r.input.name)}</h2>
          <div class="meta">{r.domain.name} | {r.domain.chain_type.title()} chain |
            {len(r.domain.sequence)} residues | Germline: {escape(r.germline.v_gene)}
            ({r.germline.identity}% identity) | Risk score: {risk}</div>
          <h3>CDR Regions</h3>
          <table><thead><tr><th>Region</th><th>Start</th><th>End</th><th>Length</th><th>Sequence</th></tr></thead>
          <tbody>{cdr_rows}</tbody></table>
          <h3>Liability Flags</h3>
          <table><thead><tr><th>Severity</th><th>Type</th><th>Position</th><th>Region</th><th>Motif</th><th>Recommendation</th></tr></thead>
          <tbody>{liab_rows}</tbody></table>
        </div>
        """

    comp_html = ""
    if len(results) > 1:
        comp_rows = ""
        ranked = []
        for r in results:
            sev = {"high": 0, "medium": 0, "low": 0}
            for f in r.liabilities:
                sev[f.severity] += 1
            risk = sev["high"] * 3 + sev["medium"] * 2 + sev["low"]
            ranked.append((risk, r, sev))
        ranked.sort(key=lambda x: x[0])
        for i, (risk, r, sev) in enumerate(ranked, 1):
            comp_rows += (
                f"<tr><td><b>#{i}</b></td><td>{escape(r.input.name)}</td>"
                f"<td>{r.domain.chain_type.title()}</td>"
                f"<td>{escape(r.germline.v_gene)}</td>"
                f"<td>{r.germline.identity}%</td>"
                f"<td>{_cdr_length(r, 'CDR3')}</td>"
                f"<td style='background:#fee2e2' align='center'>{sev['high']}</td>"
                f"<td style='background:#fef3c7' align='center'>{sev['medium']}</td>"
                f"<td style='background:#dcfce7' align='center'>{sev['low']}</td>"
                f"<td><b>{risk}</b></td></tr>"
            )
        comp_html = f"""
        <div class="seq-block">
          <h2>Candidate Comparison</h2>
          <div class="meta">Ranked by developability risk (lower = better)</div>
          <table><thead><tr><th>Rank</th><th>Sequence</th><th>Chain</th><th>Germline</th>
            <th>Identity</th><th>CDR3 Len</th><th>High</th><th>Med</th><th>Low</th><th>Risk</th></tr></thead>
          <tbody>{comp_rows}</tbody></table>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AbAnnotator Report</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:Inter,'Segoe UI',system-ui,sans-serif; color:#172033; background:#f8fafc; padding:32px; }}
  .header {{ background:linear-gradient(135deg,#1d4ed8,#059669); color:white; padding:28px 32px;
    border-radius:12px; margin-bottom:24px; }}
  .header h1 {{ font-size:1.8rem; font-weight:900; }}
  .header p {{ opacity:0.85; margin-top:6px; }}
  .seq-block {{ background:#fff; border:1px solid #e2e8f0; border-radius:10px;
    padding:20px 24px; margin-bottom:16px; box-shadow:0 4px 12px rgba(0,0,0,0.04); }}
  h2 {{ font-size:1.25rem; font-weight:900; margin-bottom:4px; }}
  h3 {{ font-size:0.95rem; font-weight:800; color:#475467; margin:14px 0 8px; text-transform:uppercase;
    letter-spacing:0.04em; }}
  .meta {{ color:#667085; font-size:0.88rem; margin-bottom:12px; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
  th {{ background:#f1f5f9; color:#344054; font-weight:800; text-align:left; padding:8px 10px;
    border-bottom:2px solid #e2e8f0; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.03em; }}
  td {{ padding:7px 10px; border-bottom:1px solid #f1f5f9; }}
  tr:hover td {{ background:#f8fafc; }}
  .footer {{ text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:24px; }}
</style>
</head>
<body>
<div class="header">
  <h1>AbAnnotator Report</h1>
  <p>Generated {datetime.now().strftime("%B %d, %Y at %H:%M")} | {len(results)} sequence(s) analyzed</p>
</div>
{comp_html}
{rows_html}
<div class="footer">Generated by AbAnnotator | Antibody variable domain analysis</div>
</body>
</html>"""

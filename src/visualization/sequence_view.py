from __future__ import annotations

from html import escape

from src.pipeline.models import AnnotatedAntibody


REGION_COLORS = {
    "FR1": "#f1f5f9",
    "FR2": "#f1f5f9",
    "FR3": "#f1f5f9",
    "FR4": "#f1f5f9",
    "CDR1": "#dbeafe",
    "CDR2": "#dcfce7",
    "CDR3": "#ffedd5",
}

INLINE_COLORS = {
    "FR1": "#94a3b8",
    "FR2": "#94a3b8",
    "FR3": "#94a3b8",
    "FR4": "#94a3b8",
    "CDR1": "#2563eb",
    "CDR2": "#059669",
    "CDR3": "#ea580c",
}


def render_sequence_view(result: AnnotatedAntibody) -> str:
    liability_by_pos: dict[int, list[str]] = {}
    for flag in result.liabilities:
        liability_by_pos.setdefault(flag.position, []).append(f"{flag.severity.upper()}: {flag.type} ({flag.motif})")

    spans = []
    for residue in result.domain.numbered_residues:
        color = REGION_COLORS.get(residue.region, "#f5f7fa")
        border = "#dc2626" if residue.index in liability_by_pos else "rgba(148, 163, 184, 0.35)"
        shadow = "box-shadow:0 0 0 2px rgba(220,38,38,.12);" if residue.index in liability_by_pos else ""
        liabilities = "; ".join(liability_by_pos.get(residue.index, ["No liability flag"]))
        title = escape(f"{residue.region} | pos {residue.position} | {liabilities}")
        # Position marker every 10 residues (shown as superscript above the token)
        pos_marker = ""
        if residue.index % 10 == 0:
            pos_marker = (
                f'<span style="position:absolute;top:-10px;left:50%;transform:translateX(-50%);'
                f'font-size:0.58rem;font-weight:700;color:#94a3b8;white-space:nowrap;">{residue.index}</span>'
            )
        pos_style = "position:relative;" if pos_marker else ""
        spans.append(
            f'<span class="aa-token" title="{title}" '
            f'style="background:{color};border-color:{border};{shadow}{pos_style}">'
            f'{pos_marker}{escape(residue.amino_acid)}</span>'
        )

    # Build inline colored sequence string (the "wow" visual)
    inline_spans = []
    current_region = None
    current_chars = []
    for residue in result.domain.numbered_residues:
        if residue.region != current_region:
            if current_chars and current_region:
                color = INLINE_COLORS.get(current_region, "#94a3b8")
                weight = "700" if current_region.startswith("CDR") else "400"
                inline_spans.append(
                    f'<span style="color:{color};font-weight:{weight}">{"".join(current_chars)}</span>'
                )
            current_region = residue.region
            current_chars = [residue.amino_acid]
        else:
            current_chars.append(residue.amino_acid)
    if current_chars and current_region:
        color = INLINE_COLORS.get(current_region, "#94a3b8")
        weight = "700" if current_region.startswith("CDR") else "400"
        inline_spans.append(
            f'<span style="color:{color};font-weight:{weight}">{"".join(current_chars)}</span>'
        )
    inline_sequence = "".join(inline_spans)

    legend = "".join(
        f'<span class="legend-item"><span style="background:{color}"></span>{name}</span>'
        for name, color in [
            ("Framework", "#f1f5f9"),
            ("CDR1", REGION_COLORS["CDR1"]),
            ("CDR2", REGION_COLORS["CDR2"]),
            ("CDR3", REGION_COLORS["CDR3"]),
            ("Liability", "#c2410c"),
        ]
    )
    raw_sequence = result.domain.sequence

    return f"""
    <style>
      .sequence-panel {{
        border: 1px solid #d8dee8;
        border-radius: 8px;
        padding: 0;
        background: #ffffff;
        box-shadow: 0 12px 28px rgba(15,23,42,0.045);
        overflow: hidden;
      }}
      .copy-btn {{
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 0.78rem;
        font-weight: 700;
        color: #475467;
        cursor: pointer;
        transition: all 0.15s;
      }}
      .copy-btn:hover {{
        background: #e2e8f0;
        color: #172033;
      }}
      .sequence-toolbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        padding: 14px 16px;
        background: linear-gradient(180deg, #ffffff, #f8fafc);
        border-bottom: 1px solid #e2e8f0;
      }}
      .sequence-title {{
        font-weight: 900;
        color: #172033;
      }}
      .sequence-subtitle {{
        color: #667085;
        font-size: 0.82rem;
        margin-top: 2px;
      }}
      .inline-sequence {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.82rem;
        line-height: 1.65;
        word-break: break-all;
        padding: 12px 16px;
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        letter-spacing: 0.5px;
      }}
      .sequence-grid {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        line-height: 2.15;
        word-break: break-all;
        padding: 16px;
        background:
          linear-gradient(90deg, rgba(15,23,42,0.025) 1px, transparent 1px),
          #ffffff;
        background-size: 13.5rem 100%;
      }}
      .aa-token {{
        display: inline-block;
        min-width: 1.32rem;
        margin: 2px;
        padding: 1px 3px;
        border: 1.5px solid transparent;
        border-radius: 4px;
        text-align: center;
        color: #172033;
        font-size: 0.88rem;
        font-weight: 750;
      }}
      .aa-token:hover {{
        transform: translateY(-1px);
        outline: 2px solid rgba(37, 99, 235, 0.18);
      }}
      .legend {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        color: #4b5563;
        font-size: 0.85rem;
      }}
      .legend-item span {{
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 1px solid #cbd5e1;
        border-radius: 3px;
        margin-right: 5px;
        vertical-align: -2px;
      }}
    </style>
    <div class="sequence-panel">
      <div class="sequence-toolbar">
        <div>
          <div class="sequence-title">{escape(result.input.name)} residue map</div>
          <div class="sequence-subtitle">{len(result.domain.sequence)} residues | hover for position, region, and liability context</div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <button class="copy-btn" onclick="
            navigator.clipboard.writeText('{raw_sequence}').then(function(){{
              var btn=event.target;btn.textContent='Copied!';
              setTimeout(function(){{btn.textContent='Copy sequence';}},1500);
            }});">Copy sequence</button>
          <div class="legend">{legend}</div>
        </div>
      </div>
      <div class="inline-sequence">{inline_sequence}</div>
      <div class="sequence-grid">{''.join(spans)}</div>
    </div>
    """

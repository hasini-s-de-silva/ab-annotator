from __future__ import annotations

from html import escape

from src.pipeline.models import AnnotatedAntibody


def render_domain_glyph(result: AnnotatedAntibody) -> str:
    domain = result.domain
    cdr_labels = " | ".join(f"{cdr.name}: {len(cdr.sequence)} aa" for cdr in domain.cdrs)
    chain_label = {
        "heavy": "Heavy chain variable domain",
        "kappa": "Kappa light chain variable domain",
        "lambda": "Lambda light chain variable domain",
        "unknown": "Variable domain",
    }.get(domain.chain_type, "Variable domain")

    # Build the linear domain bar: FR1-CDR1-FR2-CDR2-FR3-CDR3-FR4
    total_len = len(domain.sequence)
    bar_x, bar_y, bar_w, bar_h = 28, 70, 900, 36
    region_colors = {
        "FR1": "#e2e8f0", "CDR1": "#93c5fd", "FR2": "#e2e8f0",
        "CDR2": "#86efac", "FR3": "#e2e8f0", "CDR3": "#fdba74", "FR4": "#e2e8f0",
    }
    region_strokes = {
        "CDR1": "#3b82f6", "CDR2": "#16a34a", "CDR3": "#ea580c",
    }
    region_order = ["FR1", "CDR1", "FR2", "CDR2", "FR3", "CDR3", "FR4"]

    # Collect region lengths
    region_lengths = {}
    for fw in domain.frameworks:
        region_lengths[fw.name] = fw.length
    for cdr in domain.cdrs:
        region_lengths[cdr.name] = cdr.length

    bar_segments = []
    x_cursor = bar_x
    for region_name in region_order:
        rlen = region_lengths.get(region_name, 0)
        if rlen == 0:
            continue
        seg_w = max((rlen / total_len) * bar_w, 18)
        color = region_colors.get(region_name, "#e2e8f0")
        stroke = region_strokes.get(region_name, "#cbd5e1")
        is_cdr = region_name.startswith("CDR")
        rx = "6" if is_cdr else "3"
        seg_h = bar_h if is_cdr else bar_h - 8
        seg_y = bar_y if is_cdr else bar_y + 4
        bar_segments.append(
            f'<rect x="{x_cursor:.1f}" y="{seg_y}" width="{seg_w:.1f}" height="{seg_h}" '
            f'rx="{rx}" fill="{color}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        # Label inside the segment if wide enough
        if seg_w > 30:
            label = region_name
            font_size = "11" if is_cdr else "9"
            font_weight = "800" if is_cdr else "600"
            fill = "#172033" if is_cdr else "#64748b"
            bar_segments.append(
                f'<text x="{x_cursor + seg_w / 2:.1f}" y="{seg_y + seg_h / 2 + 4}" '
                f'text-anchor="middle" font-family="Inter, Arial" font-size="{font_size}" '
                f'font-weight="{font_weight}" fill="{fill}">{label}</text>'
            )
        x_cursor += seg_w + 2

    # Liability tick marks on the domain bar
    liability_ticks = []
    for flag in result.liabilities:
        pos = flag.position
        if 1 <= pos <= total_len:
            tick_x = bar_x + (pos / total_len) * bar_w
            tick_color = {"high": "#dc2626", "medium": "#f59e0b", "low": "#3b82f6"}.get(flag.severity, "#dc2626")
            liability_ticks.append(
                f'<line x1="{tick_x:.1f}" y1="{bar_y - 4}" x2="{tick_x:.1f}" y2="{bar_y + bar_h + 4}" '
                f'stroke="{tick_color}" stroke-width="2" opacity="0.75"/>'
                f'<circle cx="{tick_x:.1f}" cy="{bar_y - 6}" r="3" fill="{tick_color}" opacity="0.9"/>'
            )

    bar_svg = "\n".join(bar_segments) + "\n" + "\n".join(liability_ticks)

    # Legend
    legend_y = bar_y + bar_h + 22
    legend_items = [
        ("#e2e8f0", "#cbd5e1", "Framework"),
        ("#93c5fd", "#3b82f6", "CDR1"),
        ("#86efac", "#16a34a", "CDR2"),
        ("#fdba74", "#ea580c", "CDR3"),
        ("#dc2626", "#dc2626", "Liability"),
    ]
    legend_svg = ""
    lx = 28
    for fill, stroke, label in legend_items:
        legend_svg += (
            f'<rect x="{lx}" y="{legend_y}" width="12" height="12" rx="2" fill="{fill}" stroke="{stroke}"/>'
            f'<text x="{lx + 17}" y="{legend_y + 10}" font-family="Inter, Arial" font-size="11" '
            f'fill="#64748b" font-weight="600">{label}</text>'
        )
        lx += 17 + len(label) * 7 + 14

    svg_height = legend_y + 28

    return f"""
    <div style="border:1px solid #d8dee8;border-radius:8px;background:linear-gradient(180deg,#ffffff,#f8fafc);
                padding:0;overflow:hidden;box-shadow:0 8px 20px rgba(15,23,42,0.04);margin:8px 0 12px;">
      <svg viewBox="0 0 960 {svg_height}" width="100%" role="img" aria-label="Antibody domain architecture">
        <text x="28" y="32" font-family="Inter, Arial" font-size="16" font-weight="900" fill="#172033">
          {escape(domain.name)} Domain Architecture</text>
        <text x="28" y="52" font-family="Inter, Arial" font-size="12" fill="#667085">
          {escape(chain_label)} &middot; {total_len} residues &middot; {escape(cdr_labels)}</text>
        {bar_svg}
        {legend_svg}
      </svg>
    </div>
    """

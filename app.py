from __future__ import annotations

import sys
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import annotate_input
from src.pipeline.examples import EXAMPLE_SEQUENCES
from src.pipeline.export import (
    generate_html_report,
    results_to_csv,
    results_to_json,
    _cdr_length,
    _cdr_sequence,
)
from src.pipeline.models import AnnotatedAntibody
from src.visualization.glyph import render_domain_glyph
from src.visualization.sequence_view import render_sequence_view


st.set_page_config(
    page_title="AbAnnotator",
    page_icon="AB",
    layout="wide",
    initial_sidebar_state="collapsed",
)


CUSTOM_CSS = """
<style>
  :root {
    --ink: #172033;
    --muted: #667085;
    --line: #d8dee8;
    --panel: #ffffff;
    --soft: #f6f8fb;
    --blue: #2563eb;
    --green: #059669;
    --orange: #ea580c;
    --red: #dc2626;
  }
  html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  .stApp {
    background:
      radial-gradient(circle at 5% 8%, rgba(37, 99, 235, 0.08), transparent 30%),
      linear-gradient(180deg, #fbfcff 0%, #f7f9fd 42%, #ffffff 100%);
  }
  .main .block-container { padding-top: 1rem; max-width: 1280px; }
  header[data-testid="stHeader"],
  div[data-testid="stToolbar"],
  footer {
    visibility: hidden;
    height: 0;
  }
  h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
  div[data-testid="stVerticalBlock"] > div:has(.hero-panel) { gap: 0.75rem; }
  .hero-panel {
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 18px 22px;
    background:
      linear-gradient(135deg, rgba(37, 99, 235, 0.10), rgba(5, 150, 105, 0.08)),
      #ffffff;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.055);
  }
  .hero-kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(37, 99, 235, 0.24);
    background: rgba(37, 99, 235, 0.08);
    color: #1d4ed8;
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
  }
  .hero-title {
    margin-top: 10px;
    max-width: 880px;
    color: var(--ink);
    font-size: clamp(1.65rem, 3vw, 2.45rem);
    line-height: 1.06;
    font-weight: 900;
  }
  .hero-subtitle {
    max-width: 860px;
    margin-top: 9px;
    color: #475467;
    font-size: 0.98rem;
    line-height: 1.45;
  }
  .hero-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 12px;
  }
  .hero-chip {
    border: 1px solid rgba(100, 116, 139, 0.22);
    background: rgba(255,255,255,0.72);
    color: #334155;
    border-radius: 999px;
    padding: 7px 11px;
    font-size: 0.82rem;
    font-weight: 700;
  }
  .workbench-panel {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    padding: 18px 18px 14px;
    margin-top: 12px;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.055);
  }
  .workbench-head {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: flex-start;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }
  .workbench-title {
    color: var(--ink);
    font-size: 1.35rem;
    line-height: 1.15;
    font-weight: 900;
  }
  .workbench-copy {
    color: #475467;
    margin-top: 5px;
    line-height: 1.45;
    max-width: 760px;
  }
  .engine-pill {
    border: 1px solid #dbe4f0;
    background: #f8fafc;
    border-radius: 999px;
    color: #475467;
    padding: 8px 11px;
    font-size: 0.84rem;
    font-weight: 750;
  }
  div[data-testid="stTabs"] button {
    font-weight: 850;
  }
  div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #1d4ed8;
  }
  div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #2563eb;
  }
  div[data-testid="stFileUploader"] {
    border: 1px dashed #b8c3d6;
    border-radius: 8px;
    padding: 8px;
    background: #f8fafc;
  }
  textarea {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace !important;
  }
  div[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    color: #172033 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
  }
  div[data-testid="stTextArea"] textarea::placeholder {
    color: #94a3b8 !important;
  }
  div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #172033 !important;
  }
  div[data-testid="stSelectbox"] label,
  div[data-testid="stTextArea"] label,
  div[data-testid="stFileUploader"] label {
    color: #344054 !important;
    font-weight: 750;
  }
  div[data-testid="stForm"] {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px;
    background: #ffffff;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
  }
  .stButton > button,
  .stDownloadButton > button,
  div[data-testid="stFormSubmitButton"] button {
    border-radius: 7px;
    border: 1px solid #1d4ed8;
    background: linear-gradient(180deg, #2f6fed, #1d4ed8);
    color: white;
    font-weight: 800;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
  }
  .stButton > button:hover,
  .stDownloadButton > button:hover,
  div[data-testid="stFormSubmitButton"] button:hover {
    border-color: #1e40af;
    color: white;
  }
  .section-label {
    color: #344054;
    font-weight: 900;
    font-size: 1.05rem;
    margin: 8px 0 10px;
  }
  .result-header {
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 16px 18px;
    background: #ffffff;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.045);
  }
  .result-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }
  .result-name {
    color: var(--ink);
    font-size: 1.45rem;
    line-height: 1.15;
    font-weight: 900;
  }
  .result-meta {
    color: var(--muted);
    margin-top: 4px;
    font-size: 0.9rem;
  }
  .status-pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 7px 11px;
    font-weight: 900;
    font-size: 0.78rem;
    text-transform: uppercase;
  }
  .status-high { color: #991b1b; background: #fee2e2; border: 1px solid #fecaca; }
  .status-medium { color: #92400e; background: #fef3c7; border: 1px solid #fde68a; }
  .status-low { color: #166534; background: #dcfce7; border: 1px solid #bbf7d0; }
  .metric-card {
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 14px 16px;
    background: var(--panel);
    min-height: 96px;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035);
  }
  .metric-label {
    color: var(--muted);
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.055em;
    font-weight: 800;
  }
  .metric-value {
    color: var(--ink);
    font-size: 1.22rem;
    line-height: 1.2;
    font-weight: 900;
    margin-top: 8px;
    word-break: break-word;
  }
  .metric-note {
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 6px;
  }
  .callout-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 12px 0 4px;
  }
  .mini-card {
    border: 1px solid var(--line);
    background: #ffffff;
    border-radius: 8px;
    padding: 12px;
  }
  .mini-card-title {
    font-weight: 900;
    color: var(--ink);
    margin-bottom: 5px;
  }
  .mini-card-seq {
    color: #475467;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.84rem;
    overflow-wrap: anywhere;
  }
  .warning-note {
    border-left: 4px solid #f59e0b;
    background: #fffbeb;
    padding: 9px 12px;
    border-radius: 6px;
    color: #78350f;
    margin: 8px 0;
  }
  .method-note {
    border: 1px solid #dbe4f0;
    background: #f8fafc;
    border-radius: 8px;
    color: #475467;
    padding: 10px 12px;
    font-size: 0.9rem;
  }
  .empty-state {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    padding: 22px 24px;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.045);
  }
  .empty-title {
    color: var(--ink);
    font-size: 1.45rem;
    line-height: 1.15;
    font-weight: 900;
  }
  .empty-copy {
    color: #475467;
    line-height: 1.55;
    max-width: 760px;
    margin-top: 8px;
  }
  div[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
  }
  .severity-bar-wrap {
    display: flex;
    gap: 4px;
    margin: 8px 0 14px;
    border-radius: 6px;
    overflow: hidden;
    min-height: 32px;
  }
  .sev-seg {
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 0.78rem;
    padding: 6px 10px;
    border-radius: 6px;
  }
  .severity-bar-clean {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #166534;
    background: #dcfce7;
    font-weight: 700;
    font-size: 0.82rem;
    padding: 6px 10px;
    border-radius: 6px;
  }
  @media (max-width: 900px) {
    .callout-grid { grid-template-columns: 1fr; }
    .hero-title { font-size: 2rem; }
  }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main() -> None:
    # Initialize analysis history
    if "analysis_history" not in st.session_state:
        st.session_state["analysis_history"] = []

    # Sidebar: analysis history
    with st.sidebar:
        st.markdown("### Analysis History")
        history = st.session_state["analysis_history"]
        if history:
            for i, entry in enumerate(reversed(history)):
                label = entry["label"]
                count = entry["count"]
                scheme_used = entry["scheme"]
                flags = entry["total_flags"]
                st.markdown(
                    f'<div style="padding:8px 10px;border:1px solid #e2e8f0;border-radius:6px;'
                    f'margin-bottom:6px;background:#fff;font-size:0.85rem;">'
                    f'<div style="font-weight:800;color:#172033;">{escape(label)}</div>'
                    f'<div style="color:#667085;font-size:0.78rem;">'
                    f'{count} seq &middot; {scheme_used} &middot; {flags} flag{"s" if flags != 1 else ""}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            if st.button("Clear history", use_container_width=True):
                st.session_state["analysis_history"] = []
                st.rerun()
        else:
            st.caption("No analyses yet this session.")

    render_hero()

    raw_input, source_label, scheme = render_workbench()
    if not raw_input:
        render_empty_state()
        return

    with st.spinner("Annotating sequences..."):
        try:
            results = annotate_input(raw_input, source=source_label, scheme=scheme.lower())
        except Exception as exc:
            st.error(f"Could not annotate the input: {exc}")
            return

    if not results:
        st.warning("No sequences found.")
        return

    # Store results so the Export tab can access them on rerun
    st.session_state["last_results"] = results

    # Add to analysis history (avoid duplicates from reruns)
    total_flags = sum(len(r.liabilities) for r in results)
    if len(results) > 1:
        label = f"Batch ({len(results)} sequences)"
    else:
        label = results[0].input.name
    history_entry = {"label": label, "count": len(results), "scheme": scheme, "total_flags": total_flags}
    hist = st.session_state["analysis_history"]
    if not hist or hist[-1]["label"] != label:
        hist.append(history_entry)

    batch_mode = len(results) > 1
    render_bulk_summary(results)

    if batch_mode:
        st.markdown(
            f'<div style="color:#475467;font-size:0.9rem;margin:8px 0 4px;">'
            f'Expand any sequence below for full annotation details ({len(results)} sequences analyzed).</div>',
            unsafe_allow_html=True,
        )
        for result in results:
            highest = highest_severity(result)
            flag_count = len(result.liabilities)
            tag = f" | {flag_count} flag{'s' if flag_count != 1 else ''}" if flag_count else " | Clean"
            with st.expander(f"{result.input.name}{tag}", expanded=False):
                render_result(result)
    else:
        for result in results:
            render_result(result)

    # About / Methods
    render_about_section()


def render_about_section() -> None:
    with st.expander("About AbAnnotator: Methods and Caveats", expanded=False):
        st.markdown("""
**Annotation method.** AbAnnotator uses anchor-based numbering to identify CDR and framework
boundaries. It locates conserved structural landmarks (the two canonical cysteines, the
Trp-X-X-Q motif, and the J-region terminal motif) and applies scheme-specific offsets to
delineate CDR1, CDR2, and CDR3. Five numbering schemes are supported: IMGT, Kabat, Chothia,
Martin (Enhanced Chothia / AbM), and AHo.

**Germline identification.** V-gene and J-gene family calls are made by sequence similarity
against a curated panel of approved therapeutic antibody sequences using Python's
SequenceMatcher. High-similarity matches (>93% identity) return the specific germline allele;
lower matches fall back to family-level assignment from N-terminal motifs and J-region patterns.

**Liability scanning.** Developability flags are detected by regex pattern matching against
known sequence liabilities: Asn deamidation (NG/NS/NT/NN in CDRs), Asp isomerization
(DG/DS/DT in CDRs), Met oxidation, hydrophobic patches (5+ consecutive hydrophobic residues),
N-glycosylation motifs (N-X-S/T), unpaired cysteines, and polyreactivity risk
(high net charge or aromatic content in CDRs).

**Supported schemes.**
IMGT (default), Kabat, Chothia, Martin, and AHo each define slightly different CDR boundaries.
IMGT is recommended for most modern applications.

**Caveats and limitations.**
This is a prototype annotation tool designed for rapid triage, not production-grade numbering.
For research or clinical use, validate results against established tools such as ANARCI,
AbNum, or IMGT/DomainGapAlign. Germline calls use a limited reference panel and should be
confirmed with IgBLAST or IMGT/V-QUEST. Liability flags are sequence-based only; structural
context (solvent accessibility, paratope position) is not considered. The tool does not
perform multiple sequence alignment or homology modeling.
        """)


def render_workbench() -> tuple[str, str, str]:
    st.markdown(
        """
        <div class="workbench-panel">
          <div class="workbench-head">
            <div>
              <div class="workbench-title">Sequence Workbench</div>
              <div class="workbench-copy">
                Paste a protein sequence, upload FASTA/CSV, or load a known antibody reference.
                Click analyze to generate annotations below.
              </div>
            </div>
            <div class="engine-pill">Engine: anchor-based CDRs + rule-based liabilities</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scheme = st.selectbox(
        "Numbering scheme",
        ["IMGT", "Kabat", "Chothia", "Martin", "AHo"],
        help="Different schemes define CDR boundaries at slightly different positions. "
        "IMGT is the most widely used modern standard. Kabat uses sequence variability, "
        "Chothia uses structural loops, Martin (Enhanced Chothia / AbM) combines both. "
        "AHo uses a fixed-length alignment framework optimised for structural comparison.",
        key="scheme_selector",
    )

    # Collect result from whichever tab submits; render ALL tabs first so
    # Streamlit never skips a tab's widgets (which breaks tab switching).
    pending_result: tuple[str, str, str] | None = None

    paste_tab, upload_tab, reference_tab, batch_tab, export_tab = st.tabs(
        ["Paste Sequence", "Upload FASTA/CSV", "Reference Sequence", "Batch Compare", "Export"]
    )

    with paste_tab:
        with st.form("paste_sequence_form"):
            pasted = st.text_area(
                "Paste sequence or FASTA",
                height=210,
                placeholder="EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIY...",
                help="Accepts a raw amino-acid sequence or FASTA text.",
            ).strip()
            paste_submitted = st.form_submit_button("Analyze pasted sequence", type="primary", width="stretch")
        if paste_submitted and pasted:
            pending_result = (pasted, "text", scheme)

    with upload_tab:
        with st.form("upload_sequence_form"):
            uploaded = st.file_uploader(
                "Upload FASTA, TXT, or CSV",
                type=["fa", "fasta", "txt", "csv"],
                help='CSV files should include a "sequence" or "aa_sequence" column.',
            )
            upload_submitted = st.form_submit_button("Analyze uploaded file", type="primary", width="stretch")
        if upload_submitted and uploaded:
            pending_result = (uploaded.getvalue().decode("utf-8"), uploaded.name, scheme)
        elif upload_submitted:
            st.warning("Please choose a FASTA, TXT, or CSV file before analyzing.")

    with reference_tab:
        with st.form("reference_sequence_form"):
            example = st.selectbox("Choose a reference antibody", list(EXAMPLE_SEQUENCES.keys()))
            st.code(EXAMPLE_SEQUENCES[example], language="text")
            ref_submitted = st.form_submit_button("Analyze reference sequence", type="primary", width="stretch")
        if ref_submitted:
            pending_result = (f">{example}\n{EXAMPLE_SEQUENCES[example]}", "reference", scheme)

    with batch_tab:
        st.markdown(
            '<div style="color:#475467;font-size:0.9rem;margin-bottom:8px;">'
            "Paste multiple sequences in FASTA format to compare them side by side. "
            "Or click <b>Load all references</b> to pre-fill the built-in panel.</div>",
            unsafe_allow_html=True,
        )
        all_refs = "\n".join(f">{name}\n{seq}" for name, seq in EXAMPLE_SEQUENCES.items())

        if "batch_prefill" not in st.session_state:
            st.session_state["batch_prefill"] = ""

        batch_input = st.text_area(
            "Paste multi-FASTA",
            height=220,
            placeholder=">Candidate_1\nEVQLVESGGG...\n>Candidate_2\nDIQMTQSPS...",
            value=st.session_state["batch_prefill"],
            help="Each sequence needs a >header line followed by the amino acid sequence.",
            key="batch_text_area",
        )

        col_submit, col_load = st.columns(2)
        with col_submit:
            batch_submitted = st.button("Compare sequences", type="primary", use_container_width=True)
        with col_load:
            load_refs = st.button("Load all references", use_container_width=True)

        if load_refs:
            st.session_state["batch_prefill"] = all_refs
            st.rerun()
        if batch_submitted and batch_input.strip():
            st.session_state["batch_prefill"] = batch_input.strip()
            pending_result = (batch_input.strip(), "text", scheme)
        elif batch_submitted:
            st.warning("Paste at least two FASTA sequences to compare.")

    with export_tab:
        if "last_results" in st.session_state and st.session_state["last_results"]:
            export_results = st.session_state["last_results"]
            prefix = (
                "abannotator_batch"
                if len(export_results) > 1
                else _safe_file_name(export_results[0].input.name)
            )
            csv_data = results_to_csv(export_results).encode("utf-8")
            html_data = generate_html_report(export_results).encode("utf-8")
            json_data = results_to_json(export_results).encode("utf-8")

            st.markdown(
                f'<div style="color:#344054;font-size:0.9rem;margin-bottom:12px;">'
                f"<b>{len(export_results)}</b> sequence(s) ready for export.</div>",
                unsafe_allow_html=True,
            )
            dl_csv, dl_json, dl_html = st.columns(3)
            with dl_csv:
                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name=f"{prefix}_annotation.csv",
                    mime="text/csv",
                    key="dl_export_csv",
                    use_container_width=True,
                )
            with dl_json:
                st.download_button(
                    "Download JSON",
                    data=json_data,
                    file_name=f"{prefix}_annotation.json",
                    mime="application/json",
                    key="dl_export_json",
                    use_container_width=True,
                )
            with dl_html:
                st.download_button(
                    "Download HTML report",
                    data=html_data,
                    file_name=f"{prefix}_report.html",
                    mime="text/html",
                    key="dl_export_html",
                    use_container_width=True,
                )
        else:
            st.info("Run an analysis first, then come back here to download your results.")

    return pending_result if pending_result else ("", "text", scheme)


def render_bulk_summary(results: list[AnnotatedAntibody]) -> None:
    if len(results) == 1:
        return

    # --- Comparison Dashboard ---
    st.markdown(
        '<div style="border:1px solid #d8dee8;border-radius:8px;padding:16px 18px;'
        'background:linear-gradient(135deg,rgba(37,99,235,0.06),rgba(5,150,105,0.05)),#fff;'
        'box-shadow:0 10px 24px rgba(15,23,42,0.045);margin-top:12px;">'
        '<div style="font-weight:900;font-size:1.3rem;color:#172033;">Candidate Comparison</div>'
        f'<div style="color:#475467;margin-top:4px;">Ranked by developability risk (fewer flags = better) '
        f'&middot; {len(results)} sequences</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # Build comparison data sorted by risk
    comp_data = []
    for item in results:
        sev_counts = {"high": 0, "medium": 0, "low": 0}
        for flag in item.liabilities:
            sev_counts[flag.severity] += 1
        risk_score = sev_counts["high"] * 3 + sev_counts["medium"] * 2 + sev_counts["low"]
        comp_data.append(
            {
                "Rank": 0,
                "Sequence": item.input.name,
                "Chain": item.domain.chain_type.title(),
                "Germline": item.germline.v_gene,
                "Identity %": round(item.germline.identity, 1),
                "CDR3 Length": _cdr_length(item, "CDR3"),
                "High": sev_counts["high"],
                "Med": sev_counts["medium"],
                "Low": sev_counts["low"],
                "Total Flags": len(item.liabilities),
                "Risk Score": risk_score,
                "CDR3": _cdr_sequence(item, "CDR3"),
            }
        )
    comp_data.sort(key=lambda x: x["Risk Score"])
    for i, row in enumerate(comp_data, 1):
        row["Rank"] = i

    comp_df = pd.DataFrame(comp_data)

    # Styled comparison table
    def _risk_bg(val):
        if isinstance(val, (int, float)):
            if val == 0:
                return "background-color:#dcfce7;color:#166534;font-weight:800"
            if val <= 2:
                return "background-color:#fef3c7;color:#92400e;font-weight:800"
            return "background-color:#fee2e2;color:#991b1b;font-weight:800"
        return ""

    styled = comp_df.style.map(
        _risk_bg, subset=["High", "Med", "Low", "Total Flags", "Risk Score"]
    )
    st.dataframe(styled, width="stretch", hide_index=True)

    # Visual severity heatmap bar for each candidate
    heatmap_html = '<div style="display:flex;flex-direction:column;gap:8px;margin:8px 0 16px;">'
    for row in comp_data:
        total = row["Total Flags"] or 1
        bar_segments = ""
        for sev, color, label in [
            ("High", "#dc2626", "H"),
            ("Med", "#f59e0b", "M"),
            ("Low", "#3b82f6", "L"),
        ]:
            count = row[sev]
            if count > 0:
                w = max(count / total * 100, 15)
                bar_segments += (
                    f'<div style="flex:{w};background:{color};color:#fff;font-weight:800;'
                    f'font-size:0.75rem;padding:4px 8px;border-radius:4px;text-align:center;">'
                    f"{count}{label}</div>"
                )
        if not bar_segments:
            bar_segments = (
                '<div style="flex:1;background:#dcfce7;color:#166534;font-weight:700;'
                'font-size:0.78rem;padding:4px 8px;border-radius:4px;text-align:center;">Clean</div>'
            )
        heatmap_html += (
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="min-width:140px;font-weight:700;font-size:0.85rem;color:#172033;">'
            f'#{row["Rank"]} {escape(row["Sequence"])}</div>'
            f'<div style="flex:1;display:flex;gap:3px;border-radius:6px;overflow:hidden;">'
            f"{bar_segments}</div></div>"
        )
    heatmap_html += "</div>"
    st.markdown(heatmap_html, unsafe_allow_html=True)


def render_result(result: AnnotatedAntibody) -> None:
    st.divider()
    st.markdown(render_result_header(result), unsafe_allow_html=True)

    for warning in result.warnings:
        st.markdown(f'<div class="warning-note">{warning}</div>', unsafe_allow_html=True)

    cols = st.columns(4)
    metric(cols[0], "Domain", result.domain.name, f"{len(result.domain.sequence)} aa variable region")
    metric(cols[1], "Chain type", result.domain.chain_type.title(), f"{result.domain.confidence} confidence")
    metric(cols[2], "Germline", result.germline.v_gene, f"{result.germline.identity}% identity")
    metric(cols[3], "Risk flags", str(len(result.liabilities)), liability_summary(result))

    # Liability severity bar
    st.markdown(render_severity_bar(result), unsafe_allow_html=True)

    # Domain glyph full-width above the residue map
    st.markdown(render_domain_glyph(result), unsafe_allow_html=True)

    # Sequence residue map full-width
    st.markdown(render_sequence_view(result), unsafe_allow_html=True)

    # CDR cards using native st.columns to avoid HTML rendering issues
    render_cdr_cards_native(result)

    # Build full region table: frameworks + CDRs in domain order
    all_regions = []
    for region in sorted(
        list(result.domain.frameworks) + list(result.domain.cdrs),
        key=lambda r: r.start,
    ):
        all_regions.append(
            {
                "Region": region.name,
                "Start": region.start,
                "End": region.end,
                "Length": region.length,
                "Sequence": region.sequence,
            }
        )
    region_df = pd.DataFrame(all_regions)
    tab_overview, tab_liabilities = st.tabs(["Annotation", "Liabilities"])

    with tab_overview:
        st.dataframe(
            region_df.style.apply(
                lambda row: [
                    "background-color: #eff6ff; font-weight: 700" if row["Region"].startswith("CDR") else ""
                ] * len(row),
                axis=1,
            ),
            width="stretch",
            hide_index=True,
        )
        st.markdown(
            f'<div class="method-note">Germline method: {result.germline.method}. {result.germline.note}</div>',
            unsafe_allow_html=True,
        )

    with tab_liabilities:
        if result.liabilities:
            st.dataframe(
                liability_dataframe(result).style.map(_severity_style, subset=["Severity"]),
                width="stretch",
                hide_index=True,
            )
        else:
            st.success("No liabilities detected by the current rule set.")


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-panel">
          <div class="hero-kicker">Antibody analysis</div>
          <div class="hero-title">Analyze antibody variable domains in seconds.</div>
          <div class="hero-subtitle">
            Paste a VH or VL sequence to generate CDR/FR calls, germline hints, developability
            liability flags, and a residue-level report you can review, export, and share.
          </div>
          <div class="hero-strip">
            <span class="hero-chip">5 numbering schemes</span>
            <span class="hero-chip">CDR/FR segmentation</span>
            <span class="hero-chip">Germline family ID</span>
            <span class="hero-chip">Liability triage</span>
            <span class="hero-chip">Batch compare</span>
            <span class="hero-chip">HTML report</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
          <div style="font-size:2.4rem;margin-bottom:8px;">&#x1F9EC;</div>
          <div class="empty-title">Ready for analysis</div>
          <div class="empty-copy">
            Paste a VH or VL variable-domain sequence above, upload a FASTA/CSV file,
            or load a reference antibody to get started. Results will include CDR/FR boundaries,
            germline hints, developability flags, and exportable reports.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_header(result: AnnotatedAntibody) -> str:
    highest = highest_severity(result)
    status_class = {
        "high": "status-high",
        "medium": "status-medium",
        "low": "status-low",
        "none": "status-low",
    }[highest]
    label = "Review recommended" if highest == "high" else "Looks clean" if highest == "none" else "Monitor"
    return f"""
    <div class="result-header">
      <div class="result-title-row">
        <div>
          <div class="result-name">{escape(result.input.name)}</div>
          <div class="result-meta">{result.domain.name} | {len(result.domain.sequence)} residues | {result.domain.scheme.upper()}-style labels</div>
        </div>
        <div class="status-pill {status_class}">{label}</div>
      </div>
    </div>
    """


def render_cdr_cards_native(result: AnnotatedAntibody) -> None:
    """Render CDR cards using native Streamlit columns to avoid HTML sanitization issues."""
    cdrs = result.domain.cdrs
    if not cdrs:
        return
    cols = st.columns(len(cdrs))
    for col, cdr in zip(cols, cdrs):
        card_html = (
            f'<div class="mini-card">'
            f'<div class="mini-card-title">{escape(cdr.name)} '
            f'<span style="color:#667085;font-weight:700;">{cdr.length} aa</span></div>'
            f'<div class="mini-card-seq">{escape(cdr.sequence)}</div>'
            f'</div>'
        )
        col.markdown(card_html, unsafe_allow_html=True)


def render_severity_bar(result: AnnotatedAntibody) -> str:
    """Render a horizontal stacked severity bar for quick visual triage."""
    counts = {"high": 0, "medium": 0, "low": 0}
    for flag in result.liabilities:
        counts[flag.severity] += 1
    total = sum(counts.values())
    if total == 0:
        return '<div class="severity-bar-wrap"><div class="severity-bar-clean">No liability flags detected</div></div>'

    segments = []
    colors = {"high": "#dc2626", "medium": "#f59e0b", "low": "#3b82f6"}
    labels = {"high": "High", "medium": "Med", "low": "Low"}
    for sev in ("high", "medium", "low"):
        if counts[sev] > 0:
            pct = max(counts[sev] / total * 100, 12)
            segments.append(
                f'<div class="sev-seg" style="flex:{pct};background:{colors[sev]}">'
                f'{counts[sev]} {labels[sev]}</div>'
            )
    return f'<div class="severity-bar-wrap">{"".join(segments)}</div>'


def metric(column, label: str, value: str, note: str = "") -> None:
    column.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def liability_dataframe(result: AnnotatedAntibody) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Severity": flag.severity.upper(),
                "Type": flag.type,
                "Position": flag.position,
                "Region": flag.region,
                "Motif": flag.motif,
                "Recommendation": flag.recommendation,
            }
            for flag in result.liabilities
        ]
    )


def _severity_style(value: str) -> str:
    if value == "HIGH":
        return "background-color: #fee2e2; color: #991b1b; font-weight: 800"
    if value == "MEDIUM":
        return "background-color: #fef3c7; color: #92400e; font-weight: 800"
    return "background-color: #dcfce7; color: #166534; font-weight: 800"


def highest_severity(result: AnnotatedAntibody) -> str:
    severities = {flag.severity for flag in result.liabilities}
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    if "low" in severities:
        return "low"
    return "none"


def liability_summary(result: AnnotatedAntibody) -> str:
    counts = {"high": 0, "medium": 0, "low": 0}
    for flag in result.liabilities:
        counts[flag.severity] += 1
    if not result.liabilities:
        return "No rule-based findings"
    return f"{counts['high']} high, {counts['medium']} medium, {counts['low']} low"


def _safe_file_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value).strip("_") or "annotation"


if __name__ == "__main__":
    main()

"""Tests for src.pipeline.export."""

import json
import pytest
from src.pipeline.annotate import annotate
from src.pipeline.export import results_to_csv, results_to_json, generate_html_report
from src.pipeline.models import AntibodySequence


TRASTUZUMAB_VH = (
    "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGR"
    "FTISADTSKNTAYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS"
)

TRASTUZUMAB_VL = (
    "DIQMTQSPSSLSASVGDRVTITCRASQDVNTAVAWYQQKPGKAPKLLIYSASFLYSGVPSRFSGSRSG"
    "TDFTLTISSLQPEDFATYYCQQHYTTPPTFGQGTKVEIK"
)


def _annotate_single():
    seqs = [AntibodySequence(name="TestVH", sequence=TRASTUZUMAB_VH)]
    return annotate(seqs)


def _annotate_batch():
    seqs = [
        AntibodySequence(name="TestVH", sequence=TRASTUZUMAB_VH),
        AntibodySequence(name="TestVL", sequence=TRASTUZUMAB_VL),
    ]
    return annotate(seqs)


# --- CSV export ---

def test_csv_has_header():
    csv_text = results_to_csv(_annotate_single())
    lines = csv_text.strip().split("\n")
    assert "name" in lines[0]
    assert "chain_type" in lines[0]
    assert "region" in lines[0]


def test_csv_has_data_rows():
    csv_text = results_to_csv(_annotate_single())
    lines = csv_text.strip().split("\n")
    assert len(lines) > 1, "CSV should have header + data rows"


def test_csv_batch_has_both_sequences():
    csv_text = results_to_csv(_annotate_batch())
    assert "TestVH" in csv_text
    assert "TestVL" in csv_text


# --- JSON export ---

def test_json_valid():
    json_text = results_to_json(_annotate_single())
    data = json.loads(json_text)
    assert isinstance(data, list)
    assert len(data) == 1


def test_json_structure():
    json_text = results_to_json(_annotate_single())
    data = json.loads(json_text)
    entry = data[0]
    assert entry["name"] == "TestVH"
    assert "chain_type" in entry
    assert "germline" in entry
    assert "regions" in entry
    assert "liabilities" in entry
    assert "risk_summary" in entry


def test_json_regions_ordered():
    json_text = results_to_json(_annotate_single())
    data = json.loads(json_text)
    regions = data[0]["regions"]
    starts = [r["start"] for r in regions]
    assert starts == sorted(starts), "Regions should be ordered by start position"


def test_json_risk_summary():
    json_text = results_to_json(_annotate_single())
    data = json.loads(json_text)
    risk = data[0]["risk_summary"]
    assert "high" in risk
    assert "medium" in risk
    assert "low" in risk
    assert "score" in risk
    assert risk["score"] == risk["high"] * 3 + risk["medium"] * 2 + risk["low"]


# --- HTML report ---

def test_html_report_is_html():
    html = generate_html_report(_annotate_single())
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_html_contains_sequence_name():
    html = generate_html_report(_annotate_single())
    assert "TestVH" in html


def test_html_batch_has_comparison():
    html = generate_html_report(_annotate_batch())
    assert "Candidate Comparison" in html
    assert "TestVH" in html
    assert "TestVL" in html

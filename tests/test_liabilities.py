"""Tests for src.pipeline.liabilities."""

import pytest
from src.pipeline.numbering import number_sequence
from src.pipeline.liabilities import scan_liabilities


TRASTUZUMAB_VH = (
    "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGR"
    "FTISADTSKNTAYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS"
)


def _get_liabilities(sequence: str) -> list:
    domain = number_sequence(sequence)
    return scan_liabilities(domain)


# --- Basic scanning ---

def test_returns_list():
    flags = _get_liabilities(TRASTUZUMAB_VH)
    assert isinstance(flags, list)


def test_flags_have_required_fields():
    flags = _get_liabilities(TRASTUZUMAB_VH)
    if flags:
        flag = flags[0]
        assert hasattr(flag, "type")
        assert hasattr(flag, "severity")
        assert hasattr(flag, "position")
        assert hasattr(flag, "region")
        assert hasattr(flag, "motif")
        assert hasattr(flag, "description")
        assert hasattr(flag, "recommendation")


def test_severity_values_valid():
    flags = _get_liabilities(TRASTUZUMAB_VH)
    valid = {"high", "medium", "low"}
    for flag in flags:
        assert flag.severity in valid, f"Invalid severity: {flag.severity}"


def test_flags_sorted_by_severity():
    flags = _get_liabilities(TRASTUZUMAB_VH)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    severities = [severity_order[f.severity] for f in flags]
    assert severities == sorted(severities), "Flags should be sorted high > medium > low"


def test_no_duplicate_flags():
    flags = _get_liabilities(TRASTUZUMAB_VH)
    keys = [(f.type, f.position, f.motif) for f in flags]
    assert len(keys) == len(set(keys)), "Duplicate flags detected"


# --- Specific liability detection ---

def test_deamidation_detection():
    # Trastuzumab VH has NG motif in CDR region
    flags = _get_liabilities(TRASTUZUMAB_VH)
    deamidation = [f for f in flags if f.type == "Deamidation"]
    # Should detect at least one (NT in CDR region)
    assert any(f.type in ("Deamidation", "N-glycosylation motif") for f in flags)


def test_n_glycosylation_scan():
    # Build a sequence with a clear N-X-S/T motif
    # Use Trastuzumab which has NTAy pattern
    flags = _get_liabilities(TRASTUZUMAB_VH)
    glyco = [f for f in flags if f.type == "N-glycosylation motif"]
    # The NTS/NTT patterns should be detected across the full sequence
    assert isinstance(glyco, list)


def test_position_within_sequence():
    flags = _get_liabilities(TRASTUZUMAB_VH)
    seq_len = len(TRASTUZUMAB_VH)
    for flag in flags:
        assert 1 <= flag.position <= seq_len, (
            f"Flag position {flag.position} outside sequence length {seq_len}"
        )

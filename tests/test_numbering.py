"""Tests for src.pipeline.numbering."""

import pytest
from src.pipeline.numbering import number_sequence, guess_chain_type


TRASTUZUMAB_VH = (
    "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGR"
    "FTISADTSKNTAYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS"
)

TRASTUZUMAB_VL = (
    "DIQMTQSPSSLSASVGDRVTITCRASQDVNTAVAWYQQKPGKAPKLLIYSASFLYSGVPSRFSGSRSG"
    "TDFTLTISSLQPEDFATYYCQQHYTTPPTFGQGTKVEIK"
)

ECULIZUMAB_VL = (
    "QSALTQPASVSGSPGQSITISCTGTSSDVGGYNYVSWYQQHPGKAPKLMIYEVSNRPSGVSNRFSGS"
    "KSGNTASLTISGLQAEDEADYYCSSYTSSSTRVFGTGTKVTVL"
)


# --- guess_chain_type ---

def test_heavy_chain_detection():
    assert guess_chain_type(TRASTUZUMAB_VH) == "heavy"


def test_kappa_chain_detection():
    assert guess_chain_type(TRASTUZUMAB_VL) == "kappa"


def test_lambda_chain_detection():
    assert guess_chain_type(ECULIZUMAB_VL) == "lambda"


# --- number_sequence ---

def test_number_sequence_returns_domain():
    domain = number_sequence(TRASTUZUMAB_VH, scheme="imgt")
    assert domain.name == "VH"
    assert domain.chain_type == "heavy"
    assert domain.scheme == "imgt"
    assert len(domain.sequence) == len(TRASTUZUMAB_VH)


def test_number_sequence_has_three_cdrs():
    domain = number_sequence(TRASTUZUMAB_VH)
    cdr_names = [cdr.name for cdr in domain.cdrs]
    assert "CDR1" in cdr_names
    assert "CDR2" in cdr_names
    assert "CDR3" in cdr_names


def test_number_sequence_has_four_frameworks():
    domain = number_sequence(TRASTUZUMAB_VH)
    fw_names = [fw.name for fw in domain.frameworks]
    assert "FR1" in fw_names
    assert "FR2" in fw_names
    assert "FR3" in fw_names
    assert "FR4" in fw_names


def test_cdr_boundaries_non_overlapping():
    domain = number_sequence(TRASTUZUMAB_VH)
    cdrs = sorted(domain.cdrs, key=lambda c: c.start)
    for i in range(len(cdrs) - 1):
        assert cdrs[i].end < cdrs[i + 1].start, (
            f"{cdrs[i].name} end ({cdrs[i].end}) overlaps with "
            f"{cdrs[i + 1].name} start ({cdrs[i + 1].start})"
        )


def test_all_residues_numbered():
    domain = number_sequence(TRASTUZUMAB_VH)
    assert len(domain.numbered_residues) == len(TRASTUZUMAB_VH)


def test_different_schemes_produce_different_boundaries():
    imgt = number_sequence(TRASTUZUMAB_VH, scheme="imgt")
    kabat = number_sequence(TRASTUZUMAB_VH, scheme="kabat")
    # At least one CDR boundary should differ between schemes
    imgt_ranges = [(c.start, c.end) for c in imgt.cdrs]
    kabat_ranges = [(c.start, c.end) for c in kabat.cdrs]
    assert imgt_ranges != kabat_ranges, "IMGT and Kabat should produce different CDR boundaries"


def test_light_chain_numbering():
    domain = number_sequence(TRASTUZUMAB_VL)
    assert domain.chain_type == "kappa"
    assert domain.name == "VL-kappa"
    assert len(domain.cdrs) == 3


def test_high_confidence_with_anchors():
    domain = number_sequence(TRASTUZUMAB_VH)
    assert domain.confidence == "high"

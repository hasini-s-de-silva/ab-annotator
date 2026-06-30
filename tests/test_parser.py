"""Tests for src.pipeline.parser."""

import pytest
from src.pipeline.parser import (
    clean_sequence,
    looks_like_dna,
    parse_input,
    parse_fasta,
    parse_csv,
)


# --- clean_sequence ---

def test_clean_removes_whitespace_and_stars():
    assert clean_sequence("EVQ LVE*S") == "EVQLVES"


def test_clean_uppercases():
    assert clean_sequence("evqlves") == "EVQLVES"


# --- looks_like_dna ---

def test_dna_detected():
    dna = "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
    assert looks_like_dna(dna) is True


def test_protein_not_detected_as_dna():
    protein = "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIY"
    assert looks_like_dna(protein) is False


def test_short_dna_not_detected():
    assert looks_like_dna("ATGCGATCG") is False


# --- parse_input ---

TRASTUZUMAB_VH = (
    "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGR"
    "FTISADTSKNTAYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS"
)


def test_parse_raw_sequence():
    results = parse_input(TRASTUZUMAB_VH)
    assert len(results) == 1
    assert results[0].name == "Pasted sequence"
    assert results[0].sequence == TRASTUZUMAB_VH


def test_parse_fasta_single():
    fasta = f">TestAb\n{TRASTUZUMAB_VH}"
    results = parse_input(fasta)
    assert len(results) == 1
    assert results[0].name == "TestAb"


def test_parse_fasta_multi():
    fasta = f">Ab1\n{TRASTUZUMAB_VH}\n>Ab2\n{TRASTUZUMAB_VH}"
    results = parse_fasta(fasta)
    assert len(results) == 2
    assert results[0].name == "Ab1"
    assert results[1].name == "Ab2"


def test_parse_csv_input():
    csv_text = f"name,sequence\nTestAb,{TRASTUZUMAB_VH}"
    results = parse_csv(csv_text)
    assert len(results) == 1
    assert results[0].name == "TestAb"


def test_dna_raises_error():
    dna = "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
    with pytest.raises(ValueError, match="DNA/RNA"):
        parse_input(dna)


def test_short_sequence_raises():
    with pytest.raises(ValueError, match="too short"):
        parse_input("EVQLVES")


def test_long_sequence_raises():
    # Use a mix of amino acids that won't trigger the DNA check
    long_seq = "EVQLVES" * 36  # 252 residues
    with pytest.raises(ValueError, match="unusually long"):
        parse_input(long_seq)


def test_invalid_residues_raises():
    # 'B' is not in the standard amino acid alphabet
    bad_seq = "B" * 100
    with pytest.raises(ValueError, match="Unsupported residue"):
        parse_input(bad_seq)

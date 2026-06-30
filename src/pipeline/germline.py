from __future__ import annotations

from difflib import SequenceMatcher

from .examples import EXAMPLE_SEQUENCES
from .models import Domain, GermlineHit


CURATED_GERMLINES = {
    # Heavy chains
    "Trastuzumab VH": ("IGHV3-66*01", "IGHJ4*01"),
    "Bevacizumab VH": ("IGHV3-66*01", "IGHJ4*01"),
    "Eculizumab VH": ("IGHV3-11*01", "IGHJ4-like"),
    "Natalizumab VH": ("IGHV3-9*01", "IGHJ4-like"),
    "Adalimumab VH": ("IGHV3-family", "IGHJ4-like"),
    "Pembrolizumab VH": ("IGHV3-7-like", "IGHJ4-like"),
    "Nivolumab VH": ("IGHV4-59*01", "IGHJ4-like"),
    "Secukinumab VH": ("IGHV3-family", "IGHJ4-like"),
    "Rituximab VH": ("IGHV1-69*01", "IGHJ4-like"),
    "Cetuximab VH": ("IGHV5-51*01", "IGHJ4-like"),
    "Atezolizumab VH": ("IGHV3-23*01", "IGHJ4-like"),
    # Kappa light chains
    "Trastuzumab VL": ("IGKV1-39*01", "IGKJ1*01"),
    "Adalimumab VL": ("IGKV1-39*01", "IGKJ1-like"),
    "Bevacizumab VL": ("IGKV1-39*01", "IGKJ1-like"),
    "Rituximab VL": ("IGKV2-28*01", "IGKJ1-like"),
    "Pembrolizumab VL": ("IGKV4-1*01", "IGKJ1-like"),
    "Nivolumab VL": ("IGKV4-1*01", "IGKJ1-like"),
    "Cetuximab VL": ("IGKV1-5*01", "IGKJ1-like"),
    "Secukinumab VL": ("IGKV3-20*01", "IGKJ1-like"),
    "Natalizumab VL": ("IGKV1-39*01", "IGKJ1-like"),
    # Lambda light chains
    "Eculizumab VL": ("IGLV2-14*01", "IGLJ1-like"),
}


def identify_germline(domain: Domain) -> GermlineHit:
    best_name, best_score = _closest_curated_sequence(domain.sequence)
    if best_score >= 0.93:
        v_gene, j_gene = CURATED_GERMLINES.get(best_name, _family_level_hit(domain))
        return GermlineHit(
            v_gene=v_gene,
            j_gene=j_gene,
            identity=round(best_score * 100, 1),
            method="reference sequence match",
            note=f"Closest reference sequence: {best_name}",
        )

    v_gene, j_gene = _family_level_hit(domain)
    # Use the actual best alignment score rather than a hardcoded placeholder
    identity = round(best_score * 100, 1)
    return GermlineHit(
        v_gene=v_gene,
        j_gene=j_gene,
        identity=identity,
        method="motif-based family assignment",
        note=f"Family-level call from conserved sequence motifs. Nearest reference: {best_name} ({identity}% identity).",
    )


def _closest_curated_sequence(sequence: str) -> tuple[str, float]:
    scores = {
        name: SequenceMatcher(None, sequence, reference).ratio()
        for name, reference in EXAMPLE_SEQUENCES.items()
    }
    return max(scores.items(), key=lambda item: item[1])


def _family_level_hit(domain: Domain) -> tuple[str, str]:
    seq = domain.sequence
    if domain.chain_type == "heavy":
        if seq.startswith("EVQLVES"):
            return "IGHV3-family", _heavy_j(seq)
        if seq.startswith("QVQLVQ"):
            return "IGHV1/3-family", _heavy_j(seq)
        return "IGHV-family unresolved", _heavy_j(seq)
    if domain.chain_type == "kappa":
        if seq.startswith("DIQMTQ"):
            return "IGKV1-family", _light_j(seq)
        return "IGKV-family unresolved", _light_j(seq)
    if domain.chain_type == "lambda":
        return "IGLV-family unresolved", _lambda_j(seq)
    return "unresolved", "unresolved"


def _heavy_j(sequence: str) -> str:
    if "WGQGTLVTVSS" in sequence[-20:]:
        return "IGHJ4-like"
    if "WGQGTTVTVSS" in sequence[-20:]:
        return "IGHJ4/6-like"
    return "IGHJ-like"


def _light_j(sequence: str) -> str:
    if "FGQGTKVEIK" in sequence[-20:]:
        return "IGKJ1-like"
    if "FGGGTK" in sequence[-20:]:
        return "IGKJ-like"
    if "FGAGTKLELK" in sequence[-20:]:
        return "IGKJ4-like"
    return "IGKJ/IGLJ-like"


def _lambda_j(sequence: str) -> str:
    if "FGTGTKVTVL" in sequence[-20:]:
        return "IGLJ1-like"
    if "FGGGTKLTV" in sequence[-20:]:
        return "IGLJ2/3-like"
    return "IGLJ-like"

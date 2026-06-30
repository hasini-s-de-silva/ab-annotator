from __future__ import annotations

import re

from .models import CDRRegion, ChainType, Domain, FrameworkRegion, NumberedResidue


REGION_ORDER = ("FR1", "CDR1", "FR2", "CDR2", "FR3", "CDR3", "FR4")

# Scheme-specific CDR boundary offsets relative to conserved anchors.
# Each entry: (cdr1_start_offset, cdr1_len_heavy, cdr1_len_light,
#              cdr2_start_offset_from_w, cdr2_len_heavy, cdr2_len_light,
#              cdr3_end_trim)  -- these are approximate heuristic shifts.
SCHEME_OFFSETS = {
    "imgt": {
        "heavy": {"cdr1_c_offset": 4, "cdr2_w_offset": 16, "cdr2_maxlen": 16},
        "light": {"cdr1_c_offset": 1, "cdr2_w_offset": 0, "cdr2_maxlen": 7},
    },
    "kabat": {
        "heavy": {"cdr1_c_offset": 6, "cdr2_w_offset": 16, "cdr2_maxlen": 18},
        "light": {"cdr1_c_offset": 1, "cdr2_w_offset": 0, "cdr2_maxlen": 7},
    },
    "chothia": {
        "heavy": {"cdr1_c_offset": 3, "cdr2_w_offset": 16, "cdr2_maxlen": 10},
        "light": {"cdr1_c_offset": 1, "cdr2_w_offset": 0, "cdr2_maxlen": 7},
    },
    "martin": {
        "heavy": {"cdr1_c_offset": 3, "cdr2_w_offset": 16, "cdr2_maxlen": 12},
        "light": {"cdr1_c_offset": 1, "cdr2_w_offset": 0, "cdr2_maxlen": 7},
    },
    "aho": {
        "heavy": {"cdr1_c_offset": 4, "cdr2_w_offset": 16, "cdr2_maxlen": 10},
        "light": {"cdr1_c_offset": 1, "cdr2_w_offset": 0, "cdr2_maxlen": 7},
    },
}


def number_sequence(sequence: str, scheme: str = "imgt") -> Domain:
    chain_type = guess_chain_type(sequence)
    cdr_ranges = _find_cdr_ranges(sequence, chain_type, scheme=scheme)
    segments = _build_segments(sequence, cdr_ranges)

    numbered = [
        NumberedResidue(
            index=i,
            position=str(i),
            amino_acid=aa,
            region=_region_for_index(i, segments),
            scheme=scheme,
        )
        for i, aa in enumerate(sequence, start=1)
    ]

    cdrs: list[CDRRegion] = []
    frameworks: list[FrameworkRegion] = []
    for name, start, end in segments:
        if start > end:
            continue
        region_seq = sequence[start - 1 : end]
        region = (
            CDRRegion(name, region_seq, start, end, str(start), str(end))
            if name.startswith("CDR")
            else FrameworkRegion(name, region_seq, start, end, str(start), str(end))
        )
        if name.startswith("CDR"):
            cdrs.append(region)
        else:
            frameworks.append(region)

    confidence = "high" if _has_variable_domain_anchors(sequence, chain_type) else "low"
    domain_name = {"heavy": "VH", "kappa": "VL-kappa", "lambda": "VL-lambda"}.get(chain_type, "V-domain")
    return Domain(
        name=domain_name,
        chain_type=chain_type,
        sequence=sequence,
        numbered_residues=numbered,
        cdrs=cdrs,
        frameworks=frameworks,
        scheme=scheme,
        annotation_method="anchor-based numbering",
        confidence=confidence,
    )


def guess_chain_type(sequence: str) -> ChainType:
    prefix = sequence[:18]
    if prefix.startswith(("EVQ", "QVQ", "QLQ", "VQL", "DVQ")):
        return "heavy"
    if prefix.startswith(("DIQ", "EIV", "ELT", "QSV", "DIV", "AIQ", "DIL")):
        return "kappa"
    if prefix.startswith(("QAV", "SYE", "SSE", "ALT", "VLT", "QSA")):
        return "lambda"
    if "WGQG" in sequence[-25:] or "WGRG" in sequence[-25:] or "WGAG" in sequence[-25:]:
        return "heavy"
    if "FGQG" in sequence[-25:] or "FGGG" in sequence[-25:] or "FGAG" in sequence[-25:]:
        return "kappa"
    return "unknown"


def _find_cdr_ranges(
    sequence: str, chain_type: ChainType, scheme: str = "imgt"
) -> dict[str, tuple[int, int]]:
    length = len(sequence)
    first_c = _find_first_conserved_c(sequence)
    first_w = _find_first_framework_w(sequence, first_c)
    second_c = _find_second_conserved_c(sequence)
    terminal_motif = _find_terminal_framework_motif(sequence, chain_type)

    # Look up scheme-specific offsets
    scheme_key = scheme.lower() if scheme.lower() in SCHEME_OFFSETS else "imgt"
    chain_key = "heavy" if chain_type == "heavy" else "light"
    offsets = SCHEME_OFFSETS[scheme_key][chain_key]

    if chain_type == "heavy":
        cdr1_start = (first_c + offsets["cdr1_c_offset"]) if first_c else 26
        cdr1_end = (first_w - 1) if first_w else min(cdr1_start + 9, length)
        cdr2_start = (first_w + offsets["cdr2_w_offset"]) if first_w else 50
        cdr2_end = min(cdr2_start + offsets["cdr2_maxlen"] - 1, (second_c - 2) if second_c else length)
    else:
        cdr1_start = (first_c + offsets["cdr1_c_offset"]) if first_c else 24
        cdr1_end = (first_w - 1) if first_w else min(cdr1_start + 10, length)
        iy_motif = _find_motif(sequence, r"IY", start=(first_w or 30), end=(second_c or length))
        cdr2_start = (iy_motif + 2) if iy_motif else 50
        cdr2_end = min(cdr2_start + offsets["cdr2_maxlen"] - 1, (second_c - 2) if second_c else length)

    cdr3_start = (second_c + 1) if second_c else max(length - 22, 1)
    cdr3_end = (terminal_motif - 1) if terminal_motif else max(length - 11, cdr3_start)

    ranges = {
        "CDR1": _clamp_range(cdr1_start, cdr1_end, length),
        "CDR2": _clamp_range(cdr2_start, cdr2_end, length),
        "CDR3": _clamp_range(cdr3_start, cdr3_end, length),
    }
    return _repair_overlaps(ranges, length, chain_type)


def _build_segments(sequence: str, cdr_ranges: dict[str, tuple[int, int]]) -> list[tuple[str, int, int]]:
    length = len(sequence)
    c1 = cdr_ranges["CDR1"]
    c2 = cdr_ranges["CDR2"]
    c3 = cdr_ranges["CDR3"]
    return [
        ("FR1", 1, c1[0] - 1),
        ("CDR1", c1[0], c1[1]),
        ("FR2", c1[1] + 1, c2[0] - 1),
        ("CDR2", c2[0], c2[1]),
        ("FR3", c2[1] + 1, c3[0] - 1),
        ("CDR3", c3[0], c3[1]),
        ("FR4", c3[1] + 1, length),
    ]


def _region_for_index(index: int, segments: list[tuple[str, int, int]]) -> str:
    for name, start, end in segments:
        if start <= index <= end:
            return name
    return "FR"


def _find_first_conserved_c(sequence: str) -> int | None:
    for idx in range(15, min(36, len(sequence))):
        if sequence[idx - 1] == "C":
            return idx
    return None


def _find_first_framework_w(sequence: str, first_c: int | None) -> int | None:
    start = first_c + 5 if first_c else 28
    end = min(start + 28, len(sequence))
    return _find_motif(sequence, r"W[A-Z]{2,3}Q", start=start, end=end)


def _find_second_conserved_c(sequence: str) -> int | None:
    lower = max(78, len(sequence) - 38)
    upper = max(lower + 1, len(sequence) - 8)
    for idx in range(lower, upper + 1):
        if idx <= len(sequence) and sequence[idx - 1] == "C":
            return idx
    c_positions = [i for i, aa in enumerate(sequence, start=1) if aa == "C"]
    return c_positions[-1] if c_positions else None


def _find_terminal_framework_motif(sequence: str, chain_type: ChainType) -> int | None:
    suffix_start = max(len(sequence) - 24, 1)
    patterns = [r"WGQG", r"WGRG", r"WGAG", r"FGQG", r"FGGG"]
    if chain_type in ("kappa", "lambda"):
        patterns = [r"FGQG", r"FGGG", r"FGAG", r"FGTG", r"WGQG"]
    for pattern in patterns:
        found = _find_motif(sequence, pattern, start=suffix_start, end=len(sequence))
        if found:
            return found
    return None


def _find_motif(sequence: str, pattern: str, start: int, end: int) -> int | None:
    window = sequence[max(start - 1, 0) : min(end, len(sequence))]
    match = re.search(pattern, window)
    return (start + match.start()) if match else None


def _clamp_range(start: int, end: int, length: int) -> tuple[int, int]:
    start = max(1, min(start, length))
    end = max(start, min(end, length))
    return start, end


def _repair_overlaps(
    ranges: dict[str, tuple[int, int]], length: int, chain_type: ChainType
) -> dict[str, tuple[int, int]]:
    c1, c2, c3 = ranges["CDR1"], ranges["CDR2"], ranges["CDR3"]
    if c2[0] <= c1[1]:
        c2 = _clamp_range(c1[1] + 8, c1[1] + (23 if chain_type == "heavy" else 14), length)
    if c3[0] <= c2[1]:
        c3 = _clamp_range(max(length - 20, c2[1] + 8), max(length - 12, c2[1] + 12), length)
    return {"CDR1": c1, "CDR2": c2, "CDR3": c3}


def _has_variable_domain_anchors(sequence: str, chain_type: ChainType) -> bool:
    return bool(
        _find_first_conserved_c(sequence)
        and _find_second_conserved_c(sequence)
        and _find_terminal_framework_motif(sequence, chain_type)
    )

from __future__ import annotations

import csv
import io
import re

from .models import AntibodySequence


AA_ALPHABET = set("ACDEFGHIKLMNPQRSTVWY")
DNA_ALPHABET = set("ACGTUN")


def clean_sequence(sequence: str) -> str:
    """Normalize a protein sequence while preserving only amino-acid letters."""
    sequence = sequence.upper().replace("*", "")
    return "".join(ch for ch in sequence if ch.isalpha())


def looks_like_dna(sequence: str) -> bool:
    cleaned = clean_sequence(sequence)
    return bool(cleaned) and set(cleaned) <= DNA_ALPHABET and len(cleaned) >= 90


def parse_input(raw: str, source: str = "text") -> list[AntibodySequence]:
    raw = raw.strip()
    if not raw:
        return []

    if raw.startswith(">"):
        return parse_fasta(raw, source)

    if _looks_like_csv(raw):
        parsed = parse_csv(raw, source)
        if parsed:
            return parsed

    cleaned = clean_sequence(raw)
    if looks_like_dna(cleaned):
        raise ValueError(
            "This looks like a DNA/RNA nucleotide sequence. "
            "AbAnnotator expects protein (amino acid) sequences. "
            "Please translate your nucleotide sequence to protein first."
        )
    _validate_sequence(cleaned)
    return [AntibodySequence(name="Pasted sequence", sequence=cleaned, source=source)]


def parse_fasta(raw: str, source: str = "fasta") -> list[AntibodySequence]:
    records: list[AntibodySequence] = []
    name: str | None = None
    chunks: list[str] = []

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if name and chunks:
                sequence = clean_sequence("".join(chunks))
                if looks_like_dna(sequence):
                    raise ValueError(
                        f"Sequence '{name}' looks like DNA/RNA. "
                        "AbAnnotator expects protein sequences."
                    )
                _validate_sequence(sequence)
                records.append(AntibodySequence(name=name, sequence=sequence, source=source))
            name = line[1:].strip() or f"Sequence {len(records) + 1}"
            chunks = []
        else:
            chunks.append(line)

    if name and chunks:
        sequence = clean_sequence("".join(chunks))
        if looks_like_dna(sequence):
            raise ValueError(
                f"Sequence '{name}' looks like DNA/RNA. "
                "AbAnnotator expects protein sequences."
            )
        _validate_sequence(sequence)
        records.append(AntibodySequence(name=name, sequence=sequence, source=source))

    return records


def parse_csv(raw: str, source: str = "csv") -> list[AntibodySequence]:
    records: list[AntibodySequence] = []
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        return records

    field_map = {field.lower().strip(): field for field in reader.fieldnames}
    sequence_field = field_map.get("sequence") or field_map.get("aa_sequence")
    name_field = field_map.get("name") or field_map.get("id") or field_map.get("sequence_id")
    if not sequence_field:
        return records

    for idx, row in enumerate(reader, start=1):
        sequence = clean_sequence(row.get(sequence_field, ""))
        if not sequence:
            continue
        _validate_sequence(sequence)
        name = row.get(name_field, "").strip() if name_field else ""
        records.append(
            AntibodySequence(
                name=name or f"CSV sequence {idx}",
                sequence=sequence,
                source=source,
            )
        )
    return records


def _looks_like_csv(raw: str) -> bool:
    first_line = raw.splitlines()[0].lower()
    return "," in first_line and bool(re.search(r"\b(sequence|aa_sequence)\b", first_line))


def _validate_sequence(sequence: str) -> None:
    if len(sequence) < 70:
        raise ValueError(
            f"Sequence is too short ({len(sequence)} residues). "
            "Antibody variable domains are typically 107-130 residues. "
            "Check that the full VH or VL domain is included."
        )
    if len(sequence) > 200:
        raise ValueError(
            f"Sequence is unusually long ({len(sequence)} residues). "
            "A single variable domain is typically 107-130 residues. "
            "If this contains multiple domains or a full-length chain, "
            "please extract just the VH or VL region."
        )
    invalid = sorted(set(sequence) - AA_ALPHABET)
    if invalid:
        raise ValueError(
            f"Unsupported residue(s): {', '.join(invalid)}. "
            "Only standard amino acid letters (A-Y, no B/J/O/U/X/Z) are accepted."
        )

from __future__ import annotations

from .germline import identify_germline
from .liabilities import scan_liabilities
from .models import AnnotatedAntibody, AntibodySequence
from .numbering import number_sequence
from .parser import parse_input


def annotate(sequences: list[AntibodySequence], scheme: str = "imgt") -> list[AnnotatedAntibody]:
    results: list[AnnotatedAntibody] = []
    for item in sequences:
        domain = number_sequence(item.sequence, scheme=scheme)
        germline = identify_germline(domain)
        liabilities = scan_liabilities(domain)
        warnings = _warnings(domain)
        results.append(
            AnnotatedAntibody(
                input=item,
                domain=domain,
                germline=germline,
                liabilities=liabilities,
                warnings=warnings,
            )
        )
    return results


def annotate_input(raw: str, source: str = "text", scheme: str = "imgt") -> list[AnnotatedAntibody]:
    return annotate(parse_input(raw, source=source), scheme=scheme)


def _warnings(domain) -> list[str]:
    warnings = []
    if domain.confidence == "low":
        warnings.append(
            "Variable-domain anchors were incomplete; CDR boundaries are approximate for this sequence."
        )
    return warnings

from __future__ import annotations

import re

from .models import Domain, LiabilityFlag, Severity


def scan_liabilities(domain: Domain) -> list[LiabilityFlag]:
    flags: list[LiabilityFlag] = []
    cdrs = {cdr.name: cdr for cdr in domain.cdrs}

    for cdr in domain.cdrs:
        flags.extend(_scan_pattern(domain, cdr.name, cdr.sequence, cdr.start, r"N[GSTN]", "Deamidation", "high"))
        flags.extend(_scan_pattern(domain, cdr.name, cdr.sequence, cdr.start, r"D[GST]", "Isomerization", "high"))
        flags.extend(_scan_pattern(domain, cdr.name, cdr.sequence, cdr.start, r"M", "Oxidation", "medium"))
        flags.extend(_scan_pattern(domain, cdr.name, cdr.sequence, cdr.start, r"[AILMFWVY]{5,}", "Hydrophobic patch", "medium"))

    flags.extend(_scan_pattern(domain, "Any", domain.sequence, 1, r"N[^P][ST]", "N-glycosylation motif", "high"))
    flags.extend(_scan_cysteines(domain))
    flags.extend(_scan_polyreactivity(domain, cdrs))
    return sorted(_deduplicate(flags), key=lambda flag: (severity_rank(flag.severity), flag.position, flag.type))


def severity_rank(severity: Severity) -> int:
    return {"high": 0, "medium": 1, "low": 2}[severity]


def _scan_pattern(
    domain: Domain,
    region: str,
    sequence: str,
    offset: int,
    pattern: str,
    liability_type: str,
    severity: Severity,
) -> list[LiabilityFlag]:
    return [
        LiabilityFlag(
            type=liability_type,
            position=offset + match.start(),
            region=_region_at(domain, offset + match.start()) if region == "Any" else region,
            motif=match.group(0),
            severity=severity,
            description=_description(liability_type),
            recommendation=_recommendation(liability_type),
        )
        for match in re.finditer(pattern, sequence)
    ]


def _scan_cysteines(domain: Domain) -> list[LiabilityFlag]:
    flags: list[LiabilityFlag] = []
    cysteines = [res.index for res in domain.numbered_residues if res.amino_acid == "C"]
    cdr_cysteines = [res.index for res in domain.numbered_residues if res.amino_acid == "C" and res.region.startswith("CDR")]
    for pos in cdr_cysteines:
        flags.append(
            LiabilityFlag(
                type="Free cysteine risk",
                position=pos,
                region=_region_at(domain, pos),
                motif="C",
                severity="high",
                description="Cysteine in a CDR may form unintended disulfides or mixed species.",
                recommendation="Review structural context; mutate or pair intentionally if developability is poor.",
            )
        )
    if len(cysteines) % 2 == 1:
        flags.append(
            LiabilityFlag(
                type="Odd cysteine count",
                position=cysteines[-1],
                region=_region_at(domain, cysteines[-1]),
                motif="C",
                severity="high",
                description="An odd cysteine count suggests a possible unpaired cysteine.",
                recommendation="Verify disulfide pairing and sequence boundaries.",
            )
        )
    return flags


def _scan_polyreactivity(domain: Domain, cdrs: dict[str, object]) -> list[LiabilityFlag]:
    cdr_sequence = "".join(cdr.sequence for cdr in domain.cdrs)
    net_charge = sum(cdr_sequence.count(aa) for aa in "KRH") - sum(cdr_sequence.count(aa) for aa in "DE")
    aromatic = sum(cdr_sequence.count(aa) for aa in "FWY")
    if net_charge >= 5 or aromatic >= 8:
        cdr3 = next((cdr for cdr in domain.cdrs if cdr.name == "CDR3"), None)
        return [
            LiabilityFlag(
                type="Polyreactivity risk",
                position=cdr3.start if cdr3 else 1,
                region="CDRs",
                motif=f"net charge {net_charge}, aromatics {aromatic}",
                severity="low",
                description="Highly charged or aromatic CDR sets can correlate with nonspecific binding.",
                recommendation="Prioritize confirmatory polyspecificity or self-interaction assays.",
            )
        ]
    return []


def _region_at(domain: Domain, position: int) -> str:
    if position < 1 or position > len(domain.numbered_residues):
        return "Unknown"
    return domain.numbered_residues[position - 1].region


def _description(liability_type: str) -> str:
    return {
        "Deamidation": "Asn-containing motifs in CDRs can degrade into isoAsp/Asp variants.",
        "Isomerization": "Asp motifs in CDRs may isomerize and alter binding or stability.",
        "Oxidation": "Methionine in exposed binding loops can oxidize during manufacturing or storage.",
        "Hydrophobic patch": "Consecutive hydrophobic residues can increase aggregation risk.",
        "N-glycosylation motif": "N-X-S/T motifs can acquire heterogeneous glycans when accessible.",
    }.get(liability_type, "Potential developability liability.")


def _recommendation(liability_type: str) -> str:
    return {
        "Deamidation": "Consider conservative substitutions or stress-test the clone early.",
        "Isomerization": "Check binding after forced degradation; redesign if the motif is exposed.",
        "Oxidation": "Assess solvent exposure and oxidative stress sensitivity.",
        "Hydrophobic patch": "Inspect CDR3 surface exposure and compare aggregation readouts.",
        "N-glycosylation motif": "Confirm whether the motif is structurally accessible before expression scale-up.",
    }.get(liability_type, "Review with structural and assay context.")


def _deduplicate(flags: list[LiabilityFlag]) -> list[LiabilityFlag]:
    seen: set[tuple[str, int, str]] = set()
    unique: list[LiabilityFlag] = []
    for flag in flags:
        key = (flag.type, flag.position, flag.motif)
        if key not in seen:
            unique.append(flag)
            seen.add(key)
    return unique

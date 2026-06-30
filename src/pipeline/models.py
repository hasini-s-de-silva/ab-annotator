from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


ChainType = Literal["heavy", "kappa", "lambda", "unknown"]
Severity = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class AntibodySequence:
    name: str
    sequence: str
    source: str = "text"
    chain_type_hint: ChainType | None = None


@dataclass(frozen=True)
class NumberedResidue:
    index: int
    position: str
    amino_acid: str
    region: str
    scheme: str = "imgt"


@dataclass(frozen=True)
class Region:
    name: str
    sequence: str
    start: int
    end: int
    start_position: str
    end_position: str

    @property
    def length(self) -> int:
        return len(self.sequence)


@dataclass(frozen=True)
class CDRRegion(Region):
    pass


@dataclass(frozen=True)
class FrameworkRegion(Region):
    pass


@dataclass(frozen=True)
class GermlineHit:
    v_gene: str
    j_gene: str
    identity: float
    method: str
    note: str = ""


@dataclass(frozen=True)
class LiabilityFlag:
    type: str
    position: int
    region: str
    motif: str
    severity: Severity
    description: str
    recommendation: str


@dataclass(frozen=True)
class Domain:
    name: str
    chain_type: ChainType
    sequence: str
    numbered_residues: list[NumberedResidue]
    cdrs: list[CDRRegion]
    frameworks: list[FrameworkRegion]
    scheme: str = "imgt"
    annotation_method: str = "anchor-based"
    confidence: str = "unknown"


@dataclass(frozen=True)
class AnnotatedAntibody:
    input: AntibodySequence
    domain: Domain
    germline: GermlineHit
    liabilities: list[LiabilityFlag] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

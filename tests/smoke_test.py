import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import annotate_input
from src.pipeline.examples import EXAMPLE_SEQUENCES


def test_examples_annotate() -> None:
    for name, sequence in EXAMPLE_SEQUENCES.items():
        result = annotate_input(f">{name}\n{sequence}")[0]
        assert result.domain.cdrs, name
        assert any(cdr.name == "CDR3" and cdr.sequence for cdr in result.domain.cdrs), name
        assert result.germline.v_gene, name


def test_liability_detection() -> None:
    sequence = EXAMPLE_SEQUENCES["Pembrolizumab VH"]
    result = annotate_input(sequence)[0]
    assert any(flag.type == "Deamidation" for flag in result.liabilities)


if __name__ == "__main__":
    test_examples_annotate()
    test_liability_detection()
    print("Smoke tests passed")

"""Rescore Tests 2/5/12 from saved results; never contact a model or edit originals.

Place this file in backend/ai_benchmark alongside the evaluators/ and expected/
folders, then run it from backend. The output is a separate audit ledger, not
an overwritten benchmark batch. Existing word-count metrics are preserved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from evaluators.test_02 import calculate_required_facts_coverage
from evaluators.test_05 import evaluate_test_05
from evaluators.test_12 import evaluate_test_12

SCORER_VERSION = "ollama-scoring-audit-v1"
DEFAULT_BATCH = "c42e7725-2ed4-49d3-8ce9-2c05ccfcf61e"


def rescore(archive: Path, expected_dir: Path, batch_id: str) -> dict:
    references = {
        number: json.loads((expected_dir / f"test_{number}_expected.json").read_text(encoding="utf-8-sig"))
        for number in ("02", "05", "12")
    }
    changes = []
    run_keys = set()
    run_ids = set()
    batch_count = 0
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            if not name.lower().endswith(".json"):
                continue
            record = json.loads(bundle.read(name).decode("utf-8-sig"))
            if record.get("batch_id") != batch_id:
                continue
            key = (record["test_id"], record["case_id"], record["run_number"])
            if key in run_keys or record["run_id"] in run_ids:
                raise ValueError("Duplicate run in source batch")
            run_keys.add(key)
            run_ids.add(record["run_id"])
            batch_count += 1
            number = record["test_id"].split("_")[1]
            if number not in references:
                continue
            old = record["evaluation"]["automatic_metrics"]
            if record["execution"]["error"]:
                raise ValueError("An affected run has a provider error; handle separately")
            expected = references[number]
            if number == "02":
                expected = next(c for c in expected["cases"] if c["candidate"] == record["case_id"])
                new = {**old, **calculate_required_facts_coverage(
                    record["output"]["raw_response"], expected["required_facts"],
                )}
            elif number == "05":
                new = {**old, **evaluate_test_05(record["output"]["raw_response"], expected)}
            else:
                new = {**old, **evaluate_test_12(record["output"]["parsed_response"], expected)}
            changes.append({
                "run_id": record["run_id"], "test_id": record["test_id"],
                "case_id": record["case_id"], "run_number": record["run_number"],
                "original_archive_member": name,
                "original_metrics": old, "rescored_metrics": new,
                "changed_fields": sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k) or (k in old) != (k in new)),
            })
    if batch_count != 66 or len(changes) != 15:
        raise ValueError(f"Expected 66 source runs and 15 audit entries; got {batch_count} and {len(changes)}")
    # Include scorer/reference hashes for later replay and comparison.
    base = Path(__file__).resolve().parent
    artifacts = [base / "evaluators" / f"test_{n}.py" for n in ("02", "05", "12")]
    artifacts += [expected_dir / f"test_{n}_expected.json" for n in ("02", "05", "12")]
    artifacts += [base / "evaluators" / "automatic.py", Path(__file__).resolve()]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts if p.is_file()}
    return {
        "scorer_version": SCORER_VERSION, "source_batch_id": batch_id,
        "source_archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "source_run_count": batch_count, "audit_run_count": len(changes),
        "artifact_sha256": hashes,
        "scope": "Tests 02, 05, 12 only; generation, runtime metadata, and original files unchanged",
        "limitations": [
            "Coverage and evidence scores are lexical recognition heuristics, not semantic grounding scores.",
            "Test05 non-JSON answers still use the conservative same-line text baseline.",
            "No contradicted reference claim exists in this Test12 case; that distinction is untested (null).",
        ],
        "entries": sorted(changes, key=lambda d: (d["test_id"], d["case_id"], d["run_number"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-dir", type=Path, default=Path(__file__).resolve().parent / "expected")
    parser.add_argument("--batch-id", default=DEFAULT_BATCH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = rescore(args.archive, args.expected_dir, args.batch_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite an earlier audit; choose another versioned output path instead.
    with args.output.open("x", encoding="utf-8") as target:
        json.dump(result, target, ensure_ascii=False, indent=2)
        target.write("\n")
    print(f"Source runs verified: {result['source_run_count']}")
    print(f"Runs rescored locally: {result['audit_run_count']}")
    print(f"Audit saved: {args.output}")
    print("Original archive and generated answers unchanged; no model requests made.")


if __name__ == "__main__":
    main()

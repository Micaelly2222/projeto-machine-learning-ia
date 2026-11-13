import argparse
import json
from collections import Counter
from pathlib import Path

from app.analyzer import analyze
from app.config import ROOT_DIR
from app.schemas import CaseInput


def evaluate(path: Path, use_llm: bool = False) -> dict:
    cases = json.loads(path.read_text(encoding="utf-8"))
    rows, hits = [], 0
    for item in cases:
        result = analyze(CaseInput(**item["case"]), use_llm=use_llm)
        ok = result.decision.value == item["expected"]
        hits += ok
        rows.append({
            "name": item["name"],
            "expected": item["expected"],
            "predicted": result.decision.value,
            "citations": result.citations,
            "correct": ok,
        })
    return {
        "total": len(cases),
        "correct": hits,
        "accuracy": hits / len(cases),
        "by_decision": dict(Counter(r["predicted"] for r in rows)),
        "cases": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=ROOT_DIR / "data" / "cases.json")
    parser.add_argument("--llm", action="store_true", help="usa o extrator com LLM (exige ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    report = evaluate(args.cases, use_llm=args.llm)
    for row in report["cases"]:
        mark = "OK  " if row["correct"] else "FAIL"
        print(f"{mark} {row['predicted']:<10} expected {row['expected']:<10} {row['name']}")
    print(f"\n{report['correct']}/{report['total']} correct ({report['accuracy']:.0%})")

    out = ROOT_DIR / "reports" / "cases_evaluation.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

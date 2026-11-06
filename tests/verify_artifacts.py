"""
FinTrace 360 - Quality Assurance & Integrity Verification
Verifies all notebooks, figures, models, reports, and documentation artifacts.
"""

from pathlib import Path
import json

def verify_all():
    print("=== 1. VERIFYING JUPYTER NOTEBOOKS ===")
    notebooks = sorted(list(Path("notebooks").glob("*.ipynb")))
    assert len(notebooks) == 6, f"Expected 6 notebooks, found {len(notebooks)}"
    for nb in notebooks:
        with open(nb, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "cells" in data and len(data["cells"]) > 0
            print(f"  [PASS] {nb.name} (valid JSON, {len(data['cells'])} cells)")

    print("\n=== 2. VERIFYING GENERATED FIGURES ===")
    figures = sorted(list(Path("outputs/figures").glob("*.png")))
    assert len(figures) == 10, f"Expected 10 figures, found {len(figures)}"
    for fig in figures:
        size_kb = fig.stat().st_size / 1024
        assert size_kb > 10, f"Figure {fig.name} is unexpectedly small: {size_kb} KB"
        print(f"  [PASS] {fig.name} ({size_kb:.1f} KB)")

    print("\n=== 3. VERIFYING TRAINED MODELS ===")
    models = sorted(list(Path("models").glob("*.joblib")))
    assert len(models) >= 4, f"Expected at least 4 models, found {len(models)}"
    for m in models:
        size_kb = m.stat().st_size / 1024
        print(f"  [PASS] {m.name} ({size_kb:.1f} KB)")

    print("\n=== 4. VERIFYING REPORTS & DOCUMENTATION ===")
    reports = sorted(list(Path("reports").glob("*.md")))
    assert len(reports) == 6, f"Expected 6 reports, found {len(reports)}"
    for r in reports:
        assert r.stat().st_size > 500
        print(f"  [PASS] {r.name} ({r.stat().st_size:,} bytes)")

    docs = sorted(list(Path("docs").glob("*.md")))
    assert len(docs) == 6, f"Expected 6 docs, found {len(docs)}"
    for d in docs:
        assert d.stat().st_size > 500
        print(f"  [PASS] {d.name} ({d.stat().st_size:,} bytes)")

    print("\n=== 5. VERIFYING SQL SCRIPTS ===")
    sqls = sorted(list(Path("sql").glob("*.sql")))
    assert len(sqls) == 9, f"Expected 9 SQL scripts, found {len(sqls)}"
    for s in sqls:
        assert s.stat().st_size > 200
        print(f"  [PASS] {s.name} ({s.stat().st_size:,} bytes)")

    print("\nALL ARTIFACTS VERIFIED AND COMPLIANT!")

if __name__ == "__main__":
    verify_all()

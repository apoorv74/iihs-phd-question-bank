#!/usr/bin/env python3
"""
Export questions from questions.db to questions_part*.js + questions.js.

Run from the repo root:
    python scripts/export.py
    python scripts/export.py --stats
"""

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_FILE = ROOT / "questions.db"
PART_SIZE = 55


def load_questions(conn):
    cursor = conn.execute(
        "SELECT id, part, cat, question, opts, ans FROM questions ORDER BY id"
    )
    questions = []
    for row in cursor:
        q = {"id": row[0], "part": row[1], "cat": row[2], "q": row[3]}
        if row[4] is not None:
            q["opts"] = json.loads(row[4])
            q["ans"] = row[5]
        questions.append(q)
    return questions


def print_stats(conn):
    print("\n── Questions by Part ──")
    for row in conn.execute("SELECT part, COUNT(*) FROM questions GROUP BY part ORDER BY part"):
        label = {"A": "Part A (MCQ)", "B": "Part B (Short Answer)", "C": "Part C (Essay)"}[row[0]]
        print(f"  {label}: {row[1]}")
    total = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"  Total: {total}\n")
    print("── Questions by Category ──")
    for row in conn.execute("SELECT cat, COUNT(*) FROM questions GROUP BY cat ORDER BY COUNT(*) DESC"):
        print(f"  {row[0]}: {row[1]}")


def write_js(questions, root):
    parts = [questions[i:i+PART_SIZE] for i in range(0, len(questions), PART_SIZE)]
    for idx, part in enumerate(parts, 1):
        js = f"// questions_part{idx}.js — auto-generated\n"
        js += f"// Part {idx} of {len(parts)} · questions {part[0]['id']}–{part[-1]['id']}\n"
        js += "(window._QUESTIONS_PARTS = window._QUESTIONS_PARTS || []).push(\n"
        js += json.dumps(part, ensure_ascii=False, indent=2)
        js += "\n);\n"
        (root / f"questions_part{idx}.js").write_text(js, encoding="utf-8")
    loader = "// Auto-generated — do not edit manually.\n"
    loader += "const QUESTIONS = (window._QUESTIONS_PARTS || []).flat();\n"
    (root / "questions.js").write_text(loader, encoding="utf-8")
    print(f"Wrote {len(questions)} questions across {len(parts)} part files")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()
    if not DB_FILE.exists():
        print(f"ERROR: {DB_FILE} not found. Run scripts/migrate.py first.")
        raise SystemExit(1)
    conn = sqlite3.connect(DB_FILE)
    if args.stats:
        print_stats(conn)
    else:
        questions = load_questions(conn)
        print_stats(conn)
        write_js(questions, ROOT)
    conn.close()


if __name__ == "__main__":
    main()


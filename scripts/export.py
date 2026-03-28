#!/usr/bin/env python3
"""
Export questions from questions.db to questions.js.

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
    out = root / "questions.js"
    out.write_text(
        "// Auto-generated — do not edit manually.\n"
        "const QUESTIONS = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(questions)} questions to {out.name}")


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


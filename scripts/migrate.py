
#!/usr/bin/env python3
"""
One-time migration: extract questions from iihs_question_bank.html
and insert them into questions.db (SQLite).

Run from the repo root:
    python scripts/migrate.py
"""

import json
import re
import sqlite3
from pathlib import Path

import json5  # pip install json5

ROOT = Path(__file__).parent.parent
HTML_FILE = ROOT / "index.html"
DB_FILE = ROOT / "questions.db"


def extract_questions_from_html(html: str) -> list[dict]:
    match = re.search(r"const QUESTIONS\s*=\s*(\[.*?\]);", html, re.DOTALL)
    if not match:
        raise ValueError("Could not find QUESTIONS array in HTML")
    js_array = match.group(1)
    js_array = re.sub(r"//[^\n]*", "", js_array)
    return json5.loads(js_array)


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id       INTEGER PRIMARY KEY,
            part     TEXT    NOT NULL CHECK(part IN ('A', 'B', 'C')),
            cat      TEXT    NOT NULL,
            question TEXT    NOT NULL,
            opts     TEXT,
            ans      INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_questions_part ON questions(part);
        CREATE INDEX IF NOT EXISTS idx_questions_cat  ON questions(cat);
    """)
    conn.commit()


def insert_questions(conn: sqlite3.Connection, questions: list[dict]) -> None:
    rows = [
        (q["id"], q["part"], q["cat"], q["q"],
         json.dumps(q["opts"]) if "opts" in q else None, q.get("ans"))
        for q in questions
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO questions (id, part, cat, question, opts, ans) VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()


def main() -> None:
    html = HTML_FILE.read_text(encoding="utf-8")
    questions = extract_questions_from_html(html)
    print(f"Extracted {len(questions)} questions from HTML")
    conn = sqlite3.connect(DB_FILE)
    create_schema(conn)
    insert_questions(conn, questions)
    conn.close()
    print(f"Written to {DB_FILE}")


if __name__ == "__main__":
    main()

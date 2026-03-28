# Scripts

## migrate.py

One-time migration script that extracts the `QUESTIONS` array from `index.html` and populates `questions.db` (SQLite).

**Usage** (run from repo root):
```
uv run scripts/migrate.py
```

---

## export.py

Exports questions from `questions.db` back to `questions.js` for use by the frontend. Also prints a breakdown of questions by part and category.

**Usage** (run from repo root):
```
uv run scripts/export.py          # export to questions.js + print stats
uv run scripts/export.py --stats  # print stats only, no file written
```

Requires `questions.db` to exist - run `migrate.py` first if it doesn't.

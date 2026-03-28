---
name: add-questions
user-invocable: true
allowed-tools: Bash, Read
argument-hint: "[category] [count=5] [part=A]"
---

Add new questions to the IIHS PhD question bank SQLite database and regenerate the exported JS file.

## Arguments

Parse `$ARGUMENTS` as: `[category] [count] [part]`

- **category**: The question category (string, may be quoted). If omitted, ask the user interactively.
- **count**: Number of questions to generate (default: 5)
- **part**: Exam part — `A` (MCQ), `B` (short answer), or `C` (essay). Default: `A`

Examples:
- `/add-questions` → ask for category interactively
- `/add-questions "Climate Change"` → 5 Part A MCQs in Climate Change
- `/add-questions "Climate Change" 10` → 10 Part A MCQs
- `/add-questions "Health & Well-being" 5 B` → 5 Part B short answer questions

## Steps

### 1. Parse arguments

Extract category, count, and part from `$ARGUMENTS`. If category is missing, ask the user which category they want before proceeding.

### 2. Show current database stats

Run the following to understand what exists:

```bash
sqlite3 questions.db "SELECT cat, part, COUNT(*) as n FROM questions GROUP BY cat, part ORDER BY cat, part;"
```

This shows diversity gaps and helps avoid generating redundant content.

### 3. Read existing questions in the target category

```bash
sqlite3 questions.db "SELECT part, question FROM questions WHERE cat='<CATEGORY>' ORDER BY part;"
```

Study these carefully to avoid duplication and to match the existing style and difficulty level.

### 4. Generate questions

Generate exactly `count` questions for the specified part. Requirements:

**Part A (MCQ):**
- 4 answer options labeled a/b/c/d in content (stored as JSON array)
- One correct answer indicated by 0-indexed integer (0=a, 1=b, 2=c, 3=d)
- Question should be specific, factual, and PhD-entrance level
- Options should be plausible; avoid obviously wrong distractors
- No duplication with existing questions in the DB

**Part B (Short Answer):**
- Clear, focused prompts expecting ~100-word responses
- Analytical/applied questions, not purely definitional
- No opts or ans fields needed

**Part C (Essay):**
- Broad, discursive prompts expecting 600–800 word responses
- Should invite synthesis across multiple concepts
- No opts or ans fields needed

**Style guidelines:**
- Align with IIHS PhD entrance exam tone: rigorous, policy-relevant, India-focused where appropriate
- Cover diverse sub-topics within the category across the batch
- Avoid repeating the same angle as existing questions

### 5. Insert questions into the database

Use `sqlite3` with proper escaping. Single quotes inside strings must be escaped as `''`.

**Part A:**
```bash
sqlite3 questions.db "INSERT INTO questions (part, cat, question, opts, ans) VALUES ('A', '<CAT>', '<QUESTION>', '[\"<OPT_A>\", \"<OPT_B>\", \"<OPT_C>\", \"<OPT_D>\"]', <ANS_INDEX>);"
```

**Part B or C:**
```bash
sqlite3 questions.db "INSERT INTO questions (part, cat, question) VALUES ('<PART>', '<CAT>', '<QUESTION>');"
```

Insert each question individually. Verify no SQL errors before proceeding.

### 6. Export to questions.js

```bash
python scripts/export.py
```

This regenerates `questions.js` from the updated database.

### 7. Confirm success

Report:
- How many questions were inserted
- New total count for that category/part
- Confirm `questions.js` was updated

```bash
sqlite3 questions.db "SELECT part, COUNT(*) FROM questions WHERE cat='<CATEGORY>' GROUP BY part;"
```

## Valid Categories (existing in DB)

- Environment & Ecology
- Climate Change
- Urban Planning & Development
- Development Studies & Social Policy
- Research Methods & Statistics
- Indian Polity & Governance
- Current Affairs & Global Events
- Water, Energy & Natural Resources
- Economics & Finance
- Gender, Caste & Social Justice
- Land, Agriculture & Rural Development
- Environmental Economics & Policy
- Disaster Risk & Resilience
- Health & Well-being

New categories are also valid — they will be created automatically on insert.

## DB Schema Reference

```sql
CREATE TABLE questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  part TEXT NOT NULL,      -- 'A', 'B', or 'C'
  cat TEXT NOT NULL,       -- category string
  question TEXT NOT NULL,
  opts TEXT,               -- JSON array string, Part A only
  ans INTEGER              -- 0-indexed correct option, Part A only
);
```

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

### 3. Read ALL existing questions

```bash
sqlite3 questions.db "SELECT id, part, cat, question FROM questions ORDER BY cat, part;"
```

Load the full question list. You will use this in two ways:
- Match the existing style and difficulty level of the target category
- Detect intent-level duplicates across the entire database (Step 4b)

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

### 4b. Check for intent-level duplicates

For each generated question, compare its **core intent** against every existing question in the database — regardless of category or phrasing.

Two questions are intent-duplicates if they are testing the same underlying fact, concept, or analytical point, even if worded differently. Examples:
- "What is the Gini coefficient?" and "Which index measures income inequality?" → same intent
- "Name the body that regulates urban local bodies in India" and "Which constitutional amendment introduced the 74th Amendment Act?" → different intent (one is about the institution, the other about the legislative event)

For each generated question that is an intent-duplicate of an existing question:
- **Discard it**
- **Generate a replacement** that covers a different sub-topic or angle within the category
- Repeat until you have `count` unique-intent questions

Only proceed to Step 5 once all questions in the batch have distinct intent from the full database.

### 5. Balance answer positions (Part A only)

Before inserting, ensure the correct answers are evenly distributed across all four positions (0, 1, 2, 3). Do **not** rely on where the correct answer naturally falls in your generated questions — actively rotate positions.

**Check the current distribution in the DB:**
```bash
sqlite3 questions.db "SELECT ans, COUNT(*) as count FROM questions WHERE part='A' GROUP BY ans ORDER BY ans;"
```

Use this to determine which positions are currently underrepresented. Assign the correct answer positions for the new batch to fill the gaps first, then distribute the remainder evenly.

For example, if generating 8 new Part A questions and positions 2 and 3 are underrepresented, assign 2–3 questions to each of those positions first before filling positions 0 and 1.

**For each question in the batch:**
- Decide the target `ans` position for that question (based on the balanced assignment above)
- Rotate the options array so the correct answer sits at the target index
- The content of the correct answer must not change — only its position in the array

### 6. Insert questions into the database

Use `sqlite3` with proper escaping. Single quotes inside strings must be escaped as `''`.

Get today's date first:
```bash
date +%Y-%m-%d
```

**Part A:**
```bash
sqlite3 questions.db "INSERT INTO questions (part, cat, question, opts, ans, date_added) VALUES ('A', '<CAT>', '<QUESTION>', '[\"<OPT_A>\", \"<OPT_B>\", \"<OPT_C>\", \"<OPT_D>\"]', <ANS_INDEX>, '<YYYY-MM-DD>');"
```

**Part B or C:**
```bash
sqlite3 questions.db "INSERT INTO questions (part, cat, question, date_added) VALUES ('<PART>', '<CAT>', '<QUESTION>', '<YYYY-MM-DD>');"
```

Insert each question individually. Verify no SQL errors before proceeding.

### 7. Export to questions.js

```bash
python scripts/export.py
```

This regenerates `questions.js` from the updated database.

### 8. Confirm success

Report:
- How many questions were inserted
- New total count for that category/part
- Confirm `questions.js` was updated
- For Part A: show the updated global `ans` distribution to confirm balance is maintained

```bash
sqlite3 questions.db "SELECT part, COUNT(*) FROM questions WHERE cat='<CATEGORY>' GROUP BY part;"
sqlite3 questions.db "SELECT ans, COUNT(*) as count FROM questions WHERE part='A' GROUP BY ans ORDER BY ans;"
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
  ans INTEGER,             -- 0-indexed correct option, Part A only
  date_added TEXT NOT NULL -- ISO date string e.g. '2026-03-28'
);
```

---
name: explore-questions
user-invocable: true
allowed-tools: Bash
argument-hint: "[question about the question bank]"
---

Answer questions about the IIHS PhD question bank database (`questions.db`).

## Arguments

`$ARGUMENTS` is a natural language question about the question bank. If empty, show a summary overview.

Examples:
- `/explore-questions` → full overview of the database
- `/explore-questions how many categories are there?`
- `/explore-questions which category has the most questions?`
- `/explore-questions how many Part B questions are there?`
- `/explore-questions show me all Climate Change questions`
- `/explore-questions what question types exist?`

## DB Schema Reference

```sql
CREATE TABLE questions (
  id      INTEGER PRIMARY KEY,
  part    TEXT NOT NULL,   -- 'A' (MCQ), 'B' (short answer), 'C' (essay)
  cat     TEXT NOT NULL,   -- category string
  question TEXT NOT NULL,
  opts    TEXT,            -- JSON array of 4 options, Part A only
  ans     INTEGER          -- 0-indexed correct answer, Part A only
);
```

**Part types:**
- `A` = Multiple Choice Questions (MCQ) - has `opts` and `ans`
- `B` = Short Answer (~100 words)
- `C` = Essay (600–800 words)

## Steps

### 1. Run relevant queries

Based on the user's question (or if no question given, run all overview queries), execute the appropriate `sqlite3` queries against `questions.db`.

**Always useful - run these for any overview or when unsure:**

```bash
# Total questions and categories
sqlite3 questions.db "SELECT COUNT(*) as total_questions, COUNT(DISTINCT cat) as categories FROM questions;"

# Breakdown by part (question type)
sqlite3 questions.db "SELECT part, COUNT(*) as count FROM questions GROUP BY part ORDER BY part;"

# Breakdown by category with part split
sqlite3 questions.db "SELECT cat, SUM(CASE WHEN part='A' THEN 1 ELSE 0 END) as A, SUM(CASE WHEN part='B' THEN 1 ELSE 0 END) as B, SUM(CASE WHEN part='C' THEN 1 ELSE 0 END) as C, COUNT(*) as total FROM questions GROUP BY cat ORDER BY total DESC;"
```

**For category-specific questions:**
```bash
sqlite3 questions.db "SELECT id, part, question FROM questions WHERE cat='<CATEGORY>' ORDER BY part, id;"
```

**For part-specific questions:**
```bash
sqlite3 questions.db "SELECT id, cat, question FROM questions WHERE part='<PART>' ORDER BY cat, id;"
```

**For listing all categories:**
```bash
sqlite3 questions.db "SELECT DISTINCT cat FROM questions ORDER BY cat;"
```

**For questions with gaps (few questions):**
```bash
sqlite3 questions.db "SELECT cat, COUNT(*) as n FROM questions GROUP BY cat HAVING n < 5 ORDER BY n;"
```

### 2. Answer the question

Interpret the query results and answer the user's question clearly in plain English. Format the output as a neat markdown table or list where appropriate.

If the user asked a general overview question or provided no arguments, present:
1. **Total stats**: total questions, number of categories, breakdown by part type
2. **Category breakdown table**: category name, count per part (A/B/C), total
3. **Observations**: e.g., which categories are well-covered, which have gaps

### 3. Offer follow-up

Suggest 2–3 relevant follow-up questions the user might want to ask, like:
- "Want to see all questions in a specific category?"
- "Want to find categories with fewer than 5 questions?"

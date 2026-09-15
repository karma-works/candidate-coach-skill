# SQLite operations

Python 3 standard library, no service or third-party dependency. Resolve `scripts/interview_store.py` relative to the installed skill. Pass `--candidate` with the configured canonical absolute knowledge-base directory. The default DB is `data/<candidate-key>/interviews.sqlite3` inside the installed skill, where the key is a SHA-256 digest of that directory path. Two candidates using the same position ID still have separate stores. Use one knowledge-base root per candidate; do not repoint an existing root to another person. If a knowledge base moves, explicitly select/migrate the existing database rather than silently losing its history. An explicit `--db` overrides this routing only for tests or a user-approved migration/alternative; never point it at another candidate's database. Catalog source files stay in their position folders. Training is append-only.

Invoke:

```sh
python3 <installed-skill>/scripts/interview_store.py --candidate /absolute/path/to/candidate-knowledge-base history --input <temporary-request.json>
```

Use a UTF-8 JSON file for each request, written with a structured file tool or a safely quoted heredoc. Never interpolate transcripts into shell code. Write the request and invoke the helper in one tool call where possible. Remove temporary request files after confirmed persistence. A failed or interrupted tool result must not be reported as a saved answer: retry the identical request. Commands run under one `BEGIN IMMEDIATE` transaction, so `answer_next` commits both the answer and next-turn creation together or neither. Concurrent identical retries preserve one answer and one pending prompt.

## Request contracts

- `import`: full catalog object: `{"position":{"id":"stable-role-id","employer":"Employer","title":"Exact role"},"questions":[...]}`. Include 20–30 questions, each `{"id":"Q01","category":"Allgemein","text":"Question?","intent":"Purpose","criteria":["Criterion"],"sources":["knowledge-base/relevant.md"]}`. Existing IDs cannot change content; revisions need new IDs. Import the selected candidate’s catalog once; repeated sessions reuse it.
- `history`: `{"position":"example-role-001"}`. Position-scoped history including catalogs, questions, sessions, turns, attempts, assessments, completions, frozen blocks, block items, block ends and clarifications. Use for preparation or progress review, not between capture turns.
- `start`: `{"position":"example-role-001","size":8}`. Defaults: eight questions and `realistic`; explicit `"mode":"coaching"` only on request. Saves the block in one operation and returns `session`, stored `mode`, `planned`, `phase` and first/current `turn`. Existing blocks ignore a new `size` or mode; their sequence is stable. A prepared plan is not a record of questions already asked: `turns` are created only as they become current. Old open sessions retain prior turns in order and fill the remaining slots once; if already at/above the requested size, they move to review after their pending turns are answered. Old completed sessions remain readable and assessable without creating a new block.
- `answer_next`: `{"position":"example-role-001","turn":"TURN_UUID","answer":"Actual user words","source":"voice_transcript","transcript_note":"Unclear word; clarify at block end"}`. Store and advance in one transaction. Returns `attempt`, `saved`, `phase` and next `turn`, or `done:true` on block end. An identical retry deduplicates even after the last answer or report completion; a conflicting answer is rejected. `stop:true` stores this answer and ends the block without presenting another question. No scoring, source checks or ranking occurs in this command for a prepared block.
- `next`: `{"position":"example-role-001","session":"SESSION_UUID"}`. Recovery or optional coaching use: returns the current pending question or presents the next frozen item. Does not rank again. At exhaustion, seals the block and returns `done:true, phase:"review"`.
- `end_block`: `{"position":"example-role-001","session":"SESSION_UUID"}`. Early stop without adding an answer. Idempotently seals the block. Unanswered planned questions stay in the plan, not the response list or scoring denominator. Capture cannot be reopened after sealing; finish the review then start a new session.
- `review`: `{"position":"example-role-001","session":"SESSION_UUID"}`. After sealing, returns actual answers with criteria, sources, clarification records and assessments. Realistic-mode review is rejected during capture; coaching mode permits it. No automatic assessment is generated.
- `clarify`: `{"position":"example-role-001","attempt":"ATTEMPT_UUID","text":"the candidate's actual clarification","source":"voice_transcript"}`. Append after the block; identical text/source deduplicates. This preserves the original transcript instead of replacing it with a corrected reconstruction.
- `assess_many`: `{"position":"example-role-001","assessments":[ASSESSMENT_OBJECT,...]}`. Use the v1 shape below (position may be omitted inside each item). All assessment writes are atomic; any invalid item rolls back the batch. Realistic-mode attempts are accepted only after block end. Latest identical assessments deduplicate; corrections append revisions.
- `assess`: one assessment object. Same phase gate and rubric checks as batch assessment.
- `finish`: `{"position":"example-role-001","session":"SESSION_UUID","report":"Concrete final coaching"}`. Persist the report only after the realistic block ends and at least one actual answer exists. Closed sessions reject new capture; corrections to assessments remain append-only. Consult history before retrying an uncertain completion.
- Optional coaching helpers: `answer` uses the `answer_next` input shape but does not advance; `retry` uses `{"position":"example-role-001","session":"SESSION_UUID","turn":"PREVIOUS_TURN_UUID"}` to repeat an answered question before moving on. Immediate retry requires coaching mode. In realistic mode, use post-block `clarify` for transcription corrections.

The helper returns `phase:"capture"` or `phase:"review"` to make the runtime boundary explicit. This field does **not** change or verify a model's reasoning effort. Runtime handling is described in [runtime-phases.md](runtime-phases.md).

Assessment shape (placeholders, not a synthetic training answer):

```json
{
  "position": "POSITION_ID",
  "attempt": "ACTUAL_ATTEMPT_UUID",
  "rubric": "v1",
  "scores": {"relevance": 2, "structure": 2, "evidence": 2, "judgement": 2, "communication": 2},
  "rationales": {"relevance": "Specific observation", "structure": "Specific observation", "evidence": "Specific observation", "judgement": "Specific observation", "communication": "Specific observation"},
  "strength": "One observed strength",
  "improvement": "One concrete change",
  "next_drill": "Focused next attempt",
  "evidence_check": "Source paths and specific corroboration or uncertainty"
}
```

Never use these placeholder scores as a default. Assess actual responses only. Missing transcripts stay pending; available but unclear transcripts are saved with a note and clarified after capture. All tables reject UPDATE/DELETE. Foreign keys bind turns, attempts and assessments to their position; transactions serialize mutations. Catalog revisions retain prior snapshots and questions. SQLite is local plaintext: no uploads, audio capture, external services or hidden history creation are part of this skill.


## Protect data during skill updates

`data/` contains live user records, not distributable example assets. Before an update or reinstall:

1. Pause training writes. Create a timestamped backup with SQLite's `Connection.backup()` API (captures committed data including WAL), either in `data/backups/` for an in-place update or a safe temporary location outside the skill before a full reinstall. Verify `PRAGMA integrity_check` and compare table contents with the source.
2. Update only `SKILL.md`, `agents/`, `references/` and `scripts/`. Exclude `data/` from scaffolding, copy operations and destructive sync. Never recursively replace or delete the installed skill directory while it holds the sole copy of training data.
3. If a full reinstall is necessary, retain the verified backup outside the removed directory and restore it to `data/<candidate-key>/interviews.sqlite3` before any store command. Verify table contents and integrity again; do not overwrite a database that has newer records. Keep the backup until verification is complete.
4. Run helper tests with isolated temporary databases. Never import synthetic fixtures into `data/`, reset history or use a new empty database to conceal a migration failure.

A prior location may be retained as a clearly labelled migration backup, but it is never a second live store. The helper's default always resolves to the installed skill's candidate-specific `data/<candidate-key>/interviews.sqlite3`. Ordinary skill updates require no schema or history rewrite.


## Schema compatibility

Schema version 2 adds only `blocks`, `block_items`, `block_ends`, `clarifications`, lookup indexes and append-only triggers. It never updates or deletes earlier questions, turns, answers, assessments or reports. Once initialized, ordinary capture connections skip schema setup. Before applying the migration to a real store, use the verified backup procedure above and compare every pre-existing table's rows afterwards. Never infer that an older session used blocks: only an explicitly resumed open session receives a plan.

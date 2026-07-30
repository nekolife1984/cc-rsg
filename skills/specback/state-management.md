## State management and resume

### Schema of `state.json`

```json
{
  "current_phase": 3,
  "phase_progress": {
    "phase_3": {
      "total_subtasks": 12,
      "completed_subtasks": 8,
      "blocked_subtasks": ["chapter_payment", "chapter_auth"]
    }
  },
  "started_at": "2026-05-01T10:00:00+09:00",
  "last_updated": "2026-05-01T14:32:15+09:00",
  "session_history": [
    {"timestamp": "2026-05-01T10:00:00+09:00", "phase": 0, "event": "started"},
    {"timestamp": "2026-05-01T10:15:00+09:00", "phase": 1, "event": "transitioned"}
  ]
}
```

### Resume behaviour

When the skill detects an existing `.specback/state.json` at startup, present the situation in the resume message and confirm the user's intent. If `.specback/goal.json` is readable, the resume message is rendered in its `output_language`. Only when `goal.json` itself is missing (so the language is unknown) the bilingual format (English first, then Japanese) is used — identical in shape to Phase 0 Step 3 — to prompt the language selection again.

**Resume-message template (English version, when `output_language: "en"`)**:

```
A previous specback session is in progress. The current state is:

- Current phase: Phase 3 (Investigate)
- Progress: 8 of 12 sub-tasks completed; 2 BLOCKED on critical questions
- Question Bank: 23 unresolved questions (2 critical)
- Last updated: 2026-05-01 14:32

What would you like to do?
(A) Resume from where it stopped (finish remaining Phase 3 tasks)
(B) Roll a phase back (resume from a specified phase)
(C) Full reset (delete .specback/ and start from Phase 0)
(D) Show detailed state, then decide
```

**Resume-message template (Japanese version, when `output_language: "ja"`)**:

```
前回のセッションで specback を実行しています。状況は以下の通りです。

- 現在のフェーズ: Phase 3 (Investigate)
- 進捗: 12サブタスク中8件完了、2件は critical な疑問により BLOCKED 状態
- Question Bank: 未解決疑問 23件(うち critical: 2件)
- 最終更新: 2026-05-01 14:32

以下のいずれを実施しますか?
(A) 続きから再開(Phase 3 残タスクを完了させる)
(B) Phase を巻き戻す(指定する Phase から再開)
(C) 全リセット(.specback/ を削除して Phase 0 から開始)
(D) 状況を詳細表示してから判断する
```


Per-phase resume message details are in the resume table below.

### Resume execution rule (MANDATORY)

After the user confirms the resume option, the agent MUST:

1. **Read `state.json`** to identify `current_phase` (e.g. Phase 3).
2. **Read the corresponding phase detail file** from SKILL.md's phase overview table (e.g. `phase-3-investigate.md`).
3. **Read the appropriate common reference files** if the phase depends on them (Question Bank for Phase 1+/3+, Sub-agent for Phase 3+, State management always).
4. Only then, **resume execution** according to the phase detail file's procedure.

This rule exists because SKILL.md is intentionally lightweight — the phase detail files are NOT in the system prompt and must be explicitly loaded.

**Resume phase → file mapping:**

| current_phase | File(s) to read |
|---------------|-----------------|
| 0 | `phase-0-setup.md` |
| 1 | `phase-1-recon.md`, `question-bank.md` |
| 2 | `phase-2-wbs.md` |
| 3 | `phase-3-investigate.md`, `question-bank.md`, `subagent-behavior.md` |
| 4 | `phase-4-verify.md`, `question-bank.md` |
| 5 | `phase-5-dialogue.md`, `question-bank.md` |
| 6 | `phase-6-deliver.md`, `state-management.md` |
| 6.5 | `phase-6-5-deepdive.md` |
| 7 | `phase-7-drift.md` |
| 7b | `phase-7b-ref-autofix.md` |
| 7c | `phase-7c-changespec.md` |

---

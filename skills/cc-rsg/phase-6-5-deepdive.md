## 🆕 Phase 6.5: Deep-dive acceptance mode (when `depth_mode` is `outline` or `interactive`)

### Purpose

In `outline` / `interactive` modes, the spec at the end of Phase 6 is only "overview tables + Mermaid + deep-dive candidates". **The user reading the spec points out items of interest and asks for on-the-spot deep-dives** — that is the essence of these modes. Phase 6.5 holds the agent in a **deep-dive acceptance state**, waiting for explicit user instructions, until the env is closed.

### Behaviour

After the Phase 6 completion report, the agent emits the following message and **waits for input**:

```
✅ Overview spec generation is complete (X chapters / Y tables / Z deep-dive candidates).

Check the "Deep-dive candidates" section at the end of each chapter.
For items of interest, instruct like this:

- By candidate ID:  "Deep-dive D-001" / "D-007"
- By entity ID:    "Tell me more about M-013 Issue" / "C-018 ProjectsController"
- By natural text: "Explain the authorisation model" / "How does Issue notification delivery work?"

To end the deep-dive mode, reply "end" / "complete" / "OK, done".
```

### Recognising and processing instructions

Recognise user input via the following patterns:

1. **Explicit ID (highest priority)**: matches `D-NNN` / `M-NNN` / `C-NNN` / `T-NNN`, etc. → look up the row/candidate in `wbs.json` / `inventory.json` / per-chapter tables → obtain the file and overview.
2. **Direct entity name**: `Issue class` / `ProjectsController`, etc. → identify the file via `grep`.
3. **Natural-language topic**: keywords like `authorisation` / `notification` / `payment` → keyword-search the relevant chapters/table rows, present the top 3 to the user, and ask "Which one do you want to deep-dive?".

### Generating a deep-dive chapter

Once the deep-dive target is fixed:

1. Launch the `chapter-investigator` sub-agent via the `task` tool.
2. Sub-agent prompt:
   - Target entity / candidate ID and overview
   - List of related real source files
   - "Write 1 chapter at **comprehensive-mode-equivalent quality**" (≥ 200 lines, ≥ 10 REFs, ≥ 1 Mermaid, ≥ 5 Sources Read)
   - Output path: `.cc-rsg/drafts/deep/D-NNN-{slug}.md` or `M-NNN-{slug}.md`
3. Display the key findings returned by the sub-agent in the main thread.
4. **Update traceability.md** (append the deep-dive chapter).
5. **Update the relevant row in the original Layer 1 chapter**: bump the confidence from 🟡/🔴 → 🟢, add a "see deep-dive `D-001`" link.
6. Report completion and return to the input-waiting state.

### Ending

When the user sends a completion word ("end", "complete", "OK, done", etc.):

1. Update `state.json` with `phase_6_5_completed_at`.
2. Re-generate `final/` (consolidating the deep-dive chapters).
3. Update final/traceability.md to the final version.
4. Close the env with a thank-you message.

### Phase-specific cautions

- **While waiting for user input, the agent does NOT poll or self-progress**. It moves only after an explicit instruction.
- If a deep-dive is **requested for a target already covered**, surface the existing deep-dive chapter and ask "Regenerate it?".
- Sub-agent return values during deep-dive also follow the **mode B contract** (path + summary), not the full body.
- Be mindful of cumulative cost: each deep-dive equals roughly one comprehensive chapter. Periodically report "N deep-dives so far, cumulative cost ~$X".

---

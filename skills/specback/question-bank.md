## Question Bank operation

### Data structure

Each entry in `.specback/questions.json` has the following fields:

```json
{
  "id": "Q-042",
  "generated_at_phase": "investigation",
  "category": "business_rule",
  "body": "Is the 3-retry of this payment process driven by a technical constraint or a business requirement?",
  "evidence": {
    "file": "src/payment/PaymentRetryHandler.php",
    "lines": "45-58",
    "code_excerpt": "for ($i = 0; $i < 3; $i++) { ... }"
  },
  "related_inventory_ids": ["INV-027"],
  "severity": "important",
  "resolution_type": "ask_sme",
  "status": "open",
  "answer": null,
  "answerer": null,
  "answered_at": null,
  "related_question_ids": []
}
```

### 7 standard categories

1. **business_rule**: business rules
2. **architecture_decision**: architecture decisions
3. **data_model_intent**: data-model intent
4. **external_integration**: external-system integration
5. **naming_history**: naming and historical context
6. **operational_requirement**: operational requirements
7. **security_compliance**: security / compliance

Users may add custom categories as needed (v1 expects manual JSON editing; UI is a future extension).

### Severity levels

- **critical**: cannot write the chapter without resolving this. The sub-agent leaves the section blank (`[BLOCKED]`).
- **important**: can be written with inference but confidence is low. Leave a `[CONFIDENCE: LOW]` marker.
- **nice-to-have**: a question about fine detail. Write with inference and lightly confirm in Phase 5.

### Status transitions

```
open → asked → answered
            ↓
            abandoned
```

---

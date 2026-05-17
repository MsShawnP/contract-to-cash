# Contract-to-Cash — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search]

---

## Entries

### 2026-05-17 — JSON validation checked for numeral in word-form headline

**Attempted:** validate_exported_json.py checked whether the string "59" appeared in the headline. The headline is "For Every Dollar Invoiced, Fifty-Nine Cents Arrives as Cash" — word form, not numeral.

**Why it didn't work:** The export script uses `num_to_word()` to convert cents to English words. The validation script assumed numeral form. Assertion looked for `str(int(cents))` in the headline string — always fails when the headline uses spelled-out numbers.

**What we tried instead:** Changed the check to verify the headline is non-empty and contains the word "cent" (case-insensitive). More resilient — works regardless of whether the value is a numeral or word.

**Status:** Resolved

**Tags:** validation, assertion-mismatch, word-form, num_to_word

---


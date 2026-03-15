# ADR-003: Automated Book Rewrite Control Model

## Status
Accepted

## Context
After introducing book-level analysis and improvement plan generation (ADR-002), the system required a controlled mechanism to apply global improvements without destabilizing the entire book.

Fully automatic recursive rewriting was deemed too risky.

## Decision
Introduce BookRewriteOrchestrator with the following constraints:

1. Single-pass execution only (no recursive loops)
2. Only chapters referenced in improvement plan are updated
3. Max 1 chapter-level iteration per chapter
4. No cascade re-trigger of book-level analysis
5. Explicit endpoint for execution

## Control Philosophy
Safety over aggressiveness.

Rewrite is:
- Controlled
- Bounded
- Non-recursive
- Observable

## Architectural Layering
Level 1: Chapter Agents
Level 2: Book Analysis
Level 2.5: Controlled Rewrite Execution
Level 3: Future Strategic Automation

## Consequences
Pros:
- Predictable behavior
- Cost bounded
- No runaway rewriting
- Clear separation of planning vs execution

Cons:
- Requires manual re-analysis if needed
- No dynamic multi-pass global optimization yet

## Future Evolution
Possible ADR-004:
- Multi-pass global optimization
- Confidence-based re-analysis
- Adaptive rewrite depth

---

Principle reinforced:
"All global rewrite operations must be bounded and observable."

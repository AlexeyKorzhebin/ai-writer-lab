# ADR-002: Book-Level Consistency Layer

## Status
Accepted

## Context
After implementing chapter-level multi-agent orchestration, the system required a higher-level agent to evaluate and coordinate consistency across the entire book.

Chapter-level quality does not guarantee:
- Logical coherence across chapters
- Redundancy control
- Proper narrative progression
- Structural continuity

## Decision
Introduce:
- ConsistencyAgent (analysis-only)
- BookOrchestrator (plan generation, no automatic rewrite in V1)

## Design Principles
1. Book-level agents must operate on summaries (not full content) to remain scalable.
2. No automatic global rewriting in V1.
3. Structured JSON protocol for inter-agent communication.
4. Improvement plans generated before execution.

## Control Model
User-driven execution:
- Analyze Book
- Generate Improvement Plan
- Manual or future automated execution

## Consequences
Pros:
- Scalable architecture
- Clear separation of chapter vs book agents
- Safe incremental improvement

Cons:
- No automatic book rewrite yet
- Requires manual review of improvement plan

## Future Evolution
- ADR-003: Automated Book Rewrite Orchestrator
- ADR-004: Cross-Agent Memory Graph
- ADR-005: Enterprise Multi-Book Consistency

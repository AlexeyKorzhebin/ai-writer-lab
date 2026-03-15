# ADR-001: Multi-Agent Orchestration Architecture

## Status
Accepted

## Context
AI Writer Lab evolved from a single LLM generation flow into a multi-agent writing system.
We required:
- Controlled quality improvement
- Deterministic inter-agent communication
- Bounded iteration
- Failure-safe JSON parsing

## Decision
Adopt a hybrid multi-agent orchestration model with:
- WriterPipeline (generation)
- ReviewAgent (structured evaluation)
- EditorAgent (improvement application)
- OrchestratorAgent (control loop)

## Control Strategy
Hybrid stop conditions:
- max_iterations = 3
- stop if score >= 8 AND major_issues == false
- degrade-protection guard

## Protocol Rule
Agents must exchange machine-readable structured data when used inside orchestration.

## Consequences
Pros:
- Deterministic coordination
- Bounded compute cost
- Explicit quality gates
- Extensible architecture

Cons:
- More complexity than linear prompt chaining
- Requires strict output discipline

## Future ADRs
- ADR-002: Consistency Agent
- ADR-003: Versioning Strategy
- ADR-004: Enterprise Deployment Model

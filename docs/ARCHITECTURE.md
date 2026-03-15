# AI Writer Lab — Architecture Overview

## 1. System Vision
AI Writer Lab is a multi-agent writing engine designed to support long-form book creation with iterative quality improvement.

The system is structured around:
- Writer pipeline (generation)
- Review agent (quality evaluation)
- Editor agent (improvement application)
- Orchestrator agent (multi-agent coordination)
- Export layer (EPUB, PDF, DOCX)
- Persistence layer (SQLAlchemy models)

---

## 2. Core Layers

### 2.1 Writer Pipeline
Responsibilities:
- Draft generation
- Refinement
- Summary generation
- Continuity memory (previous summaries + full last chapter)
- Context window management

### 2.2 ReviewAgent (Structured Contract)
Returns strict JSON:
{
  "score": 0-10,
  "major_issues": true/false,
  "feedback": "markdown text"
}

Includes:
- Safe JSON parsing
- Fallback protection
- Score normalization (0–10)

### 2.3 EditorAgent
Applies structured review feedback to rewrite chapter text while preserving author tone.

### 2.4 OrchestratorAgent
Hybrid control strategy:
- Max iterations: 3
- Stop if score >= 8 AND no major issues
- Safety guard against degradation

Implements agent coordination loop:
Writer → Review → Edit → Review → Stop

---

## 3. Memory Architecture
For each chapter:
- content (full text)
- summary (compressed representation)

Continuity strategy:
- Full previous chapter included
- Older chapters via summaries only

---

## 4. Export Layer
Supported formats:
- EPUB (ebooklib)
- PDF (ReportLab + DejaVuSans for Cyrillic support)
- DOCX (python-docx)

Export layer is isolated from generation layer.

---

## 5. Agent Protocol Principles
1. Agents must return structured outputs when used in orchestration.
2. No uncontrolled text-to-text chaining.
3. All inter-agent communication should be machine-readable.
4. Fallback mechanisms required for robustness.

---

## 6. Future Directions
- ConsistencyAgent (cross-chapter logic)
- FactCheckAgent
- Full-book quality pass
- Versioning with rollback
- Automated book-level orchestration

---

System classification:
Multi-agent controlled LLM writing engine with quality gate orchestration.

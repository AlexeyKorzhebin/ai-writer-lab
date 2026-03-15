# Sequence Diagrams (Textual)

## 1. Produce High Quality Flow

User → API: POST /produce-hq
API → OrchestratorAgent: produce_high_quality
Orchestrator → WriterPipeline: generate (if needed)
Orchestrator → ReviewAgent: review
ReviewAgent → Orchestrator: JSON(score, issues, feedback)
Orchestrator → EditorAgent: apply improvements
EditorAgent → Orchestrator: improved text
Orchestrator → ReviewAgent: review (repeat)
Orchestrator → API: final content + score + iterations
API → DB: commit
API → User: result

---

## 2. Manual Review Flow

User → API: POST /review
API → ReviewAgent
ReviewAgent → API: JSON result
API → User

---

## 3. Manual Improvement Flow

User → API: POST /edit
API → EditorAgent
EditorAgent → API: improved text
API → DB: commit
API → User

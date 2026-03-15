# Agent Communication Protocol

## 1. ReviewAgent Output Contract
{
  "score": 0-10,
  "major_issues": true/false,
  "feedback": "markdown text"
}

Constraints:
- Must be valid JSON
- No markdown outside JSON
- Score normalized 0–10

## 2. EditorAgent Input
- project
- chapter
- review.feedback

Returns:
- improved chapter text

## 3. Orchestrator Loop
Pseudo-flow:
1. Generate if empty
2. Review
3. If score >= 8 AND major_issues == false → stop
4. Edit
5. Repeat ≤ 3

## 4. Failure Handling
- JSON parsing fallback
- Degradation guard
- Hard iteration limit

## 5. Extensibility
Future agents must:
- Define strict input/output contracts
- Avoid free-form text chaining
- Support fallback safety

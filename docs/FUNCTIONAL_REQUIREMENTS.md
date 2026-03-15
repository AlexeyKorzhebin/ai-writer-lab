# Functional Requirements

## 1. Project Management
- Create project
- Store metadata (author style, temperature, model config)

## 2. Outline Generation
- Generate structured JSON outline
- Persist chapter placeholders

## 3. Chapter Generation
- Draft stage
- Refine stage
- Summary generation
- Continuity support

## 4. Review
- Structured JSON review output
- Score (0-10)
- major_issues flag
- Detailed feedback

## 5. Improvement
- Apply review feedback
- Preserve author style

## 6. Orchestrated HQ Production
- Iterative improvement loop
- Stop condition hybrid model
- Return iterations + final score

## 7. Editing
- Manual chapter editing
- Regeneration

## 8. Export
- EPUB
- PDF (Cyrillic support)
- DOCX

## 9. Reliability Requirements
- Safe JSON parsing
- Fallback logic
- Bounded loops
- Context window control

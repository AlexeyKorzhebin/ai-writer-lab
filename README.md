# AI Writer Lab

## v0.2 — Clean Architecture Baseline (2026-03-15)

### ✅ Architecture
- Clean Architecture (Presentation / Application / Domain / Infrastructure)
- Domain Entities: ProjectEntity, ChapterEntity, AuthorProfile
- Repository pattern with interface abstraction
- LLMInterface (provider abstraction)
- ORM isolated to infrastructure layer
- Alembic migrations enabled
- systemd + nginx production deployment

### ✅ Testing Strategy
- Unit tests (Domain & UseCases)
- Integration tests (API endpoints)
- Multi-chapter consistency test
- Load test (10 chapters, 30+ LLM calls)
- No-LLM fallback test
- Export validation (PDF/DOCX/EPUB)
- CI with pytest + coverage gate (>=80%)

### ✅ Production Status
- Async-safe
- No ORM leakage in business logic
- Migration-driven schema evolution
- Graceful LLM fallback
- Fully regression-protected

---

Project milestone: Stable architectural baseline ready for Phase II (Vector Memory & Iterative Drafting).

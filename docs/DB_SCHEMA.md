# Database Structure

## Tables

### projects
- id (PK)
- title
- description
- model_name
- temperature
- max_tokens
- author_name
- author_style

### chapters
- id (PK)
- project_id (FK → projects.id)
- title
- content
- summary

### chapter_versions
- id (PK)
- chapter_id (FK → chapters.id)
- content
- summary
- version_number

## Relationships
projects 1 — N chapters
chapters 1 — N chapter_versions

## Design Notes
- summary used for long-form continuity
- versioning prepared for rollback feature
- export layer independent from schema

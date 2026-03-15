# Narrative Spec v0.3 — Story-Centric UX Model

Дата фиксации: 2026-03-15
Статус: Product Design Blueprint (Pre-Implementation)

---

# 1. Переход от Text-First к Story-First

v0.2 был text-centric: Project → Chapter → Generate.

v0.3 становится story-centric:

Story → World → Characters → Structure → Scenes → Text.

Главы становятся производными Narrative Spec.

---

# 2. NarrativeSpec — концептуальная модель

NarrativeSpec — это структурированное описание истории до генерации текста.

## 2.1 Core Idea Layer
- Logline
- Genre
- Tone
- Themes
- Central Conflict
- Story Format

## 2.2 World Spec
- World type (realistic / fantasy / sci-fi)
- Rules of the world
- Time period
- Power structures
- Atmosphere

## 2.3 Character Specs
Для каждого персонажа:
- Role
- Motivation
- Fear
- Secret
- Relationships
- Character Arc (start → transformation → end)

## 2.4 Structural Spec
- Macro structure (3-act / short story / etc)
- Key turning points
- Climax
- Resolution

## 2.5 Scene Map
- Ordered events
- Participants
- Scene purpose
- Emotional state

---

# 3. UX Model v0.3

## 3.1 Entry Point

Вместо "Create Project":

✨ Create Story

---

## 3.2 Story Wizard

Step 1 — Idea
- Logline
- Genre
- Themes
- Conflict

Step 2 — World
- Type
- Rules
- Atmosphere

Step 3 — Characters
- Add character
- Define arc

Step 4 — Structure
- Choose structure strategy
- Generate outline

Step 5 — Scene Map
- Generate ordered scene list

Only after this → Write Scenes

---

## 3.3 Main Workspace Layout

Left Panel — Story
- 📖 Structure
- 👤 Characters
- 🌍 World
- 🧵 Timeline

Center — Scene Editor
- Scene text
- Versions

Right Panel — AI Co-Author
- 🧠 Suggest 3 variants
- 🔍 Review logic
- 🎭 Character consistency

---

# 4. Co-Creation Mode

Instead of single Generate:

🧠 Suggest Scene Development
- Variant A
- Variant B
- Variant C
- Write My Own

Author chooses or edits.

---

# 5. Versioned Narrative

NarrativeSpec is versioned.

Changing:
- conflict
- character arc
- ending

Triggers:
- Suggest scene regeneration
- Suggest consistency re-check

---

# 6. Architectural Impact

New Domain entity:

NarrativeSpec
- world
- characters
- structure
- scenes

UseCases evolve to operate on NarrativeSpec.

StoryFormatStrategy integrates at Structural Spec level.

---

# 7. Minimal v0.3 Scope

For first iteration:
- Story Wizard (basic)
- Character panel
- Simple timeline list
- 3 scene variants
- NarrativeSpec stored as JSON (versioned)

---

# 8. Strategic Direction

AI Writer Lab evolves toward:

Narrative Operating System

Not a text generator, but a story design environment.

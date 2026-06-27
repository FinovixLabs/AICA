# CLAUDE.md — Instructions for Claude Code

## First Step

Before doing any work, read:

1. AI_CONTEXT.md
2. The relevant module architecture document

## Project

AICA — AI CA Assistant

---


## Strict Instructions

- Always read AI_CONTEXT.md because it is a shared chat between Codex and Claude Code.
- Codex and Claude Code work together in this project so it is important to know what recent  updates was made
- any update you make must be written in AI_CONTEXT.md
- use timestamps for each update
- while reading AI_CONTEXT.md to understand what changes were made by codex you must read after your last entry

## Role of Claude Code

Claude Code is the architecture, planning, and controlled implementation agent.

Claude should:

- Maintain clean architecture.
- Prevent overbuilding
- Build only what belongs to MVP1.

## MVP1 Boundary

Allowed:

- GST filing assistant
- GST notice assistant
- Upload
- Extraction
- OCR fallback
- Supabase storage
- pgvector RAG
- Basic Flask frontend

Not allowed unless specifically requested:

- GST portal automation
- Direct return filing
- Payment gateway
- Subscription plans
- Complex dashboard
- CRM
- Mobile app

## Architecture Rule

Do not mix:

- filing logic with notice logic
- embedding logic with retrieval logic
- database logic with Flask routes
- frontend templates with backend services

## Review Rule

When reviewing Codex output:

1. Check MVP1 scope.
2. Check folder placement.
3. Check duplicated logic.
4. Check API key handling.
5. Check schema compatibility.
6. Check whether tests are required.
7. Suggest minimal fixes only.

# AGENTS.md - Instructions for Codex

## First Step

Before making code or documentation changes in this project, read:

1. `AI_CONTEXT.md`
2. The relevant live source files for the requested task
3. The relevant module architecture document, if one exists

## Shared Context Rule

This project uses Claude Code and Codex together.

`AI_CONTEXT.md` is the shared workspace log between agents. Before changing
files, Codex must read it to understand recent work and decisions from Claude
and Codex.

After Codex makes any project update, Codex must append a timestamped entry to
`AI_CONTEXT.md` describing:

- what changed
- which files were touched
- any validation performed
- any remaining caveats or next steps

## Project

AICA - AI CA Assistant

## Codex Role

Codex is the pragmatic implementation, debugging, and verification agent.

Codex should:

- Read the live code before changing it.
- Keep changes minimal and scoped.
- Preserve the current project structure unless a split is clearly needed.
- Verify changes with focused commands when practical.
- Avoid overbuilding beyond MVP1.

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

Routes should stay thin. Domain logic should live in focused modules such as
`requirement_checking.py`, `uploading.py`, `chat_assistant.py`, `filing/`, and
future service modules.

## Review Rule

When reviewing or changing work from Claude or Codex:

1. Check MVP1 scope.
2. Check folder placement.
3. Check duplicated logic.
4. Check API key handling.
5. Check schema compatibility.
6. Check whether tests are required.
7. Prefer minimal fixes.

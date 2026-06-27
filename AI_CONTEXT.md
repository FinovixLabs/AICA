# AICA Shared AI Context

## Project

AICA — AI CA Assistant.

## Product Goal

Build an AI-assisted compliance platform for CA/CS/GST practitioners.

## MVP1 Focus

MVP1 includes:

- GST filing assistant
- GST notice assistant
- Document upload
- Text extraction
- Scanned PDF fallback
- Supabase database
- pgvector RAG
- Basic Flask frontend
- Client-wise document storage

## Not Allowed in MVP1

Do not build:

- GST portal login automation
- Direct GST return filing
- Payment system
- Subscription system
- Mobile app
- Complex analytics dashboard
- CRM
- Full firm OS

## Tech Stack

- Python
- Flask
- Supabase PostgreSQL
- pgvector
- LangChain
- OpenAI embeddings
- OpenAI chat model
- Gemini OCR fallback
- Flask templates
- HTML/CSS/JS

## Module Boundaries

- ingestion/ handles document extraction and chunking.
- search/ handles retrieval.
- filing/ handles GST filing workflows.
- notice/ handles GST notice workflows.
- database/ handles Supabase queries.
- services/ handles external APIs.
- routes/ handles Flask routes.

## Current Priority

Build MVP1 in this order:

1. Database schema
2. Document ingestion
3. RAG ingestion
4. Filing module
5. Notice module
6. Frontend routes
7. Testing

## Development Rule

Never overbuild beyond MVP1 unless explicitly instructed.

## Shared Agent Updates

### 2026-06-27 05:50:29 +05:30 - Codex

- Read `CLAUDE.md` and `AI_CONTEXT.md` to align Codex with the Claude Code workflow.
- Added `AGENTS.md` as the Codex-facing project instruction file.
- Codex will read `AI_CONTEXT.md` before making future code or documentation changes in this project.
- Codex will append timestamped entries to `AI_CONTEXT.md` after project updates, including files touched, validation, caveats, and next steps.

### 2026-06-27 05:57:50 +05:30 - Codex

- Added `.gitignore` for the AICA repository.
- Ignored Python caches, virtual environments, `.env` secrets, runtime logs, agent handoff scratch files, local uploads, local Codex/agent state, local Claude settings, editor files, and common test/build artifacts.
- Kept source files, docs, migrations, static frontend, filing templates, and shared project instruction files trackable.
- Validation performed: read back `.gitignore` after writing.
